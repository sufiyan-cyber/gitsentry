"""End-to-end integration test verifying the 3-beat demo script from PRD Section 5.

Verifies:
  1. PR #1: Socratic pushback on weak justification, acceptance on strong justification,
     writing to Firestore decisions, commit status clearing.
  2. PR #2: Memory retrieval of PR #1 decision, auto-opening remediation PR, blocking merge.
  3. PR #3: dev_habits tracking detecting recurring pattern, citing occurrence count and prior PR.
"""

import pytest
from common.config import Settings
from common.firestore_client import FirestoreMemoryBank
from common.github_client import GitHubClient
from common.memory import MemoryManager
from common.compaction import MemoryCompactor
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
from services.worker.dialogue import DialogueHandler
from services.worker.orchestrator import WorkerOrchestrator
from services.worker.remediation import RemediationEngine
from services.worker.status_manager import StatusManager


@pytest.fixture
def demo_env():
    settings = Settings(
        ENVIRONMENT="test",
        USE_SECRET_MANAGER=False,
        REMEDIATION_CONFIDENCE_THRESHOLD=0.85,
        SOCRATIC_WEAK_JUSTIFICATION_MIN_WORDS=8,
    )
    gh = GitHubClient(settings=settings)
    gh.reset_mock()
    fb = FirestoreMemoryBank(settings=settings)
    fb.clear_mock_store()
    memory = MemoryManager(firestore=fb, settings=settings)
    compactor = MemoryCompactor(firestore=fb, settings=settings)
    status_mgr = StatusManager(github=gh, settings=settings)
    remediation = RemediationEngine(github=gh, memory=memory, settings=settings)
    dialogue = DialogueHandler(github=gh, memory=memory, settings=settings)

    orchestrator = WorkerOrchestrator(
        github=gh,
        memory=memory,
        compactor=compactor,
        status_mgr=status_mgr,
        remediation=remediation,
        dialogue=dialogue,
        settings=settings,
    )

    return {
        "orchestrator": orchestrator,
        "gh": gh,
        "fb": fb,
        "memory": memory,
        "repo_full_name": "octocat/demo-repo",
        "repo_id": "octocat_demo-repo",
        "author_id": "dev-alice",
    }


