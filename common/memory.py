"""Memory context builder for GitSentry.

Assembles the full MemoryContext used to enrich Gemini's system prompt before
each deep security audit.  This is the integration layer between the Firestore
Memory Bank and the AI agent's prompting pipeline.

Key responsibilities (PRD Phase 3):
  1. Fetch the compacted memory brief + author's dev_habits from Firestore.
  2. Expose exemption matching (active decisions → don't re-flag).
  3. Expose habit matching (recurring patterns → cite by count).
  4. Record new decisions when an override justification is accepted.
  5. Record / update dev_habits when a recurring pattern is detected.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from common.config import Settings, get_settings
from common.firestore_client import FirestoreMemoryBank, get_firestore_memory_bank
from common.models import (
    AuditLogDocument,
    DecisionDocument,
    DecisionStatus,
    DevHabitDocument,
    ExemptionMatch,
    HabitMatch,
    MemoryContext,
    SecurityFinding,
)

logger = logging.getLogger(__name__)


class MemoryManager:
    """Orchestrates Memory Bank reads / writes for the audit pipeline.

    Typical call flow during a deep audit:
        1. ``build_context(repo_id, author_id)`` → ``MemoryContext``
        2. Inject ``context.to_system_prompt_section()`` into Gemini prompt.
        3. For each finding, call ``context.find_exemption(...)`` and
           ``context.find_habit_match(...)``.
        4. Call ``record_finding_habit(...)`` for any new or recurring pattern.
        5. Call ``record_decision(...)`` when a developer override is accepted.
        6. Call ``record_audit(...)`` to log every action taken.
    """

    def __init__(
        self,
        firestore: Optional[FirestoreMemoryBank] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.firestore = firestore or get_firestore_memory_bank(self.settings)

    # ------------------------------------------------------------------
    # Context assembly
    # ------------------------------------------------------------------

    def build_context(self, repo_id: str, author_id: str) -> MemoryContext:
        """Assembles the complete memory context for a repo + author.

        This is called **before** the deep audit Gemini pass so the model
        has access to all prior decisions and the developer's habit history.
        """
        # 1. Fetch the compacted brief (bounded-size summary)
        brief = self.firestore.get_memory_brief(repo_id)

        # 2. Fetch raw active decisions (needed for exemption matching)
        active_decisions = self.firestore.get_active_decisions(repo_id)

        # 3. Fetch author-specific habits
        author_habits = self.firestore.get_author_habits(repo_id, author_id)

        context = MemoryContext(
            repo_id=repo_id,
            author_id=author_id,
            brief=brief,
            active_decisions=active_decisions,
            author_habits=author_habits,
        )

        logger.info(
            "Built memory context for %s/@%s: brief=%s, %d active decisions, %d author habits",
            repo_id,
            author_id,
            "present" if brief else "absent",
            len(active_decisions),
            len(author_habits),
        )
        return context

    # ------------------------------------------------------------------
    # Finding enrichment
    # ------------------------------------------------------------------

    def enrich_finding(
        self,
        context: MemoryContext,
        finding: SecurityFinding,
    ) -> dict:
        """Checks a single finding against memory and returns enrichment info.

        Returns a dict with keys:
          - exemption: ExemptionMatch (if the finding is covered by a decision)
          - habit: HabitMatch (if the pattern recurs for this developer)
          - comment_suffix: str (human-readable annotation for the PR comment)
        """
        exemption = context.find_exemption(finding.explanation)
        habit = context.find_habit_match(finding.explanation)

        comment_parts: List[str] = []

        if exemption.matched:
            comment_parts.append(
                f"ℹ️ **Acknowledged exemption** — this pattern was previously approved "
                f"by {exemption.approved_by} in {exemption.pr_reference}: "
                f'"{exemption.description}"'
            )
        if habit.matched:
            count = habit.occurrence_count
            ordinal = _ordinal(count + 1)  # +1 because this is a new occurrence
            prior_list = ", ".join(habit.prior_prs[-3:])
            comment_parts.append(
                f"🔁 **Recurring pattern** — this is the {ordinal} time this pattern "
                f"has appeared in your PRs ({habit.pattern}). "
                f"Previously seen in: {prior_list}."
            )

        return {
            "exemption": exemption,
            "habit": habit,
            "comment_suffix": "\n\n".join(comment_parts) if comment_parts else "",
        }

    # ------------------------------------------------------------------
    # State mutations
    # ------------------------------------------------------------------

    def record_finding_habit(
        self,
        repo_id: str,
        author_id: str,
        pattern: str,
        pr_reference: str,
    ) -> DevHabitDocument:
        """Creates or updates a dev_habits record for a detected pattern."""
        return self.firestore.upsert_dev_habit(
            repo_id=repo_id,
            author_id=author_id,
            pattern=pattern,
            pr_reference=pr_reference,
        )

    def record_decision(
        self,
        repo_id: str,
        description: str,
        approved_by: str,
        pr_reference: str,
    ) -> str:
        """Records a new active decision (e.g. accepted override justification).

        Returns the generated Firestore doc ID.
        """
        decision = DecisionDocument(
            description=description,
            approved_by=approved_by,
            pr_reference=pr_reference,
            status=DecisionStatus.ACTIVE,
        )
        return self.firestore.add_decision(repo_id, decision)

    def record_audit(
        self,
        repo_id: str,
        pr_reference: str,
        action_taken: str,
        reasoning_summary: str,
    ) -> str:
        """Writes an audit log entry.  Returns the generated doc ID."""
        entry = AuditLogDocument(
            pr_reference=pr_reference,
            action_taken=action_taken,
            reasoning_summary=reasoning_summary,
        )
        return self.firestore.add_audit_log(repo_id, entry)

    # ------------------------------------------------------------------
    # Compaction trigger check
    # ------------------------------------------------------------------

    def should_compact(self, repo_id: str) -> bool:
        """Returns True if the raw collection sizes exceed the compaction threshold."""
        threshold = self.settings.MEMORY_COMPACTION_THRESHOLD
        decision_count = self.firestore.count_decisions(repo_id)
        habit_count = self.firestore.count_habits(repo_id)
        return (decision_count + habit_count) >= threshold


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ordinal(n: int) -> str:
    """Returns the ordinal string for a positive integer (1st, 2nd, 3rd …)."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_memory_manager_instance: Optional[MemoryManager] = None


def get_memory_manager(
    settings: Optional[Settings] = None,
    firestore: Optional[FirestoreMemoryBank] = None,
) -> MemoryManager:
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager(
            settings=settings,
            firestore=firestore,
        )
    return _memory_manager_instance
