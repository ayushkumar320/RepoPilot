"""Application settings, loaded from environment / `.env` via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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


def _split_csv(value: str) -> list[str]:
    """Parse a comma-separated env var into a cleaned list."""
    return [item.strip() for item in value.split(",") if item.strip()]


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
    repopilot_web_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://127.0.0.1:3000", "http://localhost:3000"]
    )

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
    # Retry budget sized to ride out a full Groq 60s TPM window before the
    # chain falls through to Cerebras. With base=0.5, max=20, jitter, worst
    # case cumulative sleep across 8 attempts is ~80s — enough to drain a
    # 60s per-minute quota reset before escalating.
    llm_max_429_retries: int = 8
    llm_backoff_base_seconds: float = 0.5
    llm_backoff_max_seconds: float = 20.0
    llm_request_timeout_seconds: float = 60.0
    # Cap on concurrent verifier LLM calls. Unbounded `asyncio.gather` over a
    # section's claims stampedes the free-tier per-second quota so hard that
    # backoff never catches up (both Groq and Cerebras 429 at once). A small
    # cap lets the 429 backoff actually drain the quota window. 0 = unbounded.
    llm_verifier_max_concurrency: int = 3

    # ── Reranking (RAG Phase 4) ──────────────────────────────────────────────
    # Cross-encoder over the post-retrieval pool. MiniLM-L-6-v2 is 80 MB ONNX,
    # ~460 pairs/s on CPU; BAAI/bge-reranker-base (1 GB) is the quality
    # fallback if the pairwise self-test flags MiniLM as code-mismatched.
    rerank_enabled: bool = True
    rerank_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"
    rerank_max_pool: int = 30
    rerank_lambda: float = 0.7

    # ── Context compression (RAG Phase 5) ───────────────────────────────────
    compress_enabled: bool = True
    compress_min_chunk_lines: int = 15

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

    @field_validator("repopilot_web_origins", mode="before")
    @classmethod
    def _coerce_web_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return _split_csv(value)
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor. Tests should call `get_settings.cache_clear()`."""
    return Settings()
