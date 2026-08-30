"""Memory compaction engine for GitSentry.

Summarises raw Firestore `decisions` and `dev_habits` documents into a
condensed per-repo "architecture memory brief" (a single document) that is
what actually gets injected into Gemini's context — NOT the full raw history.

PRD Section 4 (Memory Compaction):
  "raw decisions and dev_habits documents get summarized into a condensed
   per-repo 'architecture memory brief' … that's what actually gets injected
   into Gemini's context — not the full raw history.  This keeps prompt size
   bounded as the repo's history grows."

The compaction can run:
  - On-write: triggered when ``MemoryManager.should_compact()`` returns True.
  - On-schedule: via Cloud Scheduler invoking a Cloud Run endpoint.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from common.config import Settings, get_settings
from common.firestore_client import FirestoreMemoryBank, get_firestore_memory_bank
from common.models import (
    DecisionDocument,
    DecisionStatus,
    DevHabitDocument,
    MemoryBrief,
)

logger = logging.getLogger(__name__)


class MemoryCompactor:
    """Generates a compacted MemoryBrief from raw Firestore documents."""

    def __init__(
        self,
        firestore: Optional[FirestoreMemoryBank] = None,
        settings: Optional[Settings] = None,
    ):
        self.settings = settings or get_settings()
        self.firestore = firestore or get_firestore_memory_bank(self.settings)
        self.max_tokens = self.settings.MEMORY_BRIEF_MAX_TOKENS

    def compact(self, repo_id: str) -> MemoryBrief:
        """Reads all raw decisions and dev_habits for a repo, produces a
        condensed ``MemoryBrief``, and persists it to Firestore.

        The brief is built deterministically (no LLM call) so it is fast,
        free, and testable.  A future enhancement could optionally pass the
        raw docs through Gemini for a more nuanced summary.
        """
        decisions = self.firestore.get_all_decisions(repo_id)
        habits = self.firestore.get_all_habits(repo_id)
        audit_count = self.firestore.count_audit_logs(repo_id)

        decisions_summary = self._summarise_decisions(decisions)
        habits_summary = self._summarise_habits(habits)

        brief = MemoryBrief(
            repo_id=repo_id,
            decisions_summary=decisions_summary,
            habits_summary=habits_summary,
            total_decisions=len(decisions),
            total_habits=len(habits),
            total_audits=audit_count,
            generated_at=datetime.now(timezone.utc),
            source_decision_count=len(decisions),
            source_habit_count=len(habits),
        )

        self.firestore.save_memory_brief(repo_id, brief)
        logger.info(
            "Compacted memory brief for %s: %d decisions, %d habits → brief saved",
            repo_id,
            len(decisions),
            len(habits),
        )
        return brief

    def should_compact(self, repo_id: str) -> bool:
        """Returns True when raw doc counts exceed the configured threshold."""
        threshold = self.settings.MEMORY_COMPACTION_THRESHOLD
        n_decisions = self.firestore.count_decisions(repo_id)
        n_habits = self.firestore.count_habits(repo_id)
        return (n_decisions + n_habits) >= threshold

    # ------------------------------------------------------------------
    # Deterministic summarisation helpers
    # ------------------------------------------------------------------

    def _summarise_decisions(self, decisions: List[DecisionDocument]) -> str:
        """Produces a compact text summary of architectural decisions."""
        if not decisions:
            return ""

        active = [d for d in decisions if d.status == DecisionStatus.ACTIVE]
        superseded = [d for d in decisions if d.status == DecisionStatus.SUPERSEDED]

        lines: List[str] = []

        if active:
            lines.append(f"**{len(active)} active decision(s):**")
            for d in active:
                lines.append(
                    f"  • {d.description} "
                    f"(approved by {d.approved_by}, ref: {d.pr_reference})"
                )

        if superseded:
            lines.append(f"**{len(superseded)} superseded decision(s)** (historical context only):")
            # Only include a summary count + last few for brevity
            for d in superseded[-3:]:
                lines.append(
                    f"  • [superseded] {d.description} (ref: {d.pr_reference})"
                )
            if len(superseded) > 3:
                lines.append(f"  … and {len(superseded) - 3} more.")

        return self._truncate("\n".join(lines), budget=self.max_tokens // 2)

    def _summarise_habits(self, habits: List[DevHabitDocument]) -> str:
        """Produces a compact text summary of developer habits across the repo."""
        if not habits:
            return ""

        # Sort by occurrence count descending (most frequent first)
        sorted_habits = sorted(habits, key=lambda h: len(h.occurrences), reverse=True)

        lines: List[str] = []
        lines.append(f"**{len(sorted_habits)} tracked developer pattern(s):**")
        for h in sorted_habits[:15]:  # Cap at 15 most frequent
            count = len(h.occurrences)
            recent_prs = ", ".join(h.occurrences[-3:])
            lines.append(
                f"  • {h.pattern} — {count} occurrence(s), most recent: {recent_prs}"
            )
        if len(sorted_habits) > 15:
            lines.append(f"  … and {len(sorted_habits) - 15} more patterns tracked.")

        return self._truncate("\n".join(lines), budget=self.max_tokens // 2)

    @staticmethod
    def _truncate(text: str, budget: int) -> str:
        """Rough token-based truncation (≈ 4 chars per token)."""
        char_budget = budget * 4
        if len(text) <= char_budget:
            return text
        return text[:char_budget - 20] + "\n… [truncated for prompt budget]"


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_compactor_instance: Optional[MemoryCompactor] = None


def get_memory_compactor(
    settings: Optional[Settings] = None,
    firestore: Optional[FirestoreMemoryBank] = None,
) -> MemoryCompactor:
    global _compactor_instance
    if _compactor_instance is None:
        _compactor_instance = MemoryCompactor(
            settings=settings,
            firestore=firestore,
        )
    return _compactor_instance
