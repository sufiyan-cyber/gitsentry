"""Unit tests for the autonomous remediation engine."""

import pytest
from common.config import Settings
from common.firestore_client import FirestoreMemoryBank
from common.github_client import GitHubClient
from common.memory import MemoryManager
from common.models import SecurityFinding, SeverityLevel
from services.worker.remediation import RemediationEngine


@pytest.fixture
def settings() -> Settings:
    return Settings(
        ENVIRONMENT="test",
        USE_SECRET_MANAGER=False,
        REMEDIATION_CONFIDENCE_THRESHOLD=0.85,
        MAX_REMEDIATION_DIFF_LINES=50,
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
def engine(gh, memory, settings) -> RemediationEngine:
    return RemediationEngine(github=gh, memory=memory, settings=settings)


class TestCanAutoRemediate:
    def test_qualifies_when_high_confidence_single_file(self, engine: RemediationEngine):
        finding = SecurityFinding(
            severity=SeverityLevel.HIGH,
            line_range="10-15",
            owasp_category="A03:2021-Injection",
            explanation="SQL injection vulnerability",
            suggested_fix="cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
            confidence=0.95,
            file_path="src/auth.py",
        )
        assert engine.can_auto_remediate(finding) is True

    def test_disqualifies_low_confidence(self, engine: RemediationEngine):
        finding = SecurityFinding(
            severity=SeverityLevel.HIGH,
            line_range="10-15",
            owasp_category="A03:2021-Injection",
            explanation="Possible SQL injection",
            suggested_fix="cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
            confidence=0.75,  # Below 0.85 threshold
            file_path="src/auth.py",
        )
        assert engine.can_auto_remediate(finding) is False

    def test_disqualifies_missing_file_path(self, engine: RemediationEngine):
        finding = SecurityFinding(
            severity=SeverityLevel.HIGH,
            line_range="10-15",
            owasp_category="A03:2021-Injection",
            explanation="SQL injection",
            suggested_fix="fix",
            confidence=0.95,
            file_path=None,
        )
        assert engine.can_auto_remediate(finding) is False

    def test_disqualifies_oversized_fix(self, engine: RemediationEngine):
        long_fix = "\n".join([f"line_{i} = True" for i in range(60)])
        finding = SecurityFinding(
            severity=SeverityLevel.HIGH,
            line_range="1-100",
            owasp_category="A01",
            explanation="Complex refactor",
            suggested_fix=long_fix,
            confidence=0.95,
            file_path="src/large.py",
        )
        assert engine.can_auto_remediate(finding) is False


class TestCreateRemediationPR:
    def test_auto_opens_pr_for_eligible_finding(self, engine: RemediationEngine, gh: GitHubClient):
        finding = SecurityFinding(
            severity=SeverityLevel.HIGH,
            line_range="25-30",
            owasp_category="A01:2021-Broken Access Control",
            explanation="Missing authentication check on /health route in production",
            suggested_fix="@app.middleware('http')\nasync def auth_middleware(request, call_next):\n    return await call_next(request)",
            confidence=0.95,
            file_path="src/api/routes.py",
        )

        result = engine.create_remediation_pr(
            owner="octocat",
            repo="demo-repo",
            original_pr_number=42,
            base_branch="main",
            head_sha="headsha12345",
            finding=finding,
        )

        assert result.action == "remediation_pr"
        assert result.pr_number == 100
        assert "gitsentry/fix-" in result.branch_name
        assert len(gh.created_branches) == 1
        assert len(gh.created_prs) == 1
        assert gh.created_prs[0]["title"].startswith("🔒 GitSentry Fix:")

    def test_falls_back_to_suggestion_comment_for_low_confidence(self, engine: RemediationEngine, gh: GitHubClient):
        finding = SecurityFinding(
            severity=SeverityLevel.MEDIUM,
            line_range="10",
            owasp_category="A05:2021-Security Misconfiguration",
            explanation="Overly broad CORS header",
            suggested_fix="allow_origins=['https://example.com']",
            confidence=0.60,
            file_path="src/server.py",
        )

        result = engine.create_remediation_pr(
            owner="octocat",
            repo="demo-repo",
            original_pr_number=42,
            base_branch="main",
            head_sha="headsha12345",
            finding=finding,
        )

        assert result.action == "suggestion_comment"
        assert result.pr_number is None
        assert "```suggestion" in result.comment_body
        assert len(gh.created_prs) == 0


class TestProcessFindings:
    def test_process_multiple_findings_records_habits_and_audit(
        self, engine: RemediationEngine, fb: FirestoreMemoryBank
    ):
        findings = [
            SecurityFinding(
                severity=SeverityLevel.HIGH,
                line_range="10",
                owasp_category="A03:2021-Injection",
                explanation="raw SQL concatenation query",
                suggested_fix="db.execute('SELECT * FROM users WHERE id = %s', (uid,))",
                confidence=0.95,
                file_path="src/db.py",
            ),
            SecurityFinding(
                severity=SeverityLevel.LOW,
                line_range="5",
                owasp_category="A09:2021-Logging",
                explanation="Verbose debug logging enabled",
                suggested_fix="logger.setLevel(logging.INFO)",
                confidence=0.50,
                file_path="src/log.py",
            ),
        ]

        results = engine.process_findings(
            owner="octocat",
            repo="demo-repo",
            original_pr_number=10,
            base_branch="main",
            head_sha="sha999",
            findings=findings,
            repo_id="octocat_demo-repo",
            author_id="dev-alice",
        )

        assert len(results) == 2
        assert results[0].action == "remediation_pr"
        assert results[1].action == "suggestion_comment"

        # Check habits recorded in memory
        habits = fb.get_author_habits("octocat_demo-repo", "dev-alice")
        assert len(habits) == 2

        # Check audit log recorded
        logs = fb.get_audit_logs("octocat_demo-repo")
        assert len(logs) == 2


class TestBuildFindingsComment:
    def test_comment_formatting(self, engine: RemediationEngine):
        finding = SecurityFinding(
            severity=SeverityLevel.HIGH,
            line_range="15-20",
            owasp_category="A03:2021-Injection",
            explanation="Unsanitized user input in query",
            suggested_fix="safe_query()",
            confidence=0.95,
            file_path="app.py",
        )
        rem_res = engine.create_remediation_pr(
            owner="o", repo="r", original_pr_number=1, base_branch="main", head_sha="sha", finding=finding
        )
        comment = engine.build_findings_comment(
            findings=[finding],
            remediation_results=[rem_res],
            memory_annotations=["🔁 Recurring pattern — 2nd time"],
        )

        assert "GitSentry Security Audit Results" in comment
        assert "A03:2021-Injection" in comment
        assert "Auto-remediation PR opened" in comment
        assert "Recurring pattern" in comment
        assert "never merges code" in comment
