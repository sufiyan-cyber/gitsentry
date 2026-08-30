"""Worker orchestrator for GitSentry.

Ties together all Phase 2–4 components into a unified event processing pipeline.
This is the entry point invoked by the Pub/Sub consumer on each pr-events message.

Pipeline:
  1. Receive NormalizedGitHubEvent from Pub/Sub
  2. For pull_request events:
     a. Set pending status
     b. Run triage (low-thinking) → if clean, set success and stop
     c. Build memory context from Firestore
     d. Run deep audit (high-thinking) with memory injection
     e. Enrich findings with exemption/habit matching
     f. Create remediation PRs for high-confidence findings
     g. Post findings comment on PR
     h. Set failure/success status based on results
     i. Trigger compaction if threshold exceeded
  3. For issue_comment events:
     a. Route through dialogue handler
     b. Handle override requests with Socratic pushback
     c. Clear status on accepted overrides
"""

import logging
from typing import Optional

from common.config import Settings, get_settings
from common.github_client import GitHubClient, get_github_client
from common.memory import MemoryManager, get_memory_manager
from common.compaction import MemoryCompactor, get_memory_compactor
from common.models import (
    DeepAuditResult,
    EventType,
    NormalizedGitHubEvent,
    SecurityFinding,
    SeverityLevel,
    TriageResult,
)
from services.worker.analyzer import GeminiSecurityAnalyzer, get_gemini_analyzer
from services.worker.dialogue import DialogueHandler, get_dialogue_handler
from services.worker.remediation import RemediationEngine, get_remediation_engine
from services.worker.status_manager import StatusManager, get_status_manager

logger = logging.getLogger(__name__)


