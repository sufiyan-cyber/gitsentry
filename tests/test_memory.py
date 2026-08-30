"""Unit tests for the Memory Manager and MemoryContext."""

import pytest
from datetime import datetime, timezone

from common.config import Settings
from common.firestore_client import FirestoreMemoryBank
from common.memory import MemoryManager, _ordinal
from common.models import (
    DecisionDocument,
    DecisionStatus,
    DevHabitDocument,
    ExemptionMatch,
    HabitMatch,
    MemoryBrief,
    MemoryContext,
    SecurityFinding,
    SeverityLevel,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        ENVIRONMENT="test",
        USE_SECRET_MANAGER=False,
        MEMORY_COMPACTION_THRESHOLD=5,
    )


@pytest.fixture
def fb(settings) -> FirestoreMemoryBank:
    bank = FirestoreMemoryBank(settings=settings)
    bank.clear_mock_store()
    return bank


@pytest.fixture
def manager(fb, settings) -> MemoryManager:
    return MemoryManager(firestore=fb, settings=settings)


REPO = "acme_web-app"


# ------------------------------------------------------------------
# Context building
# ------------------------------------------------------------------

class TestBuildContext:
    def test_empty_repo_returns_empty_context(self, manager: MemoryManager):
        ctx = manager.build_context(REPO, "alice")
        assert ctx.repo_id == REPO
        assert ctx.author_id == "alice"
        assert ctx.brief is None
        assert ctx.active_decisions == []
        assert ctx.author_habits == []

    def test_context_includes_active_decisions(self, manager: MemoryManager, fb: FirestoreMemoryBank):
        fb.add_decision(REPO, DecisionDocument(
            description="Staging allows unauthenticated /health route",
            approved_by="sec-lead",
            pr_reference="PR #42",
        ))
        fb.add_decision(REPO, DecisionDocument(
            description="Analytics uses raw SQL by design",
            approved_by="cto",
            pr_reference="PR #15",
        ))

        ctx = manager.build_context(REPO, "alice")
        assert len(ctx.active_decisions) == 2

    def test_context_includes_author_habits(self, manager: MemoryManager, fb: FirestoreMemoryBank):
        fb.upsert_dev_habit(REPO, "alice", "raw SQL concatenation", "PR #10")
        fb.upsert_dev_habit(REPO, "alice", "missing input validation", "PR #12")
        fb.upsert_dev_habit(REPO, "bob", "hardcoded API keys", "PR #20")

        ctx = manager.build_context(REPO, "alice")
        assert len(ctx.author_habits) == 2  # Only Alice's

    def test_context_includes_memory_brief(self, manager: MemoryManager, fb: FirestoreMemoryBank):
        fb.save_memory_brief(REPO, MemoryBrief(
            repo_id=REPO,
            decisions_summary="2 active exemptions.",
            habits_summary="3 tracked patterns.",
        ))
        ctx = manager.build_context(REPO, "alice")
        assert ctx.brief is not None
        assert ctx.brief.decisions_summary == "2 active exemptions."


# ------------------------------------------------------------------
# System prompt rendering
# ------------------------------------------------------------------

class TestSystemPromptRendering:
    def test_empty_context_renders_no_memory_message(self):
        ctx = MemoryContext(repo_id=REPO, author_id="alice")
        text = ctx.to_system_prompt_section()
        assert "No prior memory context available" in text

    def test_full_context_renders_all_sections(self):
        ctx = MemoryContext(
            repo_id=REPO,
            author_id="alice",
            brief=MemoryBrief(
                repo_id=REPO,
                decisions_summary="Staging has auth exemption.",
                habits_summary="SQL patterns tracked.",
            ),
            active_decisions=[
                DecisionDocument(
                    description="Staging allows unauthenticated /health",
                    approved_by="sec-lead",
                    pr_reference="PR #42",
                ),
            ],
            author_habits=[
                DevHabitDocument(
                    pattern="raw SQL concatenation",
                    occurrences=["PR #10", "PR #25"],
                ),
            ],
        )
        text = ctx.to_system_prompt_section()
        assert "Repository Memory Context" in text
        assert "Architectural Decisions" in text
        assert "Staging has auth exemption" in text
        assert "Active Exemptions" in text
        assert "unauthenticated /health" in text
        assert "Developer Habits for @alice" in text
        assert "raw SQL concatenation" in text
        assert "2 time(s)" in text


# ------------------------------------------------------------------
# Exemption matching
# ------------------------------------------------------------------

class TestExemptionMatching:
    def test_matches_active_decision(self):
        ctx = MemoryContext(
            repo_id=REPO,
            author_id="alice",
            active_decisions=[
                DecisionDocument(
                    description="Staging allows unauthenticated /health route",
                    approved_by="sec-lead",
                    pr_reference="PR #42",
                ),
            ],
        )
        result = ctx.find_exemption("unauthenticated /health route on staging")
        assert result.matched is True
        assert result.pr_reference == "PR #42"
        assert result.approved_by == "sec-lead"

    def test_no_match_for_unrelated_finding(self):
        ctx = MemoryContext(
            repo_id=REPO,
            author_id="alice",
            active_decisions=[
                DecisionDocument(
                    description="Staging allows unauthenticated /health route",
                    approved_by="sec-lead",
                    pr_reference="PR #42",
                ),
            ],
        )
        result = ctx.find_exemption("hardcoded AWS credentials in config.py")
        assert result.matched is False

    def test_skips_superseded_decisions(self):
        ctx = MemoryContext(
            repo_id=REPO,
            author_id="alice",
            active_decisions=[
                DecisionDocument(
                    description="Allow raw SQL for analytics",
                    approved_by="cto",
                    pr_reference="PR #15",
                    status=DecisionStatus.SUPERSEDED,
                ),
            ],
        )
        result = ctx.find_exemption("raw SQL string concatenation for analytics")
        assert result.matched is False


