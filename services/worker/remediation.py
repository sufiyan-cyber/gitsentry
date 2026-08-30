"""Autonomous remediation PR engine for GitSentry.

For high-confidence, narrow-scope findings (single file, small diff, confidence
above threshold), the agent commits a fix to a new branch (gitsentry/fix-{hash})
and opens a PR against the original branch, linking it from its comment.

Lower-confidence or multi-file findings fall back to a suggestion-block comment
only — never auto-generate a fix you can't stand behind.

PRD Phase 4: "GitSentry can open PRs and block merges — it never merges code
itself.  The human always clicks merge."
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any

from common.config import Settings, get_settings
from common.github_client import GitHubClient, get_github_client
from common.memory import MemoryManager, get_memory_manager
from common.models import SecurityFinding, SeverityLevel

logger = logging.getLogger(__name__)


class RemediationResult:
    """Outcome of a remediation attempt for a single finding."""

    def __init__(
        self,
        finding: SecurityFinding,
        action: str,  # "remediation_pr", "suggestion_comment", "skipped"
        pr_url: Optional[str] = None,
        pr_number: Optional[int] = None,
        branch_name: Optional[str] = None,
        comment_body: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        self.finding = finding
        self.action = action
        self.pr_url = pr_url
        self.pr_number = pr_number
        self.branch_name = branch_name
        self.comment_body = comment_body
        self.reason = reason


class RemediationEngine:
    """Creates autonomous remediation PRs for high-confidence findings.

    Decision matrix:
      - confidence >= threshold AND single file AND small diff → open PR
      - otherwise → generate suggestion-block comment only
      - NEVER auto-merge
    """

    def __init__(
        self,
        github: Optional[GitHubClient] = None,
        memory: Optional[MemoryManager] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.github = github or get_github_client(self.settings)
        self.memory = memory or get_memory_manager(self.settings)

    def can_auto_remediate(self, finding: SecurityFinding) -> bool:
        """Determines whether a finding qualifies for autonomous remediation.

        Criteria:
          1. Confidence above configurable threshold (default 0.85)
          2. Single file (file_path is set)
          3. Suggested fix is not too large (< MAX_REMEDIATION_DIFF_LINES)
        """
        if finding.confidence < self.settings.REMEDIATION_CONFIDENCE_THRESHOLD:
            return False
        if not finding.file_path:
            return False
        fix_lines = finding.suggested_fix.count("\n") + 1
        if fix_lines > self.settings.MAX_REMEDIATION_DIFF_LINES:
            return False
        return True

    def create_remediation_pr(
        self,
        owner: str,
        repo: str,
        original_pr_number: int,
        base_branch: str,
        head_sha: str,
        finding: SecurityFinding,
        installation_token: Optional[str] = None,
    ) -> RemediationResult:
        """Creates a branch, commits the fix, and opens a remediation PR.

        Returns a RemediationResult with the action taken.
        """
        if not self.can_auto_remediate(finding):
            # Fall back to suggestion comment
            comment = self._build_suggestion_comment(finding)
            return RemediationResult(
                finding=finding,
                action="suggestion_comment",
                comment_body=comment,
                reason="Below auto-remediation threshold",
            )

        # Generate deterministic branch name
        short_hash = hashlib.sha256(
            f"{owner}/{repo}/{original_pr_number}/{finding.file_path}/{finding.line_range}".encode()
        ).hexdigest()[:8]
        branch_name = f"{self.settings.REMEDIATION_BRANCH_PREFIX}{short_hash}"

        try:
            # 1. Create branch from head SHA
            self.github.create_branch(
                owner=owner,
                repo=repo,
                branch_name=branch_name,
                from_sha=head_sha,
                installation_token=installation_token,
            )

            # 2. Commit the fix
            commit_msg = (
                f"fix: {finding.owasp_category} — {finding.explanation[:60]}\n\n"
                f"Auto-remediation by GitSentry for PR #{original_pr_number}\n"
                f"Severity: {finding.severity.value} | Confidence: {finding.confidence:.0%}\n"
                f"Lines: {finding.line_range}"
            )
            self.github.commit_file(
                owner=owner,
                repo=repo,
                branch=branch_name,
                file_path=finding.file_path,
                content=finding.suggested_fix,
                message=commit_msg,
                installation_token=installation_token,
            )

            # 3. Open remediation PR
            pr_title = f"🔒 GitSentry Fix: {finding.owasp_category} in {finding.file_path}"
            pr_body = (
                f"## Automated Security Remediation\n\n"
                f"This PR was auto-generated by **GitSentry** to fix a security finding "
                f"detected in PR #{original_pr_number}.\n\n"
                f"### Finding Details\n"
                f"- **Severity:** {finding.severity.value}\n"
                f"- **OWASP Category:** {finding.owasp_category}\n"
                f"- **File:** `{finding.file_path}` (lines {finding.line_range})\n"
                f"- **Confidence:** {finding.confidence:.0%}\n\n"
                f"### Explanation\n{finding.explanation}\n\n"
                f"### Fix Applied\n```\n{finding.suggested_fix}\n```\n\n"
                f"---\n"
                f"⚠️ **Review this fix carefully before merging.** "
                f"GitSentry opens PRs but never merges code — "
                f"the human always clicks merge.\n\n"
                f"Linked from: #{original_pr_number}"
            )

            pr_result = self.github.open_pull_request(
                owner=owner,
                repo=repo,
                title=pr_title,
                body=pr_body,
                head_branch=branch_name,
                base_branch=base_branch,
                installation_token=installation_token,
            )

            pr_number = pr_result.get("number", 0)
            pr_url = pr_result.get("html_url", "")

            logger.info(
                "Opened remediation PR #%d for finding in %s (confidence=%.0f%%)",
                pr_number, finding.file_path, finding.confidence * 100,
            )

            return RemediationResult(
                finding=finding,
                action="remediation_pr",
                pr_url=pr_url,
                pr_number=pr_number,
                branch_name=branch_name,
            )

        except Exception as exc:
            logger.error("Failed to create remediation PR: %s", exc)
            comment = self._build_suggestion_comment(finding)
            return RemediationResult(
                finding=finding,
                action="suggestion_comment",
                comment_body=comment,
                reason=f"Remediation PR creation failed: {exc}",
            )

    def process_findings(
        self,
        owner: str,
        repo: str,
        original_pr_number: int,
        base_branch: str,
        head_sha: str,
        findings: List[SecurityFinding],
        repo_id: str,
        author_id: str,
        installation_token: Optional[str] = None,
    ) -> List[RemediationResult]:
        """Processes all findings: auto-remediates where possible, falls back to comments."""
        results: List[RemediationResult] = []

        for finding in findings:
            result = self.create_remediation_pr(
                owner=owner,
                repo=repo,
                original_pr_number=original_pr_number,
                base_branch=base_branch,
                head_sha=head_sha,
                finding=finding,
                installation_token=installation_token,
            )
            results.append(result)

            # Record habit in memory
            self.memory.record_finding_habit(
                repo_id=repo_id,
                author_id=author_id,
                pattern=finding.explanation,
                pr_reference=f"PR #{original_pr_number}",
            )

            # Record audit log
            self.memory.record_audit(
                repo_id=repo_id,
                pr_reference=f"PR #{original_pr_number}",
                action_taken=f"{result.action}: {finding.owasp_category}",
                reasoning_summary=finding.explanation[:200],
            )

        return results

    def _build_suggestion_comment(self, finding: SecurityFinding) -> str:
        """Builds a suggestion-block comment for non-auto-remediatable findings."""
        severity_emoji = {
            SeverityLevel.CRITICAL: "🔴",
            SeverityLevel.HIGH: "🟠",
            SeverityLevel.MEDIUM: "🟡",
            SeverityLevel.LOW: "🔵",
            SeverityLevel.INFO: "ℹ️",
        }.get(finding.severity, "⚪")

        comment = (
            f"### {severity_emoji} Security Finding: {finding.owasp_category}\n\n"
            f"**Severity:** {finding.severity.value} | "
            f"**Confidence:** {finding.confidence:.0%}"
        )
        if finding.file_path:
            comment += f" | **File:** `{finding.file_path}` (lines {finding.line_range})"
        comment += f"\n\n{finding.explanation}\n\n"
        comment += f"**Suggested Fix:**\n```suggestion\n{finding.suggested_fix}\n```\n"
        return comment

    def build_findings_comment(
        self,
        findings: List[SecurityFinding],
        remediation_results: List[RemediationResult],
        memory_annotations: List[str],
    ) -> str:
        """Builds the full PR comment body summarising all findings and actions."""
        lines = ["## 🛡️ GitSentry Security Audit Results\n"]

        # Summary
        high_count = sum(1 for f in findings if f.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH))
        med_count = sum(1 for f in findings if f.severity == SeverityLevel.MEDIUM)
        low_count = sum(1 for f in findings if f.severity in (SeverityLevel.LOW, SeverityLevel.INFO))
        lines.append(
            f"Found **{len(findings)}** finding(s): "
            f"🔴 {high_count} critical/high, 🟡 {med_count} medium, 🔵 {low_count} low/info\n"
        )

        # Each finding
        for i, result in enumerate(remediation_results):
            f = result.finding
            severity_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "ℹ️"}.get(f.severity.value, "⚪")
            lines.append(f"### {severity_emoji} {i+1}. {f.owasp_category}")
            if f.file_path:
                lines.append(f"📁 `{f.file_path}` (lines {f.line_range})")
            lines.append(f"\n{f.explanation}\n")

            if result.action == "remediation_pr":
                lines.append(
                    f"✅ **Auto-remediation PR opened:** [{result.branch_name}]({result.pr_url})\n"
                )
            elif result.comment_body:
                lines.append(f"**Suggested Fix:**\n```suggestion\n{f.suggested_fix}\n```\n")

            # Memory annotations
            if i < len(memory_annotations) and memory_annotations[i]:
                lines.append(memory_annotations[i])
            lines.append("---\n")

        lines.append(
            "\n> 💡 Reply to this comment to discuss findings, provide justification "
            "for an override, or ask GitSentry to explain further.\n"
            "> ⚠️ GitSentry opens PRs and blocks merges but **never merges code** — "
            "the human always clicks merge."
        )

        return "\n".join(lines)


# Singleton
_remediation_engine_instance: Optional[RemediationEngine] = None


def get_remediation_engine(
    settings: Optional[Settings] = None,
    github: Optional[GitHubClient] = None,
    memory: Optional[MemoryManager] = None,
) -> RemediationEngine:
    global _remediation_engine_instance
    if _remediation_engine_instance is None:
        _remediation_engine_instance = RemediationEngine(
            github=github, memory=memory, settings=settings
        )
    return _remediation_engine_instance
