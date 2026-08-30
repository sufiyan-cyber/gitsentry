"""Commit status check lifecycle manager for GitSentry.

Manages the 'gitsentry/security' commit status on pull requests:
  - Sets 'pending' when audit begins
  - Sets 'failure' when unresolved high-severity findings exist
  - Sets 'success' when remediation PR is merged or override accepted
  - Never auto-merges — the human always clicks merge

PRD Phase 4: "the agent sets a GitHub commit status (gitsentry/security)
to pending/failure on any PR with an unresolved high-severity finding.
The status only clears when either (a) the developer accepts/merges the
remediation PR, or (b) the developer explicitly overrides with a written
justification."
"""

import logging
from typing import Dict, List, Optional, Any

from common.config import Settings, get_settings
from common.github_client import GitHubClient, get_github_client
from common.models import DeepAuditResult, SecurityFinding, SeverityLevel

logger = logging.getLogger(__name__)


class StatusManager:
    """Manages the gitsentry/security commit status lifecycle."""

    def __init__(
        self,
        github: Optional[GitHubClient] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.github = github or get_github_client(self.settings)

    def set_pending(
        self,
        owner: str,
        repo: str,
        sha: str,
        installation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sets status to 'pending' — audit in progress."""
        return self.github.set_commit_status(
            owner=owner,
            repo=repo,
            sha=sha,
            state="pending",
            description="GitSentry security audit in progress…",
            installation_token=installation_token,
        )

    def set_failure(
        self,
        owner: str,
        repo: str,
        sha: str,
        finding_count: int = 0,
        description: Optional[str] = None,
        target_url: Optional[str] = None,
        installation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sets status to 'failure' — unresolved high-severity findings."""
        desc = description or f"🚨 {finding_count} unresolved security finding(s) — merge blocked"
        return self.github.set_commit_status(
            owner=owner,
            repo=repo,
            sha=sha,
            state="failure",
            description=desc,
            target_url=target_url,
            installation_token=installation_token,
        )

    def set_success(
        self,
        owner: str,
        repo: str,
        sha: str,
        reason: str = "All findings resolved",
        installation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sets status to 'success' — all findings resolved or exempted."""
        return self.github.set_commit_status(
            owner=owner,
            repo=repo,
            sha=sha,
            state="success",
            description=f"✅ {reason}",
            installation_token=installation_token,
        )

    def evaluate_audit_result(
        self,
        owner: str,
        repo: str,
        sha: str,
        audit_result: DeepAuditResult,
        installation_token: Optional[str] = None,
    ) -> str:
        """Evaluates an audit result and sets the appropriate commit status.

        Returns the status state that was set ('success', 'failure', 'pending').
        """
        high_severity = [
            f for f in audit_result.findings
            if f.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
        ]

        if not audit_result.findings:
            self.set_success(
                owner, repo, sha,
                reason="No security concerns found",
                installation_token=installation_token,
            )
            return "success"

        if high_severity:
            self.set_failure(
                owner, repo, sha,
                finding_count=len(high_severity),
                installation_token=installation_token,
            )
            return "failure"

        # Medium/Low findings — don't block, but note them
        self.set_success(
            owner, repo, sha,
            reason=f"{len(audit_result.findings)} finding(s) noted (non-blocking)",
            installation_token=installation_token,
        )
        return "success"

    def clear_on_override(
        self,
        owner: str,
        repo: str,
        sha: str,
        override_by: str,
        installation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Clears a failure status after a developer override is accepted."""
        return self.set_success(
            owner, repo, sha,
            reason=f"Override accepted from @{override_by}",
            installation_token=installation_token,
        )

    def clear_on_remediation_merged(
        self,
        owner: str,
        repo: str,
        sha: str,
        remediation_pr_number: int,
        installation_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Clears a failure status after a remediation PR is merged."""
        return self.set_success(
            owner, repo, sha,
            reason=f"Remediation PR #{remediation_pr_number} merged",
            installation_token=installation_token,
        )


# Singleton
_status_manager_instance: Optional[StatusManager] = None


def get_status_manager(
    settings: Optional[Settings] = None,
    github: Optional[GitHubClient] = None,
) -> StatusManager:
    global _status_manager_instance
    if _status_manager_instance is None:
        _status_manager_instance = StatusManager(github=github, settings=settings)
    return _status_manager_instance
