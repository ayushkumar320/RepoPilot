"""Application settings, loaded from environment / `.env` via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single source of runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Environment ──────────────────────────────────────────────────────────
    repopilot_env: str = "development"
    repopilot_log_level: str = "INFO"

    # ── LLM providers ────────────────────────────────────────────────────────
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"

    cerebras_api_key: str | None = None
    cerebras_base_url: str = "https://api.cerebras.ai/v1"

    ollama_base_url: str = "http://localhost:11434"
    ollama_verifier_model: str = "qwen2.5-coder:7b"
    ollama_embeddings_model: str = "nomic-embed-text"

    # ── LLM behaviour ────────────────────────────────────────────────────────
    llm_cache_path: Path = Field(default_factory=lambda: Path(".cache/llm.sqlite"))
    llm_max_429_retries: int = 5
    llm_backoff_base_seconds: float = 0.5
    llm_backoff_max_seconds: float = 8.0
    llm_request_timeout_seconds: float = 60.0

    # ── GitHub ───────────────────────────────────────────────────────────────
    github_pat: str | None = None

    # ── Datastores ───────────────────────────────────────────────────────────
    postgres_dsn: str = "postgresql+psycopg://repopilot:repopilot@localhost:5432/repopilot"
    redis_url: str = "redis://localhost:6379/0"

    # ── LangSmith (optional) ─────────────────────────────────────────────────
    langsmith_api_key: str | None = None
    langsmith_project: str = "repopilot-dev"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor. Tests should call `get_settings.cache_clear()`."""
    return Settings()
