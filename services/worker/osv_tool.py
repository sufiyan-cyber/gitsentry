"""OSV.dev Vulnerability RAG Tool for GitSentry.

Queries the Google-incubated OSV.dev Open Source Vulnerabilities API
(https://api.osv.dev/v1/query) for known CVEs and GHSA advisories against
packages and versions extracted from PR diffs (requirements.txt, package.json, etc.).
"""

import logging
import re
from typing import Any, Dict, List, Optional
import httpx

from common.models import SecurityFinding, SeverityLevel

logger = logging.getLogger(__name__)

OSV_QUERY_ENDPOINT = "https://api.osv.dev/v1/query"


class PackageDependency:
    """Represents a single package and version extracted from manifest changes."""
    def __init__(self, name: str, version: str, ecosystem: str = "PyPI", file_path: str = "requirements.txt"):
        self.name = name
        self.version = version
        self.ecosystem = ecosystem
        self.file_path = file_path


class OSVTool:
    """Tool for querying known CVEs against dependencies via OSV.dev."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self._mock_vulnerabilities: Dict[str, List[Dict[str, Any]]] = {}

    def extract_dependencies_from_diff(self, diff_text: str) -> List[PackageDependency]:
        """Parses added/updated dependencies from diffs of requirements.txt or package.json."""
        dependencies: List[PackageDependency] = []

        # Parse requirements.txt additions: e.g. +requests==2.25.1 or +flask>=1.1.2
        for line in diff_text.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                raw_line = line[1:].strip()
                # Match pip format: name==version
                match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*==\s*([a-zA-Z0-9_\-\.]+)", raw_line)
                if match:
                    pkg_name, version = match.groups()
                    dependencies.append(PackageDependency(
                        name=pkg_name,
                        version=version,
                        ecosystem="PyPI",
                        file_path="requirements.txt",
                    ))
                # Match npm format in package.json: "name": "1.2.3"
                npm_match = re.match(r'^"([a-zA-Z0-9_\-\./@]+)"\s*:\s*"[\^~]?([0-9\.]+)"', raw_line)
                if npm_match:
                    pkg_name, version = npm_match.groups()
                    dependencies.append(PackageDependency(
                        name=pkg_name,
                        version=version,
                        ecosystem="npm",
                        file_path="package.json",
                    ))

        return dependencies

    def query_vulnerabilities(self, dep: PackageDependency) -> List[Dict[str, Any]]:
        """Queries OSV.dev API for a specific package and version."""
        # Check mock data first
        mock_key = f"{dep.ecosystem}:{dep.name}:{dep.version}"
        if mock_key in self._mock_vulnerabilities:
            return self._mock_vulnerabilities[mock_key]

        payload = {
            "version": dep.version,
            "package": {
                "name": dep.name,
                "ecosystem": dep.ecosystem,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(OSV_QUERY_ENDPOINT, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    vulns = data.get("vulns", [])
                    logger.info("OSV.dev returned %d vulnerability entries for %s==%s", len(vulns), dep.name, dep.version)
                    return vulns
                else:
                    logger.warning("OSV.dev query returned status %d for %s", resp.status_code, dep.name)
                    return []
        except Exception as e:
            logger.warning("OSV.dev API lookup failed for %s==%s: %s", dep.name, dep.version, e)
            return []

    def check_diff_for_vulnerabilities(self, diff_text: str) -> List[SecurityFinding]:
        """Extracts dependencies from diff, queries OSV.dev, and returns SecurityFindings."""
        deps = self.extract_dependencies_from_diff(diff_text)
        findings: List[SecurityFinding] = []

        for dep in deps:
            vulns = self.query_vulnerabilities(dep)
            for v in vulns:
                vuln_id = v.get("id", "UNKNOWN-CVE")
                summary = v.get("summary", "Known vulnerability in dependency")
                details = v.get("details", summary)

                finding = SecurityFinding(
                    severity=SeverityLevel.HIGH,
                    line_range="1",
                    owasp_category=f"A06:2021-Vulnerable and Outdated Components ({vuln_id})",
                    explanation=f"Dependency '{dep.name}=={dep.version}' has a known vulnerability ({vuln_id}): {summary}",
                    suggested_fix=f"Upgrade '{dep.name}' to a patched version resolving {vuln_id}.",
                    confidence=0.98,
                    file_path=dep.file_path,
                )
                findings.append(finding)

        return findings

    def set_mock_vulnerability(self, ecosystem: str, name: str, version: str, vulns: List[Dict[str, Any]]):
        """Helper to inject mock OSV responses for testing."""
        self._mock_vulnerabilities[f"{ecosystem}:{name}:{version}"] = vulns

    def clear_mock(self):
        self._mock_vulnerabilities.clear()


_osv_tool_instance: Optional[OSVTool] = None


def get_osv_tool() -> OSVTool:
    global _osv_tool_instance
    if _osv_tool_instance is None:
        _osv_tool_instance = OSVTool()
    return _osv_tool_instance