def test_full_three_pr_demo_scenario(demo_env):
    orchestrator = demo_env["orchestrator"]
    gh = demo_env["gh"]
    fb = demo_env["fb"]
    memory = demo_env["memory"]
    repo_full_name = demo_env["repo_full_name"]
    repo_id = demo_env["repo_id"]
    author_id = demo_env["author_id"]

    # -------------------------------------------------------------------------
    # BEAT 1: PR #1 - Socratic Dialogue & Exemption Loop
    # -------------------------------------------------------------------------
    pr1_event = NormalizedGitHubEvent(
        event_id="evt-pr-1",
        event_type=EventType.PULL_REQUEST,
        action="opened",
        repository=GitHubRepository(id=1, name="demo-repo", full_name=repo_full_name),
        sender=GitHubUser(id=10, login=author_id),
        pull_request=GitHubPullRequest(
            id=101,
            number=1,
            title="Add staging health route",
            user=GitHubUser(id=10, login=author_id),
            head=GitHubGitRef(sha="sha-pr1", ref="feat/health-staging"),
            base=GitHubGitRef(sha="sha-base", ref="main"),
        ),
        issue_number=1,
        is_pull_request=True,
    )

    # Initial PR opened -> set pending and processed through audit
    res_pr1 = orchestrator.process_event(pr1_event)
    assert res_pr1["status"] in ("processed", "audit_processed")
    assert any(s["state"] == "pending" for s in gh.set_statuses)
    assert gh.set_statuses[-1]["state"] == "failure"

    # Thin comment justification -> Socratic pushback (not accepted)
    thin_comment = NormalizedGitHubEvent(
        event_id="evt-com-1",
        event_type=EventType.ISSUE_COMMENT,
        action="created",
        repository=GitHubRepository(id=1, name="demo-repo", full_name=repo_full_name),
        sender=GitHubUser(id=10, login=author_id),
        issue_number=1,
        is_pull_request=True,
        pull_request=pr1_event.pull_request,
        issue_comment=GitHubIssueComment(
            id=201,
            body="@gitsentry override please, this is fine",
            user=GitHubUser(id=10, login=author_id),
        ),
    )
    res_thin = orchestrator.process_event(thin_comment)
    assert res_thin["action"] == "pushback"
    assert res_thin["decision_recorded"] is False
    assert res_thin["status_cleared"] is False

    # Strong justification -> Accepted, recorded, and status cleared
    strong_comment = NormalizedGitHubEvent(
        event_id="evt-com-2",
        event_type=EventType.ISSUE_COMMENT,
        action="created",
        repository=GitHubRepository(id=1, name="demo-repo", full_name=repo_full_name),
        sender=GitHubUser(id=10, login=author_id),
        issue_number=1,
        is_pull_request=True,
        pull_request=pr1_event.pull_request,
        issue_comment=GitHubIssueComment(
            id=202,
            body="@gitsentry override justification: Staging unauthenticated /health route is used exclusively by internal VPC synthetic probes with network firewall isolation.",
            user=GitHubUser(id=10, login=author_id),
        ),
    )
    res_strong = orchestrator.process_event(strong_comment)
    assert res_strong["action"] == "accepted_override"
    assert res_strong["decision_recorded"] is True
    assert res_strong["status_cleared"] is True

    # Confirm decision recorded in Firestore
    decisions = fb.get_active_decisions(repo_id)
    assert len(decisions) == 1
    assert decisions[0].pr_reference == "PR #1"

    # Confirm status set to success
    assert gh.set_statuses[-1]["state"] == "success"

    # -------------------------------------------------------------------------
    # BEAT 2: PR #2 - Cross-PR Memory & Autonomous Remediation PR
    # -------------------------------------------------------------------------
    pr2_event = NormalizedGitHubEvent(
        event_id="evt-pr-2",
        event_type=EventType.PULL_REQUEST,
        action="opened",
        repository=GitHubRepository(id=1, name="demo-repo", full_name=repo_full_name),
        sender=GitHubUser(id=10, login=author_id),
        pull_request=GitHubPullRequest(
            id=102,
            number=2,
            title="Expose health on production",
            user=GitHubUser(id=10, login=author_id),
            head=GitHubGitRef(sha="sha-pr2", ref="feat/health-prod"),
            base=GitHubGitRef(sha="sha-base", ref="main"),
        ),
        issue_number=2,
        is_pull_request=True,
    )

    audit2 = DeepAuditResult(
        findings=[
            SecurityFinding(
                severity=SeverityLevel.HIGH,
                line_range="10-15",
                owasp_category="A01:2021-Broken Access Control",
                explanation="Production route /health is unauthenticated (violates PR #1 staging-only exemption)",
                suggested_fix="from auth import require_jwt\n@app.get('/health', dependencies=[Depends(require_jwt)])",
                confidence=0.96,
                file_path="src/health.py",
            )
        ],
        summary="Production vulnerability not covered by staging exemption",
    )

    res_audit2 = orchestrator.process_audit_result(pr2_event, audit2)
    assert res_audit2["remediation_prs"] == 1
    assert res_audit2["commit_status"] == "failure"
    assert len(gh.created_prs) == 2
    assert gh.created_prs[-1]["head"].startswith("gitsentry/fix-")

    # -------------------------------------------------------------------------
    # BEAT 3: PR #3 - Developer Habit Adaptation (2nd Occurrence)
    # -------------------------------------------------------------------------
    # Seed prior occurrence of raw SQL pattern
    fb.upsert_dev_habit(
        repo_id=repo_id,
        author_id=author_id,
        pattern="raw SQL string concatenation instead of parameterized queries",
        pr_reference="PR #0",
    )

    pr3_event = NormalizedGitHubEvent(
        event_id="evt-pr-3",
        event_type=EventType.PULL_REQUEST,
        action="opened",
        repository=GitHubRepository(id=1, name="demo-repo", full_name=repo_full_name),
        sender=GitHubUser(id=10, login=author_id),
        pull_request=GitHubPullRequest(
            id=103,
            number=3,
            title="User search query",
            user=GitHubUser(id=10, login=author_id),
            head=GitHubGitRef(sha="sha-pr3", ref="feat/user-search"),
            base=GitHubGitRef(sha="sha-base", ref="main"),
        ),
        issue_number=3,
        is_pull_request=True,
    )

    audit3 = DeepAuditResult(
        findings=[
            SecurityFinding(
                severity=SeverityLevel.HIGH,
                line_range="30-35",
                owasp_category="A03:2021-Injection",
                explanation="raw SQL string concatenation instead of parameterized queries in user lookup",
                suggested_fix="cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                confidence=0.95,
                file_path="src/search.py",
            )
        ],
        summary="SQL injection found",
    )

    res_audit3 = orchestrator.process_audit_result(pr3_event, audit3)
    latest_comment = gh.posted_comments[-1]["body"]

    assert "Recurring pattern" in latest_comment
    assert "2nd time" in latest_comment
    assert "PR #0" in latest_comment
    assert res_audit3["remediation_prs"] == 1
