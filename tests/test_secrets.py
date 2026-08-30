"""Unit tests for Secret Manager client and caching logic."""

import time
from unittest.mock import MagicMock, patch
import pytest

from common.config import Settings
from common.secrets import SecretCacheEntry, SecretManagerClient


def test_secret_cache_entry_expiration():
    now = time.time()
    valid_entry = SecretCacheEntry(value="secret123", expires_at=now + 100)
    assert valid_entry.is_expired() is False

    expired_entry = SecretCacheEntry(value="secret123", expires_at=now - 10)
    assert expired_entry.is_expired() is True


def test_secret_manager_fallback_to_settings():
    settings = Settings(
        ENVIRONMENT="test",
        USE_SECRET_MANAGER=False,
        GITHUB_WEBHOOK_SECRET="local_webhook_secret",
        GITHUB_APP_PRIVATE_KEY="local_private_key",
        GEMINI_API_KEY="local_gemini_key",
    )
    client = SecretManagerClient(settings=settings)

    assert client.get_webhook_secret() == "local_webhook_secret"
    assert client.get_app_private_key() == "local_private_key"
    assert client.get_gemini_api_key() == "local_gemini_key"


def test_secret_manager_caching(monkeypatch):
    settings = Settings(
        ENVIRONMENT="test",
        USE_SECRET_MANAGER=True,
        GCP_PROJECT_ID="test-project",
    )
    client = SecretManagerClient(settings=settings, cache_ttl_seconds=60)

    # Mock the GCP Secret Manager SDK client
    mock_gcp_client = MagicMock()
    mock_response = MagicMock()
    mock_response.payload.data = b"secret_from_gcp_api"
    mock_gcp_client.access_secret_version.return_value = mock_response

    client._client = mock_gcp_client
    client._initialized_client = True

    # First fetch: should call API
    val1 = client.get_secret("my-secret")
    assert val1 == "secret_from_gcp_api"
    assert mock_gcp_client.access_secret_version.call_count == 1

    # Second fetch: should hit cache
    val2 = client.get_secret("my-secret")
    assert val2 == "secret_from_gcp_api"
    assert mock_gcp_client.access_secret_version.call_count == 1  # Still 1, did not call again

    # Clear cache and fetch again
    client.clear_cache()
    val3 = client.get_secret("my-secret")
    assert val3 == "secret_from_gcp_api"
    assert mock_gcp_client.access_secret_version.call_count == 2
