"""Unit tests for GitHub API client (mock mode)."""

import pytest
from common.config import Settings
from common.github_client import GitHubClient


@pytest.fixture
def settings() -> Settings:
    return Settings(ENVIRONMENT="test", USE_SECRET_MANAGER=False)


@pytest.fixture
def gh(settings) -> GitHubClient:
    client = GitHubClient(settings=settings)
    client.reset_mock()
    return client


class TestPRComments:
    def test_post_comment(self, gh: GitHubClient):
        result = gh.post_pr_comment("octocat", "repo", 42, "Hello from GitSentry!")
        assert result["id"] == 1000
        assert result["body"] == "Hello from GitSentry!"
        assert "42" in result["html_url"]
        assert len(gh.posted_comments) == 1
        assert len(gh.api_calls) == 1

    def test_post_multiple_comments(self, gh: GitHubClient):
        gh.post_pr_comment("o", "r", 1, "Comment 1")
        gh.post_pr_comment("o", "r", 1, "Comment 2")
        gh.post_pr_comment("o", "r", 2, "Comment on PR 2")
        assert len(gh.posted_comments) == 3

    def test_get_comments(self, gh: GitHubClient):
        gh.post_pr_comment("o", "r", 1, "First")
        gh.post_pr_comment("o", "r", 1, "Second")
        gh.post_pr_comment("o", "r", 2, "Other PR")

        comments = gh.get_pr_comments("o", "r", 1)
        assert len(comments) == 2
        assert comments[0]["body"] == "First"
        assert comments[1]["body"] == "Second"


class TestCommitStatus:
    def test_set_pending_status(self, gh: GitHubClient):
        result = gh.set_commit_status("o", "r", "abc123", "pending", "Audit in progress")
        assert result["state"] == "pending"
        assert result["context"] == "gitsentry/security"
        assert len(gh.set_statuses) == 1

    def test_set_failure_status(self, gh: GitHubClient):
        result = gh.set_commit_status("o", "r", "abc123", "failure", "2 findings")
        assert result["state"] == "failure"

    def test_set_success_status(self, gh: GitHubClient):
        result = gh.set_commit_status("o", "r", "abc123", "success", "All clear")
        assert result["state"] == "success"

    def test_description_truncated(self, gh: GitHubClient):
        long_desc = "A" * 200
        result = gh.set_commit_status("o", "r", "abc", "pending", long_desc)
        assert len(result["description"]) <= 140


class TestBranchCreation:
    def test_create_branch(self, gh: GitHubClient):
        result = gh.create_branch("o", "r", "gitsentry/fix-abc12345", "sha123")
        assert result["ref"] == "refs/heads/gitsentry/fix-abc12345"
        assert result["object"]["sha"] == "sha123"
        assert len(gh.created_branches) == 1

    def test_commit_file(self, gh: GitHubClient):
        result = gh.commit_file("o", "r", "fix-branch", "src/app.py", "print('fixed')", "fix: patch")
        assert result["content"]["path"] == "src/app.py"
        assert result["commit"]["message"] == "fix: patch"


class TestPullRequestCreation:
    def test_open_pull_request(self, gh: GitHubClient):
        result = gh.open_pull_request(
            "o", "r",
            title="Fix SQL injection",
            body="Auto-fix by GitSentry",
            head_branch="gitsentry/fix-abc",
            base_branch="main",
        )
        assert result["number"] == 100
        assert result["title"] == "Fix SQL injection"
        assert result["state"] == "open"
        assert len(gh.created_prs) == 1

    def test_open_multiple_prs(self, gh: GitHubClient):
        gh.open_pull_request("o", "r", "PR 1", "Body 1", "fix-1", "main")
        gh.open_pull_request("o", "r", "PR 2", "Body 2", "fix-2", "main")
        assert len(gh.created_prs) == 2
        assert gh.created_prs[0]["result"]["number"] == 100
        assert gh.created_prs[1]["result"]["number"] == 101


class TestMockReset:
    def test_reset_clears_all(self, gh: GitHubClient):
        gh.post_pr_comment("o", "r", 1, "test")
        gh.set_commit_status("o", "r", "sha", "pending")
        gh.create_branch("o", "r", "b", "sha")
        gh.open_pull_request("o", "r", "t", "b", "h", "m")

        assert len(gh.api_calls) == 4
        gh.reset_mock()
        assert len(gh.api_calls) == 0
        assert len(gh.posted_comments) == 0
        assert len(gh.set_statuses) == 0
        assert len(gh.created_branches) == 0
        assert len(gh.created_prs) == 0
