"""The single LLMProvider every agent goes through.

Responsibilities (Phase 0 deliverable per `docs/05_PHASE_PROMPTS.md`):

* Resolve a logical `ModelId` to the right physical model on the right provider.
* SQLite cache keyed on sha256(model + canonical_json(messages) + kwargs).
* Exponential backoff with jitter on 429, max N attempts (config).
* Provider fallback chain: Groq → Cerebras → Hugging Face (Inference Providers).
  If the entire chain is exhausted, raise `ProviderError`.
* Per-`ModelId` `tokens_used` counter, summed across providers.

Design notes
------------
The provider speaks OpenAI-compatible HTTP for Groq, Cerebras, and Hugging
Face's Inference Providers gateway (https://router.huggingface.co/v1). The
unified `LLMResponse` shape lets callers stay provider-agnostic.

Embeddings run **in-process** via `sentence-transformers` (Hugging Face
model weights, no daemon, no HTTP). This is the only embeddings backend in
v1 — there is no Ollama anywhere.

Tests in `packages/core/tests/test_llm_provider.py` cover the five Phase 0
TDD gates. The forced-429-storm test exercises the real fallback chain end
to end against an httpx mock — no shortcut around the backoff/timeout logic.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import sqlite3
import time
from collections import defaultdict
from collections.abc import Sequence
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

import httpx
import structlog

from repopilot_core.llm.models import RESOLUTION, ModelBinding, ModelId, ProviderName
from repopilot_core.settings import Settings, get_settings

log = structlog.get_logger(__name__)


# ─── Public types ──────────────────────────────────────────────────────────


class ProviderError(RuntimeError):
    """All providers in the fallback chain failed."""


class RateLimitError(RuntimeError):
    """HTTP 429 from a provider — triggers retry/fallback inside the provider."""


@dataclass(frozen=True, slots=True)
class Message:
    role: str
    content: str

    def to_openai(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass(slots=True)
class LLMResponse:
    """Provider-agnostic response shape."""

    text: str
    model: ModelId
    provider: ProviderName
    physical_model: str
    prompt_tokens: int
    completion_tokens: int
    cached: bool = False

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(slots=True)
class EmbeddingResponse:
    """Provider-agnostic embedding shape."""

    vector: list[float]
    model: ModelId
    provider: ProviderName
    physical_model: str
    cached: bool = False

    @property
    def dim(self) -> int:
        return len(self.vector)


# ─── Cache ──────────────────────────────────────────────────────────────────


class _SQLiteCache:
    """Thread-safe SQLite cache keyed on the canonical request hash."""

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS llm_cache (
        key TEXT PRIMARY KEY,
        model TEXT NOT NULL,
        provider TEXT NOT NULL,
        physical_model TEXT NOT NULL,
        response_text TEXT NOT NULL,
        prompt_tokens INTEGER NOT NULL,
        completion_tokens INTEGER NOT NULL,
        created_at REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS embedding_cache (
        key TEXT PRIMARY KEY,
        model TEXT NOT NULL,
        provider TEXT NOT NULL,
        physical_model TEXT NOT NULL,
        vector_json TEXT NOT NULL,
        created_at REAL NOT NULL
    );
    """

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        self._lock = asyncio.Lock()
        with self._connect() as conn:
            conn.executescript(self._SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, isolation_level=None, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    async def get(self, key: str) -> LLMResponse | None:
        async with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT model, provider, physical_model, response_text, "
                    "       prompt_tokens, completion_tokens "
                    "FROM llm_cache WHERE key = ?",
                    (key,),
                ).fetchone()
        if row is None:
            return None
        model_s, provider_s, physical, text, ptoks, ctoks = row
        return LLMResponse(
            text=text,
            model=ModelId(model_s),
            provider=ProviderName(provider_s),
            physical_model=physical,
            prompt_tokens=int(ptoks),
            completion_tokens=int(ctoks),
            cached=True,
        )

    async def put(self, key: str, response: LLMResponse) -> None:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO llm_cache "
                    "(key, model, provider, physical_model, response_text, "
                    " prompt_tokens, completion_tokens, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        key,
                        response.model.value,
                        response.provider.value,
                        response.physical_model,
                        response.text,
                        response.prompt_tokens,
                        response.completion_tokens,
                        time.time(),
                    ),
                )

    async def get_embedding(self, key: str) -> EmbeddingResponse | None:
        async with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT model, provider, physical_model, vector_json "
                    "FROM embedding_cache WHERE key = ?",
                    (key,),
                ).fetchone()
        if row is None:
            return None
        model_s, provider_s, physical, vector_json = row
        return EmbeddingResponse(
            vector=json.loads(vector_json),
            model=ModelId(model_s),
            provider=ProviderName(provider_s),
            physical_model=physical,
            cached=True,
        )

    async def put_embedding(self, key: str, response: EmbeddingResponse) -> None:
        async with self._lock:
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO embedding_cache "
                    "(key, model, provider, physical_model, vector_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        key,
                        response.model.value,
                        response.provider.value,
                        response.physical_model,
                        json.dumps(response.vector, separators=(",", ":")),
                        time.time(),
                    ),
                )