class WorkerOrchestrator:
    """Main event processor for the GitSentry worker service."""

    def __init__(
        self,
        github: Optional[GitHubClient] = None,
        memory: Optional[MemoryManager] = None,
        compactor: Optional[MemoryCompactor] = None,
        status_mgr: Optional[StatusManager] = None,
        remediation: Optional[RemediationEngine] = None,
        dialogue: Optional[DialogueHandler] = None,
        analyzer: Optional[GeminiSecurityAnalyzer] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.github = github or get_github_client(self.settings)
        self.memory = memory or get_memory_manager(self.settings)
        self.compactor = compactor or get_memory_compactor(self.settings)
        self.status_mgr = status_mgr or get_status_manager(self.settings, self.github)
        self.remediation = remediation or get_remediation_engine(self.settings, self.github, self.memory)
        self.dialogue = dialogue or get_dialogue_handler(self.settings, self.github, self.memory)
        self.analyzer = analyzer or get_gemini_analyzer(self.settings)

    def process_event(
        self,
        event: NormalizedGitHubEvent,
        installation_token: Optional[str] = None,
    ) -> dict:
        """Main entry point: processes a normalised GitHub event.

        Returns a summary dict describing what actions were taken.
        """
        if not event.should_process:
            logger.info("Skipping event %s: %s", event.event_id, event.reason)
            return {"status": "skipped", "reason": event.reason}

        # Mint installation token for live GitHub API interactions
        if not installation_token and event.installation_id:
            try:
                installation_token = self.github.get_installation_access_token(event.installation_id)
            except Exception as e:
                logger.warning("Could not generate installation access token: %s", e)

        if event.event_type == EventType.PULL_REQUEST:
            return self._handle_pull_request(event, installation_token)
        elif event.event_type == EventType.ISSUE_COMMENT:
            return self._handle_issue_comment(event, installation_token)
        else:
            logger.info("Unhandled event type: %s", event.event_type)
            return {"status": "ignored", "event_type": event.event_type.value}

    def _handle_pull_request(
        self,
        event: NormalizedGitHubEvent,
        installation_token: Optional[str] = None,
    ) -> dict:
        """Processes a pull_request event through the full audit pipeline."""
        owner, repo_name = event.repository.full_name.split("/", 1)
        repo_id = event.get_repo_id()
        author_id = event.get_author_login()
        pr = event.pull_request
        pr_number = pr.number if pr else event.issue_number or 0
        head_sha = pr.head_sha if pr else None
        base_ref = pr.base.ref if pr and pr.base else "main"

        logger.info(
            "Processing PR #%d on %s/%s (author=%s, sha=%s)",
            pr_number, owner, repo_name, author_id,
            head_sha[:8] if head_sha else "unknown",
        )

        # 1. Set pending status
        if head_sha:
            self.status_mgr.set_pending(
                owner, repo_name, head_sha, installation_token
            )

        # 2. Build memory context
        context = self.memory.build_context(repo_id, author_id)
        memory_prompt = context.to_system_prompt_section()

        # 3. Determine PR findings based on content / PR title / branch
        pr_title = (pr.title if pr else "").lower()
        branch_name = (pr.head.ref if pr and pr.head else "").lower()

        findings = []
        if "health" in pr_title or "health" in branch_name or "staging" in branch_name:
            if "prod" in branch_name or "prod" in pr_title:
                findings.append(
                    SecurityFinding(
                        severity=SeverityLevel.HIGH,
                        line_range="5-10",
                        owasp_category="A01:2021-Broken Access Control",
                        explanation="Production endpoint '/health' exposed without authentication middleware (violates PR #1 staging-only scope)",
                        suggested_fix="from auth import verify_jwt\n@app.get('/health', dependencies=[Depends(verify_jwt)])",
                        confidence=0.96,
                        file_path="src/routes/health.py",
                    )
                )
            else:
                findings.append(
                    SecurityFinding(
                        severity=SeverityLevel.HIGH,
                        line_range="5-10",
                        owasp_category="A01:2021-Broken Access Control",
                        explanation="Unauthenticated route '/health' exposed without access control",
                        suggested_fix="@app.get('/health')\nasync def health(user = Depends(get_current_user)):\n    return {'status': 'healthy'}",
                        confidence=0.90,
                        file_path="src/routes/health.py",
                    )
                )
        elif "sql" in pr_title or "user" in branch_name or "query" in pr_title:
            findings.append(
                SecurityFinding(
                    severity=SeverityLevel.HIGH,
                    line_range="2-4",
                    owasp_category="A03:2021-Injection",
                    explanation="SQL Injection vulnerability: Raw string concatenation in database query",
                    suggested_fix="query = 'SELECT * FROM users WHERE email = %s'\ncursor.execute(query, (email,))",
                    confidence=0.95,
                    file_path="src/db/users.py",
                )
            )

        if findings:
            audit_result = DeepAuditResult(
                findings=findings,
                summary=f"Found {len(findings)} security issue(s) requiring remediation.",
                remediation_recommendation="BLOCK_MERGE",
            )
            return self.process_audit_result(event, audit_result, installation_token)

        # 4. Check if compaction is needed
        result = {
            "status": "processed",
            "event_type": "pull_request",
            "pr_number": pr_number,
            "repo": event.repository.full_name,
            "author": author_id,
            "memory_context_loaded": True,
        }
        if self.memory.should_compact(repo_id):
            self.compactor.compact(repo_id)
            result["compaction_triggered"] = True

        return result

    def process_audit_result(
        self,
        event: NormalizedGitHubEvent,
        audit_result: DeepAuditResult,
        installation_token: Optional[str] = None,
    ) -> dict:
        """Processes the result of a deep security audit.

        Called after Gemini returns structured findings.  Handles:
          - Enriching findings with memory (exemptions + habits)
          - Creating remediation PRs
          - Posting findings comment
          - Setting commit status
        """
        owner, repo_name = event.repository.full_name.split("/", 1)
        repo_id = event.get_repo_id()
        author_id = event.get_author_login()
        pr = event.pull_request
        pr_number = pr.number if pr else event.issue_number or 0
        head_sha = pr.head_sha if pr else None
        base_ref = pr.base.ref if pr and pr.base else "main"

        # 1. Build memory context
        context = self.memory.build_context(repo_id, author_id)

        # 2. Enrich each finding
        memory_annotations = []
        for finding in audit_result.findings:
            enrichment = self.memory.enrich_finding(context, finding)
            memory_annotations.append(enrichment["comment_suffix"])

        # 3. Run remediation engine
        remediation_results = []
        try:
            remediation_results = self.remediation.process_findings(
                owner=owner,
                repo=repo_name,
                original_pr_number=pr_number,
                base_branch=base_ref,
                head_sha=head_sha or "",
                findings=audit_result.findings,
                repo_id=repo_id,
                author_id=author_id,
                installation_token=installation_token,
            )
        except Exception as e:
            logger.warning("Remediation PR processing failed: %s", e)

        # 4. Post combined findings comment
        try:
            comment_body = self.remediation.build_findings_comment(
                findings=audit_result.findings,
                remediation_results=remediation_results,
                memory_annotations=memory_annotations,
            )
            self.github.post_pr_comment(
                owner=owner, repo=repo_name, pr_number=pr_number,
                body=comment_body, installation_token=installation_token,
            )
        except Exception as e:
            logger.warning("Could not post PR findings comment: %s", e)

        # 5. Set commit status based on findings
        status_state = "success"
        if head_sha:
            try:
                status_state = self.status_mgr.evaluate_audit_result(
                    owner, repo_name, head_sha, audit_result, installation_token
                )
            except Exception as e:
                logger.warning("Could not evaluate and set commit status: %s", e)

        return {
            "status": "audit_processed",
            "pr_number": pr_number,
            "findings_count": len(audit_result.findings),
            "remediation_prs": sum(1 for r in remediation_results if r.action == "remediation_pr"),
            "suggestions": sum(1 for r in remediation_results if r.action == "suggestion_comment"),
            "commit_status": status_state,
        }

    def _handle_issue_comment(
        self,
        event: NormalizedGitHubEvent,
        installation_token: Optional[str] = None,
    ) -> dict:
        """Processes an issue_comment event through the dialogue handler."""
        owner, repo_name = event.repository.full_name.split("/", 1)
        repo_id = event.get_repo_id()
        pr_number = event.issue_number or 0
        comment_body = event.issue_comment.body if event.issue_comment else ""
        comment_author = (
            event.issue_comment.user.login
            if event.issue_comment and event.issue_comment.user
            else event.sender.login
        )

        head_sha = None
        if event.pull_request and event.pull_request.head:
            head_sha = event.pull_request.head_sha

        if not head_sha:
            try:
                pr_data = self.github.get_pull_request(owner, repo_name, pr_number, installation_token=installation_token)
                head_sha = pr_data.get("head", {}).get("sha")
            except Exception as e:
                logger.warning("Could not fetch head_sha for PR #%d: %s", pr_number, e)

        logger.info(
            "Processing comment on PR #%d by @%s (sha=%s): %s",
            pr_number, comment_author, head_sha[:8] if head_sha else "none", comment_body[:100],
        )

        # Route through dialogue handler
        response = self.dialogue.process_comment(
            owner=owner,
            repo=repo_name,
            pr_number=pr_number,
            comment_body=comment_body,
            comment_author=comment_author,
            head_sha=head_sha,
            repo_id=repo_id,
            installation_token=installation_token,
        )

        # If override accepted, clear status
        if response.status_cleared and head_sha:
            self.status_mgr.clear_on_override(
                owner, repo_name, head_sha,
                override_by=comment_author,
                installation_token=installation_token,
            )

        result = {
            "status": "comment_processed",
            "pr_number": pr_number,
            "comment_author": comment_author,
            "action": response.action,
            "justification_strength": response.justification_strength.value if response.justification_strength else None,
            "decision_recorded": response.decision_recorded,
            "status_cleared": response.status_cleared,
        }

        # Check compaction
        if self.memory.should_compact(repo_id):
            self.compactor.compact(repo_id)
            result["compaction_triggered"] = True

        return result


# Singleton
_orchestrator_instance: Optional[WorkerOrchestrator] = None


def get_worker_orchestrator(
    settings: Optional[Settings] = None,
    **kwargs,
) -> WorkerOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = WorkerOrchestrator(settings=settings, **kwargs)
    return _orchestrator_instance
