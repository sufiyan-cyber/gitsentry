"""Unit tests for Pydantic models, event normalizers, and Firestore schemas."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from common.models import (
    AuditLogDocument,
    DecisionDocument,
    DecisionStatus,
    DeepAuditResult,
    DevHabitDocument,
    EventType,
    GitHubGitRef,
    GitHubIssueComment,
    GitHubPullRequest,
    GitHubRepository,
    GitHubUser,
    NormalizedGitHubEvent,
    SecurityFinding,
    SeverityLevel,
    TriageResult,
)


def test_github_pull_request_properties():
    pr = GitHubPullRequest(
        number=42,
        id=10042,
        title="Add auth middleware",
        user=GitHubUser(login="alice", id=1),
        head=GitHubGitRef(sha="abcdef123456", ref="feat/auth"),
        base=GitHubGitRef(sha="9876543210fe", ref="main"),
    )

    assert pr.number == 42
    assert pr.head_sha == "abcdef123456"
    assert pr.base_sha == "9876543210fe"
    assert pr.author_login == "alice"


def test_normalized_event_repo_id_and_author():
    repo = GitHubRepository(id=1, name="gitsentry-core", full_name="acme/gitsentry-core")
    sender = GitHubUser(id=2, login="bob")
    pr = GitHubPullRequest(
        number=7,
        id=107,
        title="Update deps",
        user=GitHubUser(login="carol", id=3),
    )

    event = NormalizedGitHubEvent(
        event_id="deliv-12345",
        event_type=EventType.PULL_REQUEST,
        action="opened",
        repository=repo,
        sender=sender,
        pull_request=pr,
        issue_number=7,
        is_pull_request=True,
    )

    assert event.get_repo_id() == "acme_gitsentry-core"
    assert event.get_author_login() == "carol"


def test_security_finding_confidence_bounds():
    # Valid finding
    finding = SecurityFinding(
        severity=SeverityLevel.HIGH,
        line_range="15-20",
        owasp_category="A03:2021-Injection",
        explanation="SQL concatenation found",
        suggested_fix="Use db.execute('SELECT * FROM users WHERE id = :id', {'id': user_id})",
        confidence=0.95,
        file_path="src/auth.py",
    )
    assert finding.confidence == 0.95
    assert finding.severity == SeverityLevel.HIGH

    # Invalid confidence > 1.0
    with pytest.raises(ValidationError):
        SecurityFinding(
            severity=SeverityLevel.HIGH,
            line_range="1",
            owasp_category="A03",
            explanation="Test",
            suggested_fix="Fix",
            confidence=1.5,
        )


def test_firestore_schemas():
    # Decision document
    decision = DecisionDocument(
        description="Staging env allows unauthenticated /health route",
        approved_by="sec-team-lead",
        pr_reference="PR #42",
    )
    assert decision.status == DecisionStatus.ACTIVE
    assert decision.pr_reference == "PR #42"

    # Dev Habit document
    habit = DevHabitDocument(
        pattern="raw SQL string concatenation instead of parameterized queries",
        occurrences=["PR #10", "PR #42"],
    )
    assert len(habit.occurrences) == 2

    # Audit log document
    log = AuditLogDocument(
        pr_reference="PR #42",
        action_taken="opened remediation PR #43",
        reasoning_summary="Auto-remediated exposed secret with secret manager binding",
    )
    assert log.action_taken == "opened remediation PR #43"
