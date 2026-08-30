"""Unit tests for GeminiSecurityAnalyzer and OSV.dev RAG tool."""

import pytest
from common.config import Settings
from common.models import MemoryContext, SeverityLevel
from services.worker.analyzer import GeminiSecurityAnalyzer
from services.worker.osv_tool import OSVTool, PackageDependency


@pytest.fixture
def settings() -> Settings:
    return Settings(
        ENVIRONMENT="test",
        USE_SECRET_MANAGER=False,
        GEMINI_MODEL="gemini-3.7-flash",
    )


@pytest.fixture
def osv_tool() -> OSVTool:
    tool = OSVTool()
    tool.clear_mock()
    return tool


@pytest.fixture
def analyzer(settings, osv_tool) -> GeminiSecurityAnalyzer:
    return GeminiSecurityAnalyzer(settings=settings, osv_tool=osv_tool)


class TestOSVTool:
    def test_extract_dependencies_from_diff(self, osv_tool: OSVTool):
        diff_text = """
diff --git a/requirements.txt b/requirements.txt
--- a/requirements.txt
+++ b/requirements.txt
@@ -1,2 +1,3 @@
-requests==2.20.0
+requests==2.31.0
+flask==2.0.1
diff --git a/package.json b/package.json
+++ b/package.json
@@ -10,3 +10,4 @@
+    "axios": "0.21.1",
"""
        deps = osv_tool.extract_dependencies_from_diff(diff_text)
        assert len(deps) == 3
        assert deps[0].name == "requests"
        assert deps[0].version == "2.31.0"
        assert deps[0].ecosystem == "PyPI"
        assert deps[1].name == "flask"
        assert deps[1].version == "2.0.1"
        assert deps[2].name == "axios"
        assert deps[2].version == "0.21.1"
        assert deps[2].ecosystem == "npm"

    def test_check_diff_for_vulnerabilities_with_mock(self, osv_tool: OSVTool):
        osv_tool.set_mock_vulnerability(
            ecosystem="PyPI",
            name="urllib3",
            version="1.26.4",
            vulns=[{
                "id": "GHSA-1234-abcd",
                "summary": "Cookie header injection vulnerability in urllib3",
            }],
        )

        diff = "+urllib3==1.26.4"
        findings = osv_tool.check_diff_for_vulnerabilities(diff)

        assert len(findings) == 1
        assert findings[0].severity == SeverityLevel.HIGH
        assert "GHSA-1234-abcd" in findings[0].owasp_category
        assert "urllib3==1.26.4" in findings[0].explanation


class TestGeminiSecurityAnalyzer:
    def test_triage_diff_detects_security_concerns(self, analyzer: GeminiSecurityAnalyzer):
        diff_with_auth = """
+@app.route('/login')
+def login():
+    user = request.form['user']
+    pw = request.form['password']
"""
        result = analyzer.triage_diff(diff_with_auth, pr_title="Add user login route")
        assert result.has_security_concerns is True
        assert len(result.flagged_categories) > 0

    def test_triage_diff_clean_change(self, analyzer: GeminiSecurityAnalyzer):
        clean_diff = """
+def add_numbers(a: int, b: int) -> int:
+    return a + b
"""
        result = analyzer.triage_diff(clean_diff, pr_title="Add math helper")
        assert result.has_security_concerns is False

    def test_deep_audit_detects_sql_injection(self, analyzer: GeminiSecurityAnalyzer):
        sql_diff = """
+def get_user_data(user_id):
+    query = f"SELECT * FROM users WHERE id = {user_id}"
+    return db.execute(query)
"""
        ctx = MemoryContext(repo_id="test_repo", author_id="dev-alice")
        result = analyzer.deep_audit(sql_diff, memory_context=ctx, pr_title="User lookup", pr_number=10)

        assert len(result.findings) >= 1
        sql_findings = [f for f in result.findings if "A03" in f.owasp_category or "Injection" in f.owasp_category]
        assert len(sql_findings) > 0
        assert sql_findings[0].severity == SeverityLevel.HIGH

    def test_deep_audit_detects_unauthenticated_route(self, analyzer: GeminiSecurityAnalyzer):
        route_diff = """
+@app.get('/health')
+def staging_health():
+    return {"status": "unauthenticated"}
"""
        ctx = MemoryContext(repo_id="test_repo", author_id="dev-alice")
        result = analyzer.deep_audit(route_diff, memory_context=ctx, pr_title="Add health check", pr_number=1)

        assert len(result.findings) >= 1
        auth_findings = [f for f in result.findings if "A01" in f.owasp_category or "Access Control" in f.owasp_category]
        assert len(auth_findings) > 0
