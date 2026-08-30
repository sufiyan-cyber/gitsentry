"""Unit tests for commit status manager."""

import pytest
from common.config import Settings
from common.github_client import GitHubClient
from common.models import DeepAuditResult, SecurityFinding, SeverityLevel
from services.worker.status_manager import StatusManager


@pytest.fixture
def settings() -> Settings:
    return Settings(ENVIRONMENT="test", USE_SECRET_MANAGER=False)


@pytest.fixture
def gh(settings) -> GitHubClient:
    client = GitHubClient(settings=settings)
    client.reset_mock()
    return client


@pytest.fixture
def status_mgr(gh, settings) -> StatusManager:
    return StatusManager(github=gh, settings=settings)


class TestStatusLifecycle:
    def test_set_pending(self, status_mgr: StatusManager, gh: GitHubClient):
        result = status_mgr.set_pending("o", "r", "sha123")
        assert result["state"] == "pending"
        assert "in progress" in result["description"]

    def test_set_failure(self, status_mgr: StatusManager, gh: GitHubClient):
        result = status_mgr.set_failure("o", "r", "sha123", finding_count=3)
        assert result["state"] == "failure"
        assert "3" in result["description"]

    def test_set_success(self, status_mgr: StatusManager, gh: GitHubClient):
        result = status_mgr.set_success("o", "r", "sha123", reason="All clear")
        assert result["state"] == "success"
        assert "All clear" in result["description"]


class TestEvaluateAuditResult:
    def test_no_findings_sets_success(self, status_mgr: StatusManager, gh: GitHubClient):
        audit = DeepAuditResult(findings=[], summary="Clean")
        state = status_mgr.evaluate_audit_result("o", "r", "sha", audit)
        assert state == "success"
        assert gh.set_statuses[-1]["state"] == "success"

    def test_high_severity_sets_failure(self, status_mgr: StatusManager, gh: GitHubClient):
        audit = DeepAuditResult(
            findings=[
                SecurityFinding(
                    severity=SeverityLevel.HIGH,
                    line_range="10-15",
                    owasp_category="A03:2021-Injection",
                    explanation="SQL injection",
                    suggested_fix="Use parameterized queries",
                    confidence=0.9,
                ),
            ],
            summary="SQL injection found",
        )
        state = status_mgr.evaluate_audit_result("o", "r", "sha", audit)
        assert state == "failure"

    def test_critical_severity_sets_failure(self, status_mgr: StatusManager, gh: GitHubClient):
        audit = DeepAuditResult(
            findings=[
                SecurityFinding(
                    severity=SeverityLevel.CRITICAL,
                    line_range="1",
                    owasp_category="A07:2021-Auth",
                    explanation="Hardcoded admin password",
                    suggested_fix="Use environment variable",
                    confidence=0.99,
                ),
            ],
            summary="Critical finding",
        )
        state = status_mgr.evaluate_audit_result("o", "r", "sha", audit)
        assert state == "failure"

    def test_medium_only_sets_success(self, status_mgr: StatusManager, gh: GitHubClient):
        audit = DeepAuditResult(
            findings=[
                SecurityFinding(
                    severity=SeverityLevel.MEDIUM,
                    line_range="20",
                    owasp_category="A05",
                    explanation="Overly permissive CORS",
                    suggested_fix="Restrict origins",
                    confidence=0.7,
                ),
            ],
            summary="Medium finding",
        )
        state = status_mgr.evaluate_audit_result("o", "r", "sha", audit)
        assert state == "success"
        assert "non-blocking" in gh.set_statuses[-1]["description"]


class TestClearStatus:
    def test_clear_on_override(self, status_mgr: StatusManager, gh: GitHubClient):
        result = status_mgr.clear_on_override("o", "r", "sha", override_by="alice")
        assert result["state"] == "success"
        assert "alice" in result["description"]

    def test_clear_on_remediation_merged(self, status_mgr: StatusManager, gh: GitHubClient):
        result = status_mgr.clear_on_remediation_merged("o", "r", "sha", remediation_pr_number=99)
        assert result["state"] == "success"
        assert "99" in result["description"]
