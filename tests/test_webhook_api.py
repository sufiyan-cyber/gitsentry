"""Integration tests for GitSentry Webhook Receiver API endpoints."""

import json
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from common.crypto import generate_github_signature
from tests.conftest import TEST_SECRET


def test_root_endpoint(test_client: TestClient):
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["service"] == "GitSentry Webhook Receiver"
    assert data["version"] == "0.1.0"


def test_healthz_endpoint(test_client: TestClient):
    response = test_client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readyz_endpoint(test_client: TestClient):
    response = test_client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["secret_configured"] is True


def test_webhook_ping_event(test_client: TestClient):
    payload = {
        "zen": "Encourage flow.",
        "hook_id": 987654,
        "repository": {"id": 1, "name": "repo", "full_name": "org/repo"},
        "sender": {"id": 2, "login": "octocat"},
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = generate_github_signature(payload_bytes, TEST_SECRET)

    response = test_client.post(
        "/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "delivery-ping-001",
            "X-Hub-Signature-256": sig,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["event"] == "ping"
    assert data["zen"] == "Encourage flow."


def test_webhook_pull_request_opened(test_client: TestClient, sample_pr_payload: dict):
    payload_bytes = json.dumps(sample_pr_payload).encode("utf-8")
    sig = generate_github_signature(payload_bytes, TEST_SECRET)

    response = test_client.post(
        "/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-pr-opened-001",
            "X-Hub-Signature-256": sig,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["event_type"] == "pull_request"
    assert data["action"] == "opened"
    assert data["pr_number"] == 10
    assert data["repository"] == "octocat/demo-repo"
    assert data["published"] is True
    assert "mock-msg-delivery-pr-opened-001" in data["message_id"]


def test_webhook_pull_request_synchronize(test_client: TestClient, sample_pr_payload: dict):
    sample_pr_payload["action"] = "synchronize"
    payload_bytes = json.dumps(sample_pr_payload).encode("utf-8")
    sig = generate_github_signature(payload_bytes, TEST_SECRET)

    response = test_client.post(
        "/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-pr-sync-002",
            "X-Hub-Signature-256": sig,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["action"] == "synchronize"


def test_webhook_issue_comment_on_pr(test_client: TestClient, sample_comment_payload: dict):
    payload_bytes = json.dumps(sample_comment_payload).encode("utf-8")
    sig = generate_github_signature(payload_bytes, TEST_SECRET)

    response = test_client.post(
        "/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "issue_comment",
            "X-GitHub-Delivery": "delivery-comment-003",
            "X-Hub-Signature-256": sig,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert data["event_type"] == "issue_comment"
    assert data["pr_number"] == 10
    assert data["published"] is True


def test_webhook_issue_comment_on_regular_issue(test_client: TestClient, sample_comment_payload: dict):
    # Remove pull_request key from issue object to simulate a standard issue
    del sample_comment_payload["issue"]["pull_request"]

    payload_bytes = json.dumps(sample_comment_payload).encode("utf-8")
    sig = generate_github_signature(payload_bytes, TEST_SECRET)

    response = test_client.post(
        "/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "issue_comment",
            "X-GitHub-Delivery": "delivery-comment-issue-004",
            "X-Hub-Signature-256": sig,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
    assert "not a Pull Request" in data["reason"]


def test_webhook_missing_signature_returns_401(test_client: TestClient, sample_pr_payload: dict):
    payload_bytes = json.dumps(sample_pr_payload).encode("utf-8")

    response = test_client.post(
        "/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-unsigned-005",
        },
    )

    assert response.status_code == 401
    assert "Invalid or missing HMAC signature" in response.json()["detail"]


def test_webhook_invalid_signature_returns_401(test_client: TestClient, sample_pr_payload: dict):
    payload_bytes = json.dumps(sample_pr_payload).encode("utf-8")
    tampered_sig = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

    response = test_client.post(
        "/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "delivery-tampered-006",
            "X-Hub-Signature-256": tampered_sig,
        },
    )

    assert response.status_code == 401
    assert "Invalid or missing HMAC signature" in response.json()["detail"]


def test_webhook_missing_event_header_returns_400(test_client: TestClient, sample_pr_payload: dict):
    payload_bytes = json.dumps(sample_pr_payload).encode("utf-8")
    sig = generate_github_signature(payload_bytes, TEST_SECRET)

    response = test_client.post(
        "/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Delivery": "delivery-no-event-007",
            "X-Hub-Signature-256": sig,
        },
    )

    assert response.status_code == 400
    assert "Missing X-GitHub-Event" in response.json()["detail"]


def test_webhook_unhandled_event_type_ignored(test_client: TestClient):
    payload = {
        "action": "created",
        "repository": {"id": 1, "name": "repo", "full_name": "org/repo"},
        "sender": {"id": 2, "login": "star-user"},
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = generate_github_signature(payload_bytes, TEST_SECRET)

    response = test_client.post(
        "/webhook",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "star",
            "X-GitHub-Delivery": "delivery-star-008",
            "X-Hub-Signature-256": sig,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
    assert "star" in data["reason"]


def test_dashboard_page(test_client: TestClient):
    response = test_client.get("/dashboard")
    assert response.status_code == 200
    assert "GitSentry" in response.text
    assert "Memory Bank" in response.text


def test_dashboard_api_endpoints(test_client: TestClient):
    # Test memory status endpoint
    res_mem = test_client.get("/api/dashboard/memory")
    assert res_mem.status_code == 200
    assert "decisions" in res_mem.json()

    # Test run beat endpoint
    res_beat = test_client.post("/api/dashboard/run-beat?beat=1")
    assert res_beat.status_code == 200
    assert "BEAT 1" in res_beat.json()["log"]

    # Test reset endpoint
    res_reset = test_client.post("/api/dashboard/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["status"] == "ok"

