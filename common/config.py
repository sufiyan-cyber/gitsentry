"""Configuration management for GitSentry services using Pydantic Settings."""

from functools import lru_cache
from typing import Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Environment
    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Google Cloud Platform
    GCP_PROJECT_ID: str = "gitsentry-dev"
    PUBSUB_TOPIC_PR_EVENTS: str = "pr-events"
    PUBSUB_EMULATOR_HOST: Optional[str] = None
    FIRESTORE_DATABASE: str = "(default)"

    # Google Secret Manager Secret IDs
    GITHUB_WEBHOOK_SECRET_NAME: str = "github-webhook-secret"
    GITHUB_APP_PRIVATE_KEY_NAME: str = "github-app-private-key"
    GEMINI_API_KEY_NAME: str = "gemini-api-key"

    # Direct Environment Overrides (used for local testing / development when Secret Manager is not attached)
    GITHUB_WEBHOOK_SECRET: Optional[str] = None
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_APP_PRIVATE_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # AI Model
    GEMINI_MODEL: str = "gemini-3.7-flash"

    # Firestore Memory Bank (Phase 3)
    FIRESTORE_EMULATOR_HOST: Optional[str] = None
    MEMORY_COMPACTION_THRESHOLD: int = 20  # Compact when raw docs exceed this count
    MEMORY_BRIEF_MAX_TOKENS: int = 2000  # Max approximate token budget for the injected brief
    MEMORY_MAX_HABITS_PER_AUTHOR: int = 50  # Cap dev_habits docs per author before compaction
    MEMORY_MAX_DECISIONS: int = 100  # Cap decisions per repo before compaction

    # Phase 4 — Socratic Dialogue & Autonomous Remediation
    REMEDIATION_CONFIDENCE_THRESHOLD: float = 0.85  # Auto-open fix PR above this confidence
    REMEDIATION_BRANCH_PREFIX: str = "gitsentry/fix-"
    STATUS_CHECK_CONTEXT: str = "gitsentry/security"
    GITSENTRY_BOT_LOGIN: str = "gitsentry[bot]"
    MAX_REMEDIATION_DIFF_LINES: int = 50  # Only auto-fix if suggested_fix < this many lines
    SOCRATIC_WEAK_JUSTIFICATION_MIN_WORDS: int = 10  # Below this, justification is "thin"

    # Feature Flags
    USE_SECRET_MANAGER: Optional[bool] = None  # Auto-detected if None

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_test(self) -> bool:
        return self.ENVIRONMENT == "test"

    @property
    def should_use_secret_manager(self) -> bool:
        if self.USE_SECRET_MANAGER is not None:
            return self.USE_SECRET_MANAGER
        return self.ENVIRONMENT in ("production", "staging")


@lru_cache()
def get_settings() -> Settings:
    """Returns cached instance of application settings."""
    return Settings()