# ------------------------------------------------------------------
# Habit matching
# ------------------------------------------------------------------

class TestHabitMatching:
    def test_matches_existing_habit(self):
        ctx = MemoryContext(
            repo_id=REPO,
            author_id="alice",
            author_habits=[
                DevHabitDocument(
                    pattern="raw SQL string concatenation instead of parameterized queries",
                    occurrences=["PR #10", "PR #25"],
                ),
            ],
        )
        result = ctx.find_habit_match("raw SQL string concatenation in user lookup")
        assert result.matched is True
        assert result.occurrence_count == 2
        assert "PR #10" in result.prior_prs

    def test_no_match_for_different_pattern(self):
        ctx = MemoryContext(
            repo_id=REPO,
            author_id="alice",
            author_habits=[
                DevHabitDocument(
                    pattern="raw SQL string concatenation",
                    occurrences=["PR #10"],
                ),
            ],
        )
        result = ctx.find_habit_match("missing CSRF token validation")
        assert result.matched is False


# ------------------------------------------------------------------
# Finding enrichment
# ------------------------------------------------------------------

class TestFindingEnrichment:
    def test_enrichment_with_exemption_and_habit(self, manager: MemoryManager, fb: FirestoreMemoryBank):
        fb.add_decision(REPO, DecisionDocument(
            description="Staging allows unauthenticated /health route",
            approved_by="sec-lead",
            pr_reference="PR #42",
        ))
        fb.upsert_dev_habit(REPO, "alice", "unauthenticated /health route", "PR #10")

        ctx = manager.build_context(REPO, "alice")
        finding = SecurityFinding(
            severity=SeverityLevel.MEDIUM,
            line_range="15-20",
            owasp_category="A01:2021-Broken Access Control",
            explanation="unauthenticated /health route exposed",
            suggested_fix="Add auth middleware",
            confidence=0.85,
        )
        enrichment = manager.enrich_finding(ctx, finding)
        assert enrichment["exemption"].matched is True
        assert enrichment["habit"].matched is True
        assert "Acknowledged exemption" in enrichment["comment_suffix"]
        assert "Recurring pattern" in enrichment["comment_suffix"]


# ------------------------------------------------------------------
# State mutations
# ------------------------------------------------------------------

class TestStateMutations:
    def test_record_decision(self, manager: MemoryManager, fb: FirestoreMemoryBank):
        doc_id = manager.record_decision(
            repo_id=REPO,
            description="Allow plaintext logging in staging",
            approved_by="alice",
            pr_reference="PR #50",
        )
        assert doc_id.startswith("dec-")
        decisions = fb.get_active_decisions(REPO)
        assert len(decisions) == 1
        assert decisions[0].description == "Allow plaintext logging in staging"

    def test_record_finding_habit(self, manager: MemoryManager, fb: FirestoreMemoryBank):
        habit = manager.record_finding_habit(
            repo_id=REPO,
            author_id="bob",
            pattern="missing error handling",
            pr_reference="PR #7",
        )
        assert habit.pattern == "missing error handling"
        assert len(habit.occurrences) == 1

        # Record again — should increment
        habit2 = manager.record_finding_habit(
            repo_id=REPO,
            author_id="bob",
            pattern="missing error handling",
            pr_reference="PR #14",
        )
        assert len(habit2.occurrences) == 2

    def test_record_audit(self, manager: MemoryManager, fb: FirestoreMemoryBank):
        doc_id = manager.record_audit(
            repo_id=REPO,
            pr_reference="PR #42",
            action_taken="blocked merge",
            reasoning_summary="High-severity SQL injection found",
        )
        assert doc_id.startswith("audit-")
        logs = fb.get_audit_logs(REPO)
        assert len(logs) == 1


# ------------------------------------------------------------------
# Compaction threshold check
# ------------------------------------------------------------------

class TestCompactionThreshold:
    def test_should_compact_below_threshold(self, manager: MemoryManager):
        assert manager.should_compact(REPO) is False

    def test_should_compact_above_threshold(self, manager: MemoryManager, fb: FirestoreMemoryBank):
        # Threshold is 5 — add 5 decisions to trigger
        for i in range(5):
            fb.add_decision(REPO, DecisionDocument(
                description=f"Decision {i}",
                approved_by="admin",
                pr_reference=f"PR #{i}",
            ))
        assert manager.should_compact(REPO) is True


# ------------------------------------------------------------------
# Ordinal helper
# ------------------------------------------------------------------

class TestOrdinal:
    @pytest.mark.parametrize("n,expected", [
        (1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"),
        (11, "11th"), (12, "12th"), (13, "13th"),
        (21, "21st"), (22, "22nd"), (23, "23rd"), (100, "100th"),
    ])
    def test_ordinal(self, n, expected):
        assert _ordinal(n) == expected