def _cache_key(model: ModelId, messages: Sequence[Message], kwargs: dict[str, Any]) -> str:
    payload = {
        "model": model.value,
        "messages": [m.to_openai() for m in messages],
        "kwargs": kwargs,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ─── Backoff ────────────────────────────────────────────────────────────────


def _backoff_delay(attempt: int, base: float, cap: float) -> float:
    """Exponential backoff with full jitter. attempt=0 is the first retry."""
    expo = min(cap, base * (2**attempt))
    return random.uniform(0.0, expo)


# ─── Provider HTTP clients ──────────────────────────────────────────────────


class _BaseClient:
    """Common interface for provider HTTP shims."""

    provider: ProviderName

    async def chat(
        self,
        binding: ModelBinding,
        messages: Sequence[Message],
        kwargs: dict[str, Any],
    ) -> LLMResponse:
        raise NotImplementedError


class _OpenAICompatibleClient(_BaseClient):
    """Speaks the OpenAI chat-completions shape. Used for Groq and Cerebras."""

    def __init__(
        self,
        provider: ProviderName,
        http: httpx.AsyncClient,
        base_url: str,
        api_key: str,
    ) -> None:
        self.provider = provider
        self._http = http
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    async def chat(
        self,
        binding: ModelBinding,
        messages: Sequence[Message],
        kwargs: dict[str, Any],
    ) -> LLMResponse:
        body = {
            "model": binding.physical_model,
            "messages": [m.to_openai() for m in messages],
            **kwargs,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        resp = await self._http.post(
            f"{self._base_url}/chat/completions",
            json=body,
            headers=headers,
        )
        if resp.status_code == 429:
            raise RateLimitError(f"{self.provider.value} returned 429")
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
        return LLMResponse(
            text=text,
            model=ModelId.INTENT_PROFILER,  # overwritten by caller; see provider.generate
            provider=self.provider,
            physical_model=binding.physical_model,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
        )


class _SentenceTransformersEmbedder(_BaseClient):
    """In-process embedder using sentence-transformers (Hugging Face weights).

    No HTTP, no daemon, no Docker. Model weights are downloaded from
    huggingface.co on first use into the local `huggingface_hub` cache.
    `nomic-embed-text-v1.5` is 768-dim and matches the existing pgvector schema.
    """

    provider = ProviderName.HUGGINGFACE

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        # Lazy-loaded on first use so module import stays cheap.
        self._model: Any = None
        self._load_lock = asyncio.Lock()

    async def _ensure_loaded(self) -> Any:
        if self._model is None:
            async with self._load_lock:
                if self._model is None:  # double-checked locking
                    self._model = await asyncio.to_thread(self._load_model)
        return self._model

    def _load_model(self) -> Any:
        # Import inside the method so a missing optional dep doesn't blow up
        # import of repopilot_core.
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(self._model_name, trust_remote_code=True)

    async def embed(self, binding: ModelBinding, text: str) -> EmbeddingResponse:
        model = await self._ensure_loaded()
        vector = await asyncio.to_thread(
            lambda: model.encode(text, normalize_embeddings=True, convert_to_numpy=True).tolist()
        )
        return EmbeddingResponse(
            vector=list(vector),
            model=ModelId.EMBEDDINGS,
            provider=self.provider,
            physical_model=binding.physical_model,
        )

    async def chat(
        self,
        binding: ModelBinding,
        messages: Sequence[Message],
        kwargs: dict[str, Any],
    ) -> LLMResponse:
        raise NotImplementedError("sentence-transformers embedder does not support chat completion")


# ─── LLMProvider ────────────────────────────────────────────────────────────


@dataclass
class LLMProvider:
    """Single entrypoint to every LLM call in the system."""

    settings: Settings
    http: httpx.AsyncClient
    cache: _SQLiteCache
    clients: dict[ProviderName, _BaseClient]
    embedder: _BaseClient  # always sentence-transformers in v1
    tokens_used: dict[ModelId, int] = field(default_factory=lambda: defaultdict(int))

    # ── construction ───────────────────────────────────────────────────────

    @classmethod
    def build(
        cls,
        *,
        settings: Settings | None = None,
        http: httpx.AsyncClient | None = None,
        clients: dict[ProviderName, _BaseClient] | None = None,
        embedder: _BaseClient | None = None,
    ) -> Self:
        """Default wiring used by the app. Tests pass `clients` for full control."""
        settings = settings or get_settings()
        http = http or httpx.AsyncClient(timeout=settings.llm_request_timeout_seconds)
        if clients is None:
            clients = {}
            if settings.groq_api_key:
                clients[ProviderName.GROQ] = _OpenAICompatibleClient(
                    ProviderName.GROQ,
                    http,
                    settings.groq_base_url,
                    settings.groq_api_key,
                )
            if settings.cerebras_api_key:
                clients[ProviderName.CEREBRAS] = _OpenAICompatibleClient(
                    ProviderName.CEREBRAS,
                    http,
                    settings.cerebras_base_url,
                    settings.cerebras_api_key,
                )
            # Hugging Face Inference Providers (OpenAI-compatible gateway).
            # The chat path uses HF for any model in the resolution chain whose
            # provider is HUGGINGFACE. The embedding path is served separately
            # by the in-process sentence-transformers embedder below.
            if settings.huggingface_api_key:
                clients[ProviderName.HUGGINGFACE] = _OpenAICompatibleClient(
                    ProviderName.HUGGINGFACE,
                    http,
                    settings.huggingface_base_url,
                    settings.huggingface_api_key,
                )
        cache = _SQLiteCache(settings.llm_cache_path)
        # The embedder loads its model lazily on first call; constructing it
        # is cheap. Tests can pass `embedder=` to override.
        if embedder is None:
            embedder = _SentenceTransformersEmbedder(settings.huggingface_embedding_model)
        return cls(
            settings=settings,
            http=http,
            cache=cache,
            clients=clients,
            embedder=embedder,
        )

    async def aclose(self) -> None:
        with suppress(Exception):
            await self.http.aclose()

    # ── public API ─────────────────────────────────────────────────────────

    async def generate(
        self,
        model: ModelId,
        messages: Sequence[Message],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion. Hits cache first; otherwise walks the fallback chain."""
        key = _cache_key(model, messages, kwargs)
        cached = await self.cache.get(key)
        if cached is not None:
            cached.model = model
            log.debug("llm.cache_hit", model=model.value, provider=cached.provider.value)
            return cached

        chain = RESOLUTION.get(model)
        if not chain:
            raise ProviderError(f"no resolution chain for {model.value}")

        last_error: Exception | None = None
        for binding in chain:
            client = self.clients.get(binding.provider)
            if client is None:
                log.debug("llm.skip_unconfigured_provider", provider=binding.provider.value)
                continue
            try:
                response = await self._call_with_429_retry(client, binding, messages, kwargs)
            except RateLimitError as exc:
                last_error = exc
                log.warning(
                    "llm.provider_exhausted_retries",
                    model=model.value,
                    provider=binding.provider.value,
                    physical=binding.physical_model,
                )
                continue
            except (httpx.HTTPError, ConnectionError, OSError) as exc:
                last_error = exc
                log.warning(
                    "llm.provider_transport_error",
                    model=model.value,
                    provider=binding.provider.value,
                    error=str(exc),
                )
                continue

            response.model = model
            self.tokens_used[model] += response.total_tokens
            await self.cache.put(key, response)
            return response

        raise ProviderError(
            f"all providers failed for {model.value}: {last_error!r}"
        ) from last_error

    async def embed(self, text: str, *, model: ModelId = ModelId.EMBEDDINGS) -> EmbeddingResponse:
        """Embed ``text`` via the in-process sentence-transformers embedder.

        No HTTP, no daemon, no Docker. Model weights are downloaded from
        Hugging Face on first use into the local hub cache. Cached by
        ``sha256(model + text)`` in SQLite.
        """
        canonical = json.dumps(
            {"model": model.value, "text": text}, sort_keys=True, separators=(",", ":")
        )
        key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        cached = await self.cache.get_embedding(key)
        if cached is not None:
            cached.model = model
            return cached

        chain = RESOLUTION.get(model)
        if not chain:
            raise ProviderError(f"no resolution chain for {model.value}")
        # In v1 the chain has a single binding pointing at the in-process
        # sentence-transformers embedder. We pass the binding through so the
        # embedder knows which HF model id to load.
        binding = chain[0]
        embed_method = getattr(self.embedder, "embed", None)
        if embed_method is None:
            raise ProviderError("embedder does not support embed()")
        try:
            response: EmbeddingResponse = await embed_method(binding, text)
        except (OSError, RuntimeError) as exc:
            raise ProviderError(f"embedding failed for {model.value}: {exc!r}") from exc

        response.model = model
        await self.cache.put_embedding(key, response)
        return response

    # ── helpers ────────────────────────────────────────────────────────────

    async def _call_with_429_retry(
        self,
        client: _BaseClient,
        binding: ModelBinding,
        messages: Sequence[Message],
        kwargs: dict[str, Any],
    ) -> LLMResponse:
        """Per-binding 429 retry loop with exponential backoff + jitter."""
        max_attempts = max(1, self.settings.llm_max_429_retries)
        attempt = 0
        while True:
            try:
                return await client.chat(binding, messages, kwargs)
            except RateLimitError:
                attempt += 1
                if attempt >= max_attempts:
                    raise
                delay = _backoff_delay(
                    attempt - 1,
                    self.settings.llm_backoff_base_seconds,
                    self.settings.llm_backoff_max_seconds,
                )
                log.info(
                    "llm.backoff",
                    provider=binding.provider.value,
                    attempt=attempt,
                    delay=round(delay, 3),
                )
                await asyncio.sleep(delay)
