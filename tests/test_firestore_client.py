"""Unit tests for Firestore Memory Bank client (in-memory mock mode)."""

import pytest
from datetime import datetime, timezone

from common.config import Settings
from common.firestore_client import FirestoreMemoryBank
from common.models import (
    AuditLogDocument,
    DecisionDocument,
    DecisionStatus,
    DevHabitDocument,
    MemoryBrief,
)


@pytest.fixture
def fb() -> FirestoreMemoryBank:
    settings = Settings(ENVIRONMENT="test", USE_SECRET_MANAGER=False)
    bank = FirestoreMemoryBank(settings=settings)
    bank.clear_mock_store()
    return bank


REPO = "acme_sentinel-core"


# ------------------------------------------------------------------
# Decisions
# ------------------------------------------------------------------

class TestDecisions:
    def test_add_and_retrieve_active_decision(self, fb: FirestoreMemoryBank):
        doc_id = fb.add_decision(
            REPO,
            DecisionDocument(
                description="Staging allows unauthenticated /health route",
                approved_by="sec-lead",
                pr_reference="PR #42",
            ),
        )
        assert doc_id.startswith("dec-")

        active = fb.get_active_decisions(REPO)
        assert len(active) == 1
        assert active[0].description == "Staging allows unauthenticated /health route"
        assert active[0].approved_by == "sec-lead"
        assert active[0].pr_reference == "PR #42"
        assert active[0].status == DecisionStatus.ACTIVE

    def test_supersede_decision_filters_it_out(self, fb: FirestoreMemoryBank):
        doc_id = fb.add_decision(
            REPO,
            DecisionDocument(
                description="Allow raw SQL for analytics dashboard",
                approved_by="cto",
                pr_reference="PR #10",
            ),
        )
        assert fb.count_decisions(REPO) == 1
        assert len(fb.get_active_decisions(REPO)) == 1

        fb.supersede_decision(REPO, doc_id)
        assert len(fb.get_active_decisions(REPO)) == 0
        assert len(fb.get_all_decisions(REPO)) == 1

    def test_multiple_decisions(self, fb: FirestoreMemoryBank):
        for i in range(5):
            fb.add_decision(
                REPO,
                DecisionDocument(
                    description=f"Decision {i}",
                    approved_by="admin",
                    pr_reference=f"PR #{i}",
                ),
            )
        assert fb.count_decisions(REPO) == 5
        assert len(fb.get_active_decisions(REPO)) == 5


# ------------------------------------------------------------------
# Dev Habits
# ------------------------------------------------------------------

class TestDevHabits:
    def test_create_new_habit(self, fb: FirestoreMemoryBank):
        habit = fb.upsert_dev_habit(
            REPO,
            author_id="alice",
            pattern="raw SQL string concatenation",
            pr_reference="PR #10",
        )
        assert habit.pattern == "raw SQL string concatenation"
        assert habit.occurrences == ["PR #10"]

    def test_upsert_appends_occurrence(self, fb: FirestoreMemoryBank):
        fb.upsert_dev_habit(REPO, "bob", "missing input validation", "PR #5")
        habit = fb.upsert_dev_habit(REPO, "bob", "missing input validation", "PR #12")
        assert len(habit.occurrences) == 2
        assert "PR #5" in habit.occurrences
        assert "PR #12" in habit.occurrences

    def test_upsert_idempotent_same_pr(self, fb: FirestoreMemoryBank):
        fb.upsert_dev_habit(REPO, "carol", "hardcoded secrets", "PR #7")
        habit = fb.upsert_dev_habit(REPO, "carol", "hardcoded secrets", "PR #7")
        assert len(habit.occurrences) == 1  # Not duplicated

    def test_get_author_habits_filters_by_author(self, fb: FirestoreMemoryBank):
        fb.upsert_dev_habit(REPO, "alice", "pattern A", "PR #1")
        fb.upsert_dev_habit(REPO, "bob", "pattern B", "PR #2")
        fb.upsert_dev_habit(REPO, "alice", "pattern C", "PR #3")

        alice_habits = fb.get_author_habits(REPO, "alice")
        assert len(alice_habits) == 2
        patterns = {h.pattern for h in alice_habits}
        assert patterns == {"pattern A", "pattern C"}

        bob_habits = fb.get_author_habits(REPO, "bob")
        assert len(bob_habits) == 1
        assert bob_habits[0].pattern == "pattern B"

    def test_get_all_habits(self, fb: FirestoreMemoryBank):
        fb.upsert_dev_habit(REPO, "alice", "p1", "PR #1")
        fb.upsert_dev_habit(REPO, "bob", "p2", "PR #2")
        all_habits = fb.get_all_habits(REPO)
        assert len(all_habits) == 2


# ------------------------------------------------------------------
# Audit Log
# ------------------------------------------------------------------

class TestAuditLog:
    def test_add_and_retrieve_audit_log(self, fb: FirestoreMemoryBank):
        doc_id = fb.add_audit_log(
            REPO,
            AuditLogDocument(
                pr_reference="PR #42",
                action_taken="opened remediation PR #43",
                reasoning_summary="Auto-remediated exposed /health route",
            ),
        )
        assert doc_id.startswith("audit-")

        logs = fb.get_audit_logs(REPO)
        assert len(logs) == 1
        assert logs[0].action_taken == "opened remediation PR #43"

    def test_count_audit_logs(self, fb: FirestoreMemoryBank):
        for i in range(3):
            fb.add_audit_log(
                REPO,
                AuditLogDocument(
                    pr_reference=f"PR #{i}",
                    action_taken=f"action {i}",
                    reasoning_summary=f"reason {i}",
                ),
            )
        assert fb.count_audit_logs(REPO) == 3


# ------------------------------------------------------------------
# Memory Brief
# ------------------------------------------------------------------

class TestMemoryBrief:
    def test_save_and_load_brief(self, fb: FirestoreMemoryBank):
        brief = MemoryBrief(
            repo_id=REPO,
            decisions_summary="2 active decisions about auth and staging.",
            habits_summary="3 patterns: raw SQL (2x), missing validation (1x), hardcoded secrets (1x).",
            total_decisions=2,
            total_habits=3,
            total_audits=5,
            source_decision_count=2,
            source_habit_count=3,
        )
        fb.save_memory_brief(REPO, brief)

        loaded = fb.get_memory_brief(REPO)
        assert loaded is not None
        assert loaded.repo_id == REPO
        assert loaded.total_decisions == 2
        assert loaded.decisions_summary == brief.decisions_summary

    def test_brief_returns_none_when_absent(self, fb: FirestoreMemoryBank):
        assert fb.get_memory_brief("nonexistent_repo") is None

    def test_brief_overwrites_on_save(self, fb: FirestoreMemoryBank):
        fb.save_memory_brief(REPO, MemoryBrief(repo_id=REPO, decisions_summary="v1"))
        fb.save_memory_brief(REPO, MemoryBrief(repo_id=REPO, decisions_summary="v2"))
        loaded = fb.get_memory_brief(REPO)
        assert loaded.decisions_summary == "v2"


# ------------------------------------------------------------------
# Mock mode
# ------------------------------------------------------------------

class TestMockBehaviour:
    def test_is_mock_in_test_mode(self, fb: FirestoreMemoryBank):
        assert fb.is_mock is True

    def test_clear_mock_store(self, fb: FirestoreMemoryBank):
        fb.add_decision(REPO, DecisionDocument(
            description="test", approved_by="x", pr_reference="PR #1"
        ))
        assert fb.count_decisions(REPO) == 1
        fb.clear_mock_store()
        assert fb.count_decisions(REPO) == 0
