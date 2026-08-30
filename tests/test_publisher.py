"""Unit tests for Pub/Sub Event Publisher."""

import json
from unittest.mock import MagicMock
import pytest

from common.config import Settings
from common.models import (
    EventType,
    GitHubPullRequest,
    GitHubRepository,
    GitHubUser,
    NormalizedGitHubEvent,
)
from common.publisher import EventPublisher


def test_publisher_mock_mode():
    settings = Settings(
        ENVIRONMENT="test",
        GCP_PROJECT_ID="test-proj",
        PUBSUB_TOPIC_PR_EVENTS="pr-events-test",
    )
    publisher = EventPublisher(settings=settings)
    publisher.reset_mock_history()

    repo = GitHubRepository(id=101, name="web-app", full_name="org/web-app")
    sender = GitHubUser(id=202, login="developer-dan")
    pr = GitHubPullRequest(id=303, number=15, title="Update dependencies")

    event = NormalizedGitHubEvent(
        event_id="delivery-abc-123",
        event_type=EventType.PULL_REQUEST,
        action="synchronize",
        repository=repo,
        sender=sender,
        pull_request=pr,
        issue_number=15,
        is_pull_request=True,
    )

    msg_id = publisher.publish_event(event)
    assert msg_id == "mock-msg-delivery-abc-123"
    assert len(publisher.published_events) == 1

    entry = publisher.published_events[0]
    assert entry["attributes"]["event_type"] == "pull_request"
    assert entry["attributes"]["action"] == "synchronize"
    assert entry["attributes"]["repo"] == "org/web-app"
    assert entry["attributes"]["delivery_id"] == "delivery-abc-123"
    assert entry["attributes"]["is_pull_request"] == "true"


def test_publisher_live_gcp_client():
    settings = Settings(
        ENVIRONMENT="production",
        GCP_PROJECT_ID="prod-proj",
        PUBSUB_TOPIC_PR_EVENTS="pr-events-prod",
    )
    publisher = EventPublisher(settings=settings)

    mock_client = MagicMock()
    mock_future = MagicMock()
    mock_future.result.return_value = "pubsub-msg-999888777"
    mock_client.publish.return_value = mock_future

    publisher._client = mock_client
    publisher._initialized = True

    repo = GitHubRepository(id=1, name="core", full_name="acme/core")
    sender = GitHubUser(id=2, login="user1")

    event = NormalizedGitHubEvent(
        event_id="deliv-777",
        event_type=EventType.PULL_REQUEST,
        action="opened",
        repository=repo,
        sender=sender,
        is_pull_request=True,
    )

    result = publisher.publish_event(event)
    assert result == "pubsub-msg-999888777"
    assert mock_client.publish.call_count == 1
