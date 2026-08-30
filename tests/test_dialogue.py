"""Unit tests for the Socratic multi-turn dialogue handler."""

import pytest
from common.config import Settings
from common.firestore_client import FirestoreMemoryBank
from common.github_client import GitHubClient
from common.memory import MemoryManager
from common.models import DecisionDocument, DecisionStatus
from services.worker.dialogue import DialogueHandler, JustificationStrength


@pytest.fixture
def settings() -> Settings:
    return Settings(
        ENVIRONMENT="test",
        USE_SECRET_MANAGER=False,
        SOCRATIC_WEAK_JUSTIFICATION_MIN_WORDS=8,
    )


@pytest.fixture
def gh(settings) -> GitHubClient:
    client = GitHubClient(settings=settings)
    client.reset_mock()
    return client


@pytest.fixture
def fb(settings) -> FirestoreMemoryBank:
    bank = FirestoreMemoryBank(settings=settings)
    bank.clear_mock_store()
    return bank


@pytest.fixture
def memory(fb, settings) -> MemoryManager:
    return MemoryManager(firestore=fb, settings=settings)


@pytest.fixture
def dialogue(gh, memory, settings) -> DialogueHandler:
    return DialogueHandler(github=gh, memory=memory, settings=settings)


class TestIsOverrideRequest:
    def test_detects_override_keywords(self, dialogue: DialogueHandler):
        assert dialogue.is_override_request("@gitsentry please override this finding") is True
        assert dialogue.is_override_request("This is an approved exception for staging") is True
        assert dialogue.is_override_request("This behavior is by design for analytics") is True
        assert dialogue.is_override_request("This is a false positive") is True

    def test_ignores_non_override_comments(self, dialogue: DialogueHandler):
        assert dialogue.is_override_request("Can you explain how this vulnerability works?") is False
        assert dialogue.is_override_request("Looks good to me, thanks!") is False


class TestEvaluateJustification:
    def test_absent_justification(self, dialogue: DialogueHandler):
        assert dialogue.evaluate_justification("") == JustificationStrength.ABSENT
        assert dialogue.evaluate_justification("@gitsentry") == JustificationStrength.ABSENT
        assert dialogue.evaluate_justification("  @gitsentry   ") == JustificationStrength.ABSENT

    def test_weak_justification_too_short(self, dialogue: DialogueHandler):
        # Only 3-4 substantive words (< 8)
        assert dialogue.evaluate_justification("@gitsentry override please") == JustificationStrength.WEAK
        assert dialogue.evaluate_justification("It's fine, allow it.") == JustificationStrength.WEAK

    def test_strong_justification(self, dialogue: DialogueHandler):
        strong_comment = (
            "@gitsentry This unauthenticated /health route is temporary and exclusively "
            "used by our internal synthetic monitoring agent in the staging environment. "
            "Compensating network controls prevent public access."
        )
        assert dialogue.evaluate_justification(strong_comment) == JustificationStrength.STRONG


class TestProcessComment:
    def test_ignores_bot_own_comments(self, dialogue: DialogueHandler, gh: GitHubClient):
        res = dialogue.process_comment(
            owner="octocat",
            repo="demo-repo",
            pr_number=42,
            comment_body="🛡️ GitSentry Security Audit Results...",
            comment_author="gitsentry[bot]",
        )
        assert res.action == "ignored"
        assert len(gh.posted_comments) == 0

    def test_weak_justification_triggers_socratic_pushback(
        self, dialogue: DialogueHandler, gh: GitHubClient
    ):
        res = dialogue.process_comment(
            owner="octocat",
            repo="demo-repo",
            pr_number=42,
            comment_body="@gitsentry please override this, it is fine",
            comment_author="dev-alice",
        )

        assert res.action == "pushback"
        assert res.decision_recorded is False
        assert res.status_cleared is False
        assert "Could you clarify" in res.reply_body or "justification" in res.reply_body
        assert len(gh.posted_comments) == 1

    def test_strong_justification_accepts_and_records_decision(
        self, dialogue: DialogueHandler, gh: GitHubClient, fb: FirestoreMemoryBank
    ):
        strong_text = (
            "@gitsentry We need an exception here. The /health endpoint on staging is "
            "monitored by our internal VPC probe which does not support auth headers. "
            "Network security groups restrict access strictly to the VPC."
        )

        res = dialogue.process_comment(
            owner="octocat",
            repo="demo-repo",
            pr_number=42,
            comment_body=strong_text,
            comment_author="dev-alice",
            repo_id="octocat_demo-repo",
        )

        assert res.action == "accepted_override"
        assert res.decision_recorded is True
        assert res.status_cleared is True
        assert "Override accepted and recorded" in res.reply_body

        # Verify recorded in Firestore decisions collection
        decisions = fb.get_active_decisions("octocat_demo-repo")
        assert len(decisions) == 1
        assert decisions[0].approved_by == "dev-alice"
        assert decisions[0].pr_reference == "PR #42"
        assert decisions[0].status == DecisionStatus.ACTIVE

        # Verify audit log was recorded
        logs = fb.get_audit_logs("octocat_demo-repo")
        assert len(logs) == 1
        assert "accepted override" in logs[0].action_taken

        # Verify comment was posted
        assert len(gh.posted_comments) == 1

    def test_non_override_question_returns_informational(
        self, dialogue: DialogueHandler
    ):
        res = dialogue.process_comment(
            owner="octocat",
            repo="demo-repo",
            pr_number=42,
            comment_body="What dependencies were changed in this PR?",
            comment_author="dev-bob",
        )
        assert res.action == "informational"
        assert res.decision_recorded is False
