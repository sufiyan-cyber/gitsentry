"""GitHub API client for GitSentry.

Handles all GitHub REST API interactions using the GitHub App installation
token pattern (not static PATs).  Supports:
  - PR comments (post, list thread)
  - Commit status checks (set pending / failure / success)
  - Branch creation and file commits (for remediation PRs)
  - Pull request creation (link remediation PR from original)

In test/mock mode, all mutations are recorded locally without calling GitHub.
"""

import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from common.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass
class GitHubAPICall:
    """Record of a single API call made (or mocked)."""
    method: str
    endpoint: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    response: Optional[Dict[str, Any]] = None


class GitHubClient:
    """Interacts with GitHub REST API via App installation tokens.

    In test or local dev mode, all calls are captured in ``self.api_calls`` and
    ``self.mock_responses`` can be pre-loaded to simulate GitHub responses.
    """

    def __init__(self, settings: Optional[Settings] = None, force_mock: bool = False):
        self.settings = settings or get_settings()
        self._http_client = None
        self._initialized = False
        
        # Check if live GitHub App credentials are provided
        private_key = self.settings.GITHUB_APP_PRIVATE_KEY
        if not private_key:
            try:
                from common.secrets import get_secret_manager
                private_key = get_secret_manager(self.settings).get_app_private_key()
            except Exception:
                private_key = None

        has_real_creds = bool(
            private_key
            and not str(private_key).startswith("mock")
            and "..." not in str(private_key)
            and self.settings.GITHUB_APP_ID
            and str(self.settings.GITHUB_APP_ID) not in ("123456", "mock")
        )
        self._use_mock = force_mock or self.settings.is_test or not has_real_creds

        # Mock tracking
        self.api_calls: List[GitHubAPICall] = []
        self.mock_responses: Dict[str, Dict[str, Any]] = {}

        # Generated PR/branch tracking for tests
        self.created_branches: List[Dict[str, Any]] = []
        self.created_prs: List[Dict[str, Any]] = []
        self.posted_comments: List[Dict[str, Any]] = []
        self.set_statuses: List[Dict[str, Any]] = []

    def _get_http_client(self):
        """Lazy-initialises httpx client."""
        if not self._initialized:
            self._initialized = True
            if not self._use_mock:
                try:
                    import httpx
                    self._http_client = httpx.Client(
                        base_url="https://api.github.com",
                        timeout=30.0,
                        headers={
                            "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2022-11-28",
                        },
                    )
                except Exception as e:
                    logger.warning("Could not initialise HTTP client: %s", e)
        return self._http_client

    def get_installation_access_token(self, installation_id: Optional[int]) -> Optional[str]:
        """Exchanges GitHub App private key + app ID for a short-lived installation access token."""
        if not installation_id:
            return None

        private_key = self.settings.GITHUB_APP_PRIVATE_KEY
        if not private_key:
            try:
                from common.secrets import get_secret_manager
                private_key = get_secret_manager(self.settings).get_app_private_key()
            except Exception:
                private_key = None

        app_id = self.settings.GITHUB_APP_ID

        if not private_key or not app_id or str(private_key).startswith("mock"):
            return None

        try:
            import jwt
            import time
            import httpx

            now = int(time.time())
            payload = {
                "iat": now - 60,
                "exp": now + 600,
                "iss": str(app_id),
            }
            # Handle \n escaped strings from environment variables
            formatted_key = private_key.replace("\\n", "\n") if isinstance(private_key, str) else private_key
            encoded_jwt = jwt.encode(payload, formatted_key, algorithm="RS256")

            url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
            headers = {
                "Authorization": f"Bearer {encoded_jwt}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            resp = httpx.post(url, headers=headers, timeout=15.0)
            if resp.is_success:
                token_data = resp.json()
                logger.info("Successfully minted GitHub installation token for installation %s", installation_id)
                return token_data.get("token")
            else:
                logger.warning("Failed to obtain installation token: %s %s", resp.status_code, resp.text)
                return None
        except Exception as e:
            logger.warning("Exception while generating installation access token: %s", e)
            return None

    def _record_call(self, method: str, endpoint: str, payload: dict, response: dict = None) -> GitHubAPICall:
        call = GitHubAPICall(method=method, endpoint=endpoint, payload=payload, response=response)
        self.api_calls.append(call)
        return call

    # ------------------------------------------------------------------
    # PR Comments
    # ------------------------------------------------------------------

    def post_pr_comment(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        body: str,
        installation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Posts a comment on a pull request.

        Uses the Issues API (comments on PRs are issue comments in GitHub).
        """
        endpoint = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"
        payload = {"body": body}

        if self._use_mock:
            comment_id = len(self.posted_comments) + 1000
            result = {
                "id": comment_id,
                "body": body,
                "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}#issuecomment-{comment_id}",
                "user": {"login": self.settings.GITSENTRY_BOT_LOGIN},
            }
            self.posted_comments.append({
                "owner": owner, "repo": repo, "pr_number": pr_number,
                "body": body, "result": result,
            })
            self._record_call("POST", endpoint, payload, result)
            logger.info("[Mock] Posted comment on %s/%s#%d", owner, repo, pr_number)
            return result

        client = self._get_http_client()
        headers = {}
        if installation_token:
            headers["Authorization"] = f"token {installation_token}"
        resp = client.post(endpoint, json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()
        self._record_call("POST", endpoint, payload, result)
        return result

    def get_pr_comments(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        installation_token: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetches all comments on a pull request (issue comment thread)."""
        endpoint = f"/repos/{owner}/{repo}/issues/{pr_number}/comments"

        if self._use_mock:
            # Return mock comments that match this PR
            results = [
                c["result"] for c in self.posted_comments
                if c["owner"] == owner and c["repo"] == repo and c["pr_number"] == pr_number
            ]
            self._record_call("GET", endpoint, {}, {"count": len(results)})
            return results

        client = self._get_http_client()
        headers = {}
        if installation_token:
            headers["Authorization"] = f"token {installation_token}"
        resp = client.get(endpoint, headers=headers)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Commit Status Checks
    # ------------------------------------------------------------------

    def set_commit_status(
        self,
        owner: str,
        repo: str,
        sha: str,
        state: str,
        description: str = "",
        target_url: Optional[str] = None,
        installation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sets a commit status check (gitsentry/security).

        Args:
            state: One of 'pending', 'success', 'failure', 'error'.
            description: Short explanation (max ~140 chars).
        """
        endpoint = f"/repos/{owner}/{repo}/statuses/{sha}"
        context = self.settings.STATUS_CHECK_CONTEXT
        payload = {
            "state": state,
            "description": description[:140],
            "context": context,
        }
        if target_url:
            payload["target_url"] = target_url

        if self._use_mock:
            result = {
                "id": len(self.set_statuses) + 5000,
                "state": state,
                "context": context,
                "description": description[:140],
                "sha": sha,
            }
            self.set_statuses.append({
                "owner": owner, "repo": repo, "sha": sha,
                "state": state, "description": description,
                "result": result,
            })
            self._record_call("POST", endpoint, payload, result)
            logger.info("[Mock] Set status %s on %s/%s@%s", state, owner, repo, sha[:8])
            return result

        client = self._get_http_client()
        headers = {}
        if installation_token:
            headers["Authorization"] = f"token {installation_token}"
        resp = client.post(endpoint, json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()
        self._record_call("POST", endpoint, payload, result)
        return result

    def get_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        installation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetches a pull request by number to retrieve its head SHA and details."""
        endpoint = f"/repos/{owner}/{repo}/pulls/{pr_number}"
        if self._use_mock:
            return {"number": pr_number, "head": {"sha": "mock_sha_123"}}
        client = self._get_http_client()
        headers = {}
        if installation_token:
            headers["Authorization"] = f"token {installation_token}"
        resp = client.get(endpoint, headers=headers)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Branch & Remediation PR Creation
    # ------------------------------------------------------------------

    def create_branch(
        self,
        owner: str,
        repo: str,
        branch_name: str,
        from_sha: str,
        installation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates a new branch from the given SHA (Git refs API)."""
        endpoint = f"/repos/{owner}/{repo}/git/refs"
        payload = {
            "ref": f"refs/heads/{branch_name}",
            "sha": from_sha,
        }

        if self._use_mock:
            result = {
                "ref": f"refs/heads/{branch_name}",
                "object": {"sha": from_sha},
            }
            self.created_branches.append({
                "owner": owner, "repo": repo,
                "branch_name": branch_name, "from_sha": from_sha,
                "result": result,
            })
            self._record_call("POST", endpoint, payload, result)
            logger.info("[Mock] Created branch %s on %s/%s", branch_name, owner, repo)
            return result

        client = self._get_http_client()
        headers = {}
        if installation_token:
            headers["Authorization"] = f"token {installation_token}"
        resp = client.post(endpoint, json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()
        self._record_call("POST", endpoint, payload, result)
        return result

    def commit_file(
        self,
        owner: str,
        repo: str,
        branch: str,
        file_path: str,
        content: str,
        message: str,
        installation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Creates or updates a file on a branch (Contents API)."""
        import base64
        endpoint = f"/repos/{owner}/{repo}/contents/{file_path}"
        payload = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": branch,
        }

        if self._use_mock:
            result = {
                "content": {"path": file_path, "sha": hashlib.sha1(content.encode()).hexdigest()},
                "commit": {"sha": f"fix-commit-{uuid.uuid4().hex[:8]}", "message": message},
            }
            self._record_call("PUT", endpoint, {"file_path": file_path, "branch": branch, "message": message}, result)
            logger.info("[Mock] Committed file %s to %s/%s@%s", file_path, owner, repo, branch)
            return result

        client = self._get_http_client()
        headers = {}
        if installation_token:
            headers["Authorization"] = f"token {installation_token}"
        # Check if file exists to get current sha for update
        get_resp = client.get(endpoint, params={"ref": branch}, headers=headers)
        if get_resp.status_code == 200:
            payload["sha"] = get_resp.json()["sha"]
        resp = client.put(endpoint, json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()
        self._record_call("PUT", endpoint, {"file_path": file_path, "branch": branch}, result)
        return result

    def open_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str,
        installation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Opens a new pull request."""
        endpoint = f"/repos/{owner}/{repo}/pulls"
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
        }

        if self._use_mock:
            pr_number = 100 + len(self.created_prs)
            result = {
                "number": pr_number,
                "title": title,
                "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}",
                "head": {"ref": head_branch},
                "base": {"ref": base_branch},
                "state": "open",
                "user": {"login": self.settings.GITSENTRY_BOT_LOGIN},
            }
            self.created_prs.append({
                "owner": owner, "repo": repo,
                "title": title, "head": head_branch, "base": base_branch,
                "result": result,
            })
            self._record_call("POST", endpoint, payload, result)
            logger.info("[Mock] Opened PR #%d on %s/%s", pr_number, owner, repo)
            return result

        client = self._get_http_client()
        headers = {}
        if installation_token:
            headers["Authorization"] = f"token {installation_token}"
        resp = client.post(endpoint, json=payload, headers=headers)
        resp.raise_for_status()
        result = resp.json()
        self._record_call("POST", endpoint, payload, result)
        return result

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def reset_mock(self):
        """Clears all mock tracking state."""
        self.api_calls.clear()
        self.created_branches.clear()
        self.created_prs.clear()
        self.posted_comments.clear()
        self.set_statuses.clear()
        self.mock_responses.clear()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_github_client_instance: Optional[GitHubClient] = None


def get_github_client(settings: Optional[Settings] = None) -> GitHubClient:
    global _github_client_instance
    if _github_client_instance is None:
        _github_client_instance = GitHubClient(settings=settings)
    return _github_client_instance
