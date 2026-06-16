"""Application settings, loaded from environment / `.env` via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_repo_env() -> Path:
    """Walk up from this file to the repo root and return the ``.env`` path.

    Lets ``alembic`` / ``pytest`` / scripts invoked from any subdirectory
    pick up the single repo-root ``.env`` instead of silently falling back
    to defaults (which masked Neon connectivity behind a local-Postgres
    fallback during Phase 3 entry checks).
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / ".env"
        if candidate.exists():
            return candidate
    return Path(".env")


class Settings(BaseSettings):
    """Single source of runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=_find_repo_env(),
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

    # Hugging Face Inference Providers (https://router.huggingface.co/v1) —
    # OpenAI-compatible gateway that routes to underlying model providers
    # (Cerebras, Together, Replicate, etc.). Token can be a free user token
    # from huggingface.co/settings/tokens (read scope is sufficient).
    huggingface_api_key: str | None = None
    huggingface_base_url: str = "https://router.huggingface.co/v1"

    # Sentence-transformers embedder. Runs in-process; no daemon, no HTTP.
    # nomic-embed-text-v1.5 is 768-dim and matches the existing pgvector schema.
    # On first use the model weights are downloaded from huggingface.co into
    # the local `huggingface_hub` cache (~250MB).
    huggingface_embedding_model: str = "nomic-ai/nomic-embed-text-v1.5"

    # ── LLM behaviour ────────────────────────────────────────────────────────
    llm_cache_path: Path = Field(default_factory=lambda: Path(".cache/llm.sqlite"))
    llm_max_429_retries: int = 5
    llm_backoff_base_seconds: float = 0.5
    llm_backoff_max_seconds: float = 8.0
    llm_request_timeout_seconds: float = 60.0

    # ── GitHub ───────────────────────────────────────────────────────────────
    github_pat: str | None = None

    # ── Ingestion (Phase 1) ──────────────────────────────────────────────────
    ingestion_clone_root: Path = Field(default_factory=lambda: Path(".cache/clones"))
    ingestion_max_repo_loc: int = 200_000
    ingestion_summary_concurrency: int = 8
    ingestion_embed_batch_size: int = 32
    ingestion_embed_concurrency: int = 4

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
