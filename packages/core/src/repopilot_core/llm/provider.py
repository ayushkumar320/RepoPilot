"""The single LLMProvider every agent goes through.

Responsibilities (Phase 0 deliverable per `docs/05_PHASE_PROMPTS.md`):

* Resolve a logical `ModelId` to the right physical model on the right provider.
* SQLite cache keyed on sha256(model + canonical_json(messages) + kwargs).
* Exponential backoff with jitter on 429, max N attempts (config).
* Provider fallback chain: Groq → Cerebras → Ollama. If the entire chain is
  exhausted, raise `ProviderError`.
* Per-`ModelId` `tokens_used` counter, summed across providers.

Design notes
------------
The provider speaks OpenAI-compatible HTTP for Groq and Cerebras, and the
native Ollama HTTP API. Both shapes are mapped to a unified `LLMResponse`
internally so callers never branch on provider.

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


class _OllamaClient(_BaseClient):
    """Native Ollama API client."""

    provider = ProviderName.OLLAMA

    def __init__(self, http: httpx.AsyncClient, base_url: str) -> None:
        self._http = http
        self._base_url = base_url.rstrip("/")

    async def chat(
        self,
        binding: ModelBinding,
        messages: Sequence[Message],
        kwargs: dict[str, Any],
    ) -> LLMResponse:
        body: dict[str, Any] = {
            "model": binding.physical_model,
            "messages": [m.to_openai() for m in messages],
            "stream": False,
        }
        options = {k: v for k, v in kwargs.items() if k not in {"stream"}}
        if options:
            body["options"] = options
        resp = await self._http.post(f"{self._base_url}/api/chat", json=body)
        if resp.status_code == 429:
            raise RateLimitError("ollama returned 429")
        resp.raise_for_status()
        data = resp.json()
        text = data.get("message", {}).get("content", "")
        return LLMResponse(
            text=text,
            model=ModelId.INTENT_PROFILER,  # overwritten by caller
            provider=self.provider,
            physical_model=binding.physical_model,
            prompt_tokens=int(data.get("prompt_eval_count", 0)),
            completion_tokens=int(data.get("eval_count", 0)),
        )


# ─── LLMProvider ────────────────────────────────────────────────────────────


@dataclass
class LLMProvider:
    """Single entrypoint to every LLM call in the system."""

    settings: Settings
    http: httpx.AsyncClient
    cache: _SQLiteCache
    clients: dict[ProviderName, _BaseClient]
    tokens_used: dict[ModelId, int] = field(default_factory=lambda: defaultdict(int))

    # ── construction ───────────────────────────────────────────────────────

    @classmethod
    def build(
        cls,
        *,
        settings: Settings | None = None,
        http: httpx.AsyncClient | None = None,
        clients: dict[ProviderName, _BaseClient] | None = None,
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
            clients[ProviderName.OLLAMA] = _OllamaClient(http, settings.ollama_base_url)
        cache = _SQLiteCache(settings.llm_cache_path)
        return cls(settings=settings, http=http, cache=cache, clients=clients)

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
