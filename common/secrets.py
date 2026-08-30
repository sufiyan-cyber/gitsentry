"""Google Secret Manager client with local environment fallback and TTL caching."""

import logging
import os
import time
from typing import Dict, Optional, Tuple

from common.config import Settings, get_settings

logger = logging.getLogger(__name__)


class SecretCacheEntry:
    def __init__(self, value: str, expires_at: float):
        self.value = value
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class SecretManagerClient:
    """Manages retrieving secrets from Google Cloud Secret Manager with local fallbacks."""

    def __init__(self, settings: Optional[Settings] = None, cache_ttl_seconds: int = 300):
        self.settings = settings or get_settings()
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, SecretCacheEntry] = {}
        self._client = None
        self._initialized_client = False

    def _get_client(self):
        """Lazy-initializes Google Secret Manager client."""
        if not self._initialized_client:
            self._initialized_client = True
            try:
                from google.cloud import secretmanager
                self._client = secretmanager.SecretManagerServiceClient()
                logger.info("Initialized Google Secret Manager client")
            except Exception as e:
                logger.warning(
                    "Could not initialize Google Secret Manager client: %s. "
                    "Falling back to environment variables.", e
                )
                self._client = None
        return self._client

    def get_secret(
        self,
        secret_id: str,
        version: str = "latest",
        fallback_value: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Optional[str]:
        """Fetches secret value from cache, Secret Manager, or fallback value/env.
        
        Args:
            secret_id: The Secret Manager secret ID or resource name.
            version: The secret version (defaults to 'latest').
            fallback_value: Direct fallback value if Secret Manager is not available.
            project_id: GCP Project ID override.
            
        Returns:
            The secret string payload, or None if not found.
        """
        cache_key = f"{project_id or self.settings.GCP_PROJECT_ID}/{secret_id}/{version}"
        
        # Check cache
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired():
                return entry.value

        # Direct fallback check if configured not to use Secret Manager
        if not self.settings.should_use_secret_manager and fallback_value:
            return fallback_value

        # Attempt to fetch from Secret Manager
        client = self._get_client()
        if client:
            proj = project_id or self.settings.GCP_PROJECT_ID
            # Build resource name if not already formatted
            if "/" in secret_id:
                name = secret_id
            else:
                name = f"projects/{proj}/secrets/{secret_id}/versions/{version}"

            try:
                response = client.access_secret_version(request={"name": name})
                secret_payload = response.payload.data.decode("UTF-8")
                self._cache[cache_key] = SecretCacheEntry(
                    value=secret_payload,
                    expires_at=time.time() + self.cache_ttl_seconds,
                )
                logger.debug("Successfully accessed secret '%s' from Secret Manager", secret_id)
                return secret_payload
            except Exception as e:
                logger.warning(
                    "Failed to fetch secret '%s' from Secret Manager (%s). Using fallback if available.",
                    name, e
                )

        # Fallback to local value or env var
        if fallback_value:
            return fallback_value

        env_var_name = secret_id.upper().replace("-", "_")
        env_val = os.getenv(env_var_name)
        if env_val:
            return env_val

        return None

    def get_webhook_secret(self) -> str:
        """Convenience method to resolve GitHub webhook secret."""
        val = self.get_secret(
            secret_id=self.settings.GITHUB_WEBHOOK_SECRET_NAME,
            fallback_value=self.settings.GITHUB_WEBHOOK_SECRET,
        )
        if not val:
            logger.warning("GITHUB_WEBHOOK_SECRET is not resolved!")
            return ""
        return val

    def get_app_private_key(self) -> str:
        """Convenience method to resolve GitHub App Private Key."""
        val = self.get_secret(
            secret_id=self.settings.GITHUB_APP_PRIVATE_KEY_NAME,
            fallback_value=self.settings.GITHUB_APP_PRIVATE_KEY,
        )
        if not val:
            logger.warning("GITHUB_APP_PRIVATE_KEY is not resolved!")
            return ""
        return val

    def get_gemini_api_key(self) -> str:
        """Convenience method to resolve Gemini API Key."""
        val = self.get_secret(
            secret_id=self.settings.GEMINI_API_KEY_NAME,
            fallback_value=self.settings.GEMINI_API_KEY,
        )
        if not val:
            logger.warning("GEMINI_API_KEY is not resolved!")
            return ""
        return val

    def clear_cache(self):
        """Clears all cached secrets."""
        self._cache.clear()


# Default singleton instance
_secret_manager_instance: Optional[SecretManagerClient] = None


def get_secret_manager(settings: Optional[Settings] = None) -> SecretManagerClient:
    """Returns or creates the singleton SecretManagerClient."""
    global _secret_manager_instance
    if _secret_manager_instance is None:
        _secret_manager_instance = SecretManagerClient(settings=settings)
    return _secret_manager_instance
