"""Pytest configuration, fixtures, and mocks for GitSentry tests."""

import os
import pytest
from fastapi.testclient import TestClient

from common.config import Settings, get_settings
from common.publisher import EventPublisher, get_event_publisher
from common.secrets import SecretManagerClient, get_secret_manager
from services.receiver.app import create_app

TEST_SECRET = "test_webhook_secret_value_xyz123"
TEST_PROJECT_ID = "test-gitsentry-project"
TEST_TOPIC = "pr-events-test"


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Sets environment variables for testing."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("GCP_PROJECT_ID", TEST_PROJECT_ID)
    monkeypatch.setenv("PUBSUB_TOPIC_PR_EVENTS", TEST_TOPIC)
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", TEST_SECRET)
    monkeypatch.setenv("GITHUB_APP_PRIVATE_KEY", "mock-rsa-private-key-test")
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-api-key-test")
    monkeypatch.setenv("USE_SECRET_MANAGER", "false")


@pytest.fixture
def test_settings() -> Settings:
    """Returns test settings instance."""
    return Settings(
        ENVIRONMENT="test",
        GCP_PROJECT_ID=TEST_PROJECT_ID,
        PUBSUB_TOPIC_PR_EVENTS=TEST_TOPIC,
        GITHUB_WEBHOOK_SECRET=TEST_SECRET,
        GITHUB_APP_PRIVATE_KEY="mock-rsa-private-key-test",
        GEMINI_API_KEY="mock-gemini-api-key-test",
        USE_SECRET_MANAGER=False,
    )


@pytest.fixture
def test_secret_manager(test_settings) -> SecretManagerClient:
    """Returns SecretManagerClient configured for testing."""
    client = SecretManagerClient(settings=test_settings)
    client.clear_cache()
    return client


@pytest.fixture
def test_publisher(test_settings) -> EventPublisher:
    """Returns EventPublisher configured for testing."""
    pub = EventPublisher(settings=test_settings)
    pub.reset_mock_history()
    return pub


@pytest.fixture
def test_client(test_settings, test_secret_manager, test_publisher) -> TestClient:
    """Returns FastAPI TestClient with overridden dependencies."""
    app = create_app()

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_secret_manager] = lambda: test_secret_manager
    app.dependency_overrides[get_event_publisher] = lambda: test_publisher

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_pr_payload() -> dict:
    """Sample GitHub pull_request.opened payload."""
    return {
        "action": "opened",
        "number": 10,
        "pull_request": {
            "id": 50010,
            "number": 10,
            "state": "open",
            "title": "Fix SQL injection in user authentication route",
            "body": "Replaces string format query with parameterized statements.",
            "user": {
                "login": "octocat-dev",
                "id": 12345,
                "type": "User",
            },
            "head": {
                "sha": "11223344556677889900aabbccddeeff11223344",
                "ref": "fix/sql-injection",
            },
            "base": {
                "sha": "99887766554433221100ffeeddccbbaa99887766",
                "ref": "main",
            },
            "diff_url": "https://github.com/octocat/demo-repo/pull/10.diff",
            "html_url": "https://github.com/octocat/demo-repo/pull/10",
            "created_at": "2026-08-28T12:00:00Z",
            "updated_at": "2026-08-28T12:00:00Z",
        },
        "repository": {
            "id": 999999,
            "name": "demo-repo",
            "full_name": "octocat/demo-repo",
            "private": False,
            "owner": {"login": "octocat", "id": 100},
        },
        "sender": {
            "login": "octocat-dev",
            "id": 12345,
            "type": "User",
        },
        "installation": {
            "id": 888777,
        },
    }


@pytest.fixture
def sample_comment_payload() -> dict:
    """Sample GitHub issue_comment.created payload on a PR."""
    return {
        "action": "created",
        "issue": {
            "number": 10,
            "id": 50010,
            "title": "Fix SQL injection in user authentication route",
            "pull_request": {
                "url": "https://api.github.com/repos/octocat/demo-repo/pulls/10",
                "html_url": "https://github.com/octocat/demo-repo/pull/10",
            },
            "user": {"login": "octocat-dev", "id": 12345},
        },
        "comment": {
            "id": 654321,
            "body": "@gitsentry This is approved as an exception for staging test environment per policy SEC-99.",
            "user": {"login": "octocat-dev", "id": 12345},
            "html_url": "https://github.com/octocat/demo-repo/pull/10#issuecomment-654321",
            "created_at": "2026-08-28T12:05:00Z",
            "updated_at": "2026-08-28T12:05:00Z",
        },
        "repository": {
            "id": 999999,
            "name": "demo-repo",
            "full_name": "octocat/demo-repo",
            "private": False,
            "owner": {"login": "octocat", "id": 100},
        },
        "sender": {
            "login": "octocat-dev",
            "id": 12345,
            "type": "User",
        },
        "installation": {
            "id": 888777,
        },
    }
