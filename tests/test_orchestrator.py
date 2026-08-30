"""Unit tests for the Worker Orchestrator end-to-end pipeline."""

import pytest
from common.config import Settings
from common.firestore_client import FirestoreMemoryBank
from common.github_client import GitHubClient
from common.memory import MemoryManager
from common.models import (
    DeepAuditResult,
    EventType,
    GitHubGitRef,
    GitHubIssueComment,
    GitHubPullRequest,
    GitHubRepository,
    GitHubUser,
    NormalizedGitHubEvent,
    SecurityFinding,
    SeverityLevel,
)
from common.compaction import MemoryCompactor
from services.worker.dialogue import DialogueHandler
from services.worker.orchestrator import WorkerOrchestrator
from services.worker.remediation import RemediationEngine
from services.worker.status_manager import StatusManager


@pytest.fixture
def settings() -> Settings:
    return Settings(
        ENVIRONMENT="test",
        USE_SECRET_MANAGER=False,
        REMEDIATION_CONFIDENCE_THRESHOLD=0.85,
        SOCRATIC_WEAK_JUSTIFICATION_MIN_WORDS=8,
        MEMORY_COMPACTION_THRESHOLD=5,
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
def compactor(fb, settings) -> MemoryCompactor:
    return MemoryCompactor(firestore=fb, settings=settings)


@pytest.fixture
def orchestrator(gh, memory, compactor, settings) -> WorkerOrchestrator:
    status_mgr = StatusManager(github=gh, settings=settings)
    remediation = RemediationEngine(github=gh, memory=memory, settings=settings)
    dialogue = DialogueHandler(github=gh, memory=memory, settings=settings)
    return WorkerOrchestrator(
        github=gh,
        memory=memory,
        compactor=compactor,
        status_mgr=status_mgr,
        remediation=remediation,
        dialogue=dialogue,
        settings=settings,
    )


class TestPullRequestPipeline:
    def test_handle_pr_event_sets_pending_and_loads_memory(
        self, orchestrator: WorkerOrchestrator, gh: GitHubClient
    ):
        event = NormalizedGitHubEvent(
            event_id="deliv-pr-1",
            event_type=EventType.PULL_REQUEST,
            action="opened",
            repository=GitHubRepository(id=1, name="web", full_name="acme/web"),
            sender=GitHubUser(id=2, login="alice"),
            pull_request=GitHubPullRequest(
                id=10,
                number=42,
                title="Add new feature",
                user=GitHubUser(id=2, login="alice"),
                head=GitHubGitRef(sha="sha4242", ref="feat/new"),
                base=GitHubGitRef(sha="sha0000", ref="main"),
            ),
            issue_number=42,
            is_pull_request=True,
        )

        result = orchestrator.process_event(event)

        assert result["status"] == "processed"
        assert result["pr_number"] == 42
        assert result["memory_context_loaded"] is True
        assert len(gh.set_statuses) == 1
        assert gh.set_statuses[0]["state"] == "pending"

    def test_process_audit_result_creates_remediation_and_blocks_status(
        self, orchestrator: WorkerOrchestrator, gh: GitHubClient, fb: FirestoreMemoryBank
    ):
        event = NormalizedGitHubEvent(
            event_id="deliv-pr-2",
            event_type=EventType.PULL_REQUEST,
            action="opened",
            repository=GitHubRepository(id=1, name="web", full_name="acme/web"),
            sender=GitHubUser(id=2, login="alice"),
            pull_request=GitHubPullRequest(
                id=10,
                number=42,
                title="Add staging health route",
                user=GitHubUser(id=2, login="alice"),
                head=GitHubGitRef(sha="sha4242", ref="feat/health"),
                base=GitHubGitRef(sha="sha0000", ref="main"),
            ),
            issue_number=42,
            is_pull_request=True,
        )

        audit_result = DeepAuditResult(
            findings=[
                SecurityFinding(
                    severity=SeverityLevel.HIGH,
                    line_range="12-18",
                    owasp_category="A01:2021-Broken Access Control",
                    explanation="Unauthenticated /health route exposed to public",
                    suggested_fix="add_jwt_middleware()",
                    confidence=0.95,
                    file_path="routes/health.py",
                )
            ],
            summary="High severity vulnerability found",
            remediation_recommendation="BLOCK_MERGE",
        )

        res = orchestrator.process_audit_result(event, audit_result)

        assert res["status"] == "audit_processed"
        assert res["remediation_prs"] == 1
        assert res["commit_status"] == "failure"

        # Verify PR comment posted
        assert len(gh.posted_comments) == 1
        assert "Auto-remediation PR opened" in gh.posted_comments[0]["body"]

        # Verify remediation PR created
        assert len(gh.created_prs) == 1


class TestIssueCommentPipeline:
    def test_handle_override_comment_clears_status_and_records_decision(
        self, orchestrator: WorkerOrchestrator, gh: GitHubClient, fb: FirestoreMemoryBank
    ):
        event = NormalizedGitHubEvent(
            event_id="deliv-comment-1",
            event_type=EventType.ISSUE_COMMENT,
            action="created",
            repository=GitHubRepository(id=1, name="web", full_name="acme/web"),
            sender=GitHubUser(id=2, login="alice"),
            issue_number=42,
            is_pull_request=True,
            pull_request=GitHubPullRequest(
                id=10,
                number=42,
                title="Add staging health route",
                user=GitHubUser(id=2, login="alice"),
                head=GitHubGitRef(sha="sha4242", ref="feat/health"),
                base=GitHubGitRef(sha="sha0000", ref="main"),
            ),
            issue_comment=GitHubIssueComment(
                id=999,
                body="@gitsentry override: Staging environment allows unauthenticated /health route for synthetic monitor probe strictly within the private VPC.",
                user=GitHubUser(id=2, login="alice"),
            ),
        )

        res = orchestrator.process_event(event)

        assert res["status"] == "comment_processed"
        assert res["action"] == "accepted_override"
        assert res["decision_recorded"] is True
        assert res["status_cleared"] is True

        # Verify decision recorded in Firestore
        decisions = fb.get_active_decisions("acme_web")
        assert len(decisions) == 1
        assert "unauthenticated /health" in decisions[0].description

        # Verify status cleared (set to success)
        assert any(s["state"] == "success" for s in gh.set_statuses)
