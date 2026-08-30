"""Pub/Sub event publisher for decoupled webhook ingestion."""

import json
import logging
from typing import Any, Dict, List, Optional

from common.config import Settings, get_settings
from common.models import NormalizedGitHubEvent

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes normalized GitHub events to GCP Pub/Sub topic."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.topic_path = f"projects/{self.settings.GCP_PROJECT_ID}/topics/{self.settings.PUBSUB_TOPIC_PR_EVENTS}"
        self._client = None
        self._initialized = False
        # For testing / local development inspection
        self.published_events: List[Dict[str, Any]] = []

    def _get_client(self):
        """Initializes Google Pub/Sub PublisherClient."""
        if not self._initialized:
            self._initialized = True
            if self.settings.is_test or not self.settings.is_production:
                # In test or dev without GCP credentials, we can run in mock/local mode
                try:
                    from google.cloud import pubsub_v1
                    self._client = pubsub_v1.PublisherClient()
                    logger.info("Initialized Google Cloud Pub/Sub publisher for topic %s", self.topic_path)
                except Exception as e:
                    logger.warning(
                        "Google Cloud Pub/Sub client not initialized (%s). Operating in mock/local mode.",
                        e
                    )
                    self._client = None
            else:
                from google.cloud import pubsub_v1
                self._client = pubsub_v1.PublisherClient()
                logger.info("Initialized Google Cloud Pub/Sub publisher for topic %s", self.topic_path)
        return self._client

    def publish_event(self, event: NormalizedGitHubEvent) -> str:
        """Publishes a NormalizedGitHubEvent to Pub/Sub.
        
        Args:
            event: Normalized GitHub event model.
            
        Returns:
            Message ID or mock acknowledgment string.
        """
        payload_dict = json.loads(event.model_dump_json())
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        
        attributes = {
            "event_type": str(event.event_type.value),
            "action": str(event.action),
            "repo": str(event.repository.full_name),
            "delivery_id": str(event.event_id),
            "is_pull_request": str(event.is_pull_request).lower(),
        }

        # Keep record in local memory for audit & testing
        self.published_events.append({
            "event": payload_dict,
            "attributes": attributes,
            "topic": self.topic_path,
        })

        client = self._get_client()
        if client:
            try:
                future = client.publish(
                    self.topic_path,
                    data=payload_bytes,
                    **attributes
                )
                message_id = future.result(timeout=10.0)
                logger.info(
                    "Published event %s (%s) to %s - Message ID: %s",
                    event.event_id, event.event_type.value, self.topic_path, message_id
                )
                return message_id
            except Exception as e:
                logger.error(
                    "Failed to publish event %s to Pub/Sub: %s",
                    event.event_id, e
                )
                raise
        else:
            mock_id = f"mock-msg-{event.event_id}"
            logger.info(
                "[Mock/Local Publisher] Recorded event %s (%s) for topic %s",
                event.event_id, event.event_type.value, self.topic_path
            )
            return mock_id

    def reset_mock_history(self):
        """Clears test publication history."""
        self.published_events.clear()


# Default singleton instance
_publisher_instance: Optional[EventPublisher] = None


def get_event_publisher(settings: Optional[Settings] = None) -> EventPublisher:
    """Returns or creates the singleton EventPublisher."""
    global _publisher_instance
    if _publisher_instance is None:
        _publisher_instance = EventPublisher(settings=settings)
    return _publisher_instance
