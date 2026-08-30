"""Unit tests for the Memory Compaction engine."""

import pytest
from datetime import datetime, timezone

from common.config import Settings
from common.firestore_client import FirestoreMemoryBank
from common.compaction import MemoryCompactor
from common.models import (
    AuditLogDocument,
    DecisionDocument,
    DecisionStatus,
    DevHabitDocument,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        ENVIRONMENT="test",
        USE_SECRET_MANAGER=False,
        MEMORY_COMPACTION_THRESHOLD=5,
        MEMORY_BRIEF_MAX_TOKENS=2000,
    )


@pytest.fixture
def fb(settings) -> FirestoreMemoryBank:
    bank = FirestoreMemoryBank(settings=settings)
    bank.clear_mock_store()
    return bank


@pytest.fixture
def compactor(fb, settings) -> MemoryCompactor:
    return MemoryCompactor(firestore=fb, settings=settings)


REPO = "acme_web-app"


class TestCompaction:
    def test_compact_empty_repo(self, compactor: MemoryCompactor):
        brief = compactor.compact(REPO)
        assert brief.repo_id == REPO
        assert brief.total_decisions == 0
        assert brief.total_habits == 0
        assert brief.decisions_summary == ""
        assert brief.habits_summary == ""

    def test_compact_with_decisions(self, compactor: MemoryCompactor, fb: FirestoreMemoryBank):
        fb.add_decision(REPO, DecisionDocument(
            description="Staging allows unauthenticated /health route",
            approved_by="sec-lead",
            pr_reference="PR #42",
        ))
        fb.add_decision(REPO, DecisionDocument(
            description="Analytics dashboard uses raw SQL by design",
            approved_by="cto",
            pr_reference="PR #15",
        ))

        brief = compactor.compact(REPO)
        assert brief.total_decisions == 2
        assert brief.source_decision_count == 2
        assert "unauthenticated /health" in brief.decisions_summary
        assert "raw SQL" in brief.decisions_summary
        assert "2 active decision" in brief.decisions_summary

    def test_compact_with_superseded_decisions(self, compactor: MemoryCompactor, fb: FirestoreMemoryBank):
        doc_id = fb.add_decision(REPO, DecisionDocument(
            description="Allow legacy API without auth",
            approved_by="cto",
            pr_reference="PR #5",
        ))
        fb.supersede_decision(REPO, doc_id)
        fb.add_decision(REPO, DecisionDocument(
            description="New API requires auth",
            approved_by="sec-lead",
            pr_reference="PR #50",
        ))

        brief = compactor.compact(REPO)
        assert "1 active decision" in brief.decisions_summary
        assert "1 superseded decision" in brief.decisions_summary

    def test_compact_with_habits(self, compactor: MemoryCompactor, fb: FirestoreMemoryBank):
        fb.upsert_dev_habit(REPO, "alice", "raw SQL concatenation", "PR #10")
        fb.upsert_dev_habit(REPO, "alice", "raw SQL concatenation", "PR #25")
        fb.upsert_dev_habit(REPO, "bob", "missing input validation", "PR #12")

        brief = compactor.compact(REPO)
        assert brief.total_habits == 2
        assert "raw SQL" in brief.habits_summary
        assert "missing input validation" in brief.habits_summary
        assert "2 tracked developer pattern" in brief.habits_summary

    def test_compact_with_audit_logs(self, compactor: MemoryCompactor, fb: FirestoreMemoryBank):
        fb.add_audit_log(REPO, AuditLogDocument(
            pr_reference="PR #42",
            action_taken="blocked merge",
            reasoning_summary="SQL injection",
        ))
        fb.add_audit_log(REPO, AuditLogDocument(
            pr_reference="PR #43",
            action_taken="opened remediation PR #44",
            reasoning_summary="Auto-fix applied",
        ))

        brief = compactor.compact(REPO)
        assert brief.total_audits == 2

    def test_compact_saves_brief_to_firestore(self, compactor: MemoryCompactor, fb: FirestoreMemoryBank):
        fb.add_decision(REPO, DecisionDocument(
            description="Test decision",
            approved_by="admin",
            pr_reference="PR #1",
        ))
        compactor.compact(REPO)

        loaded = fb.get_memory_brief(REPO)
        assert loaded is not None
        assert loaded.repo_id == REPO
        assert loaded.total_decisions == 1

    def test_compact_overwrites_previous_brief(self, compactor: MemoryCompactor, fb: FirestoreMemoryBank):
        fb.add_decision(REPO, DecisionDocument(
            description="First pass",
            approved_by="admin",
            pr_reference="PR #1",
        ))
        compactor.compact(REPO)

        fb.add_decision(REPO, DecisionDocument(
            description="Second decision",
            approved_by="admin",
            pr_reference="PR #2",
        ))
        compactor.compact(REPO)

        loaded = fb.get_memory_brief(REPO)
        assert loaded.total_decisions == 2


class TestCompactionThreshold:
    def test_should_compact_false_below_threshold(self, compactor: MemoryCompactor, fb: FirestoreMemoryBank):
        fb.add_decision(REPO, DecisionDocument(
            description="d1", approved_by="a", pr_reference="PR #1"
        ))
        assert compactor.should_compact(REPO) is False

    def test_should_compact_true_at_threshold(self, compactor: MemoryCompactor, fb: FirestoreMemoryBank):
        for i in range(5):
            fb.add_decision(REPO, DecisionDocument(
                description=f"d{i}", approved_by="a", pr_reference=f"PR #{i}"
            ))
        assert compactor.should_compact(REPO) is True

    def test_should_compact_counts_both_collections(self, compactor: MemoryCompactor, fb: FirestoreMemoryBank):
        for i in range(3):
            fb.add_decision(REPO, DecisionDocument(
                description=f"d{i}", approved_by="a", pr_reference=f"PR #{i}"
            ))
        fb.upsert_dev_habit(REPO, "alice", "pattern1", "PR #10")
        fb.upsert_dev_habit(REPO, "bob", "pattern2", "PR #11")

        # 3 decisions + 2 habits = 5 >= threshold of 5
        assert compactor.should_compact(REPO) is True


class TestTruncation:
    def test_truncate_long_text(self, compactor: MemoryCompactor):
        long_text = "A" * 20000
        result = MemoryCompactor._truncate(long_text, budget=100)
        assert len(result) <= 400 + 30  # 100 tokens * 4 chars + truncation notice
        assert "[truncated" in result

    def test_truncate_short_text(self, compactor: MemoryCompactor):
        short_text = "Short summary"
        result = MemoryCompactor._truncate(short_text, budget=1000)
        assert result == short_text  # Not truncated


class TestManyDecisionsSummary:
    def test_many_superseded_shows_ellipsis(self, compactor: MemoryCompactor, fb: FirestoreMemoryBank):
        for i in range(10):
            doc_id = fb.add_decision(REPO, DecisionDocument(
                description=f"Old decision {i}",
                approved_by="admin",
                pr_reference=f"PR #{i}",
            ))
            fb.supersede_decision(REPO, doc_id)

        brief = compactor.compact(REPO)
        assert "10 superseded" in brief.decisions_summary
        assert "… and" in brief.decisions_summary
