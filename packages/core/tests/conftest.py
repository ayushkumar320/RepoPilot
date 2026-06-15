"""Shared fixtures for the core package's tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

from repopilot_core.llm.models import ModelId, ProviderName
from repopilot_core.llm.provider import (
    LLMProvider,
    LLMResponse,
    Message,
    _BaseClient,
    _SQLiteCache,
)
from repopilot_core.settings import Settings, get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Iterator[None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def tmp_settings(tmp_path: Path) -> Settings:
    return Settings(
        repopilot_env="test",
        groq_api_key="test-groq",
        cerebras_api_key="test-cerebras",
        ollama_base_url="http://ollama.local",
        llm_cache_path=tmp_path / "llm.sqlite",
        llm_max_429_retries=3,
        llm_backoff_base_seconds=0.0,
        llm_backoff_max_seconds=0.0,
        llm_request_timeout_seconds=5.0,
    )


class FakeClient(_BaseClient):
    """Test double for an LLM provider client."""

    def __init__(self, provider: ProviderName, responses: list[object]) -> None:
        self.provider = provider
        self._responses = list(responses)
        self.calls: list[tuple[str, list[Message], dict[str, object]]] = []

    async def chat(self, binding, messages, kwargs):
        self.calls.append((binding.physical_model, list(messages), dict(kwargs)))
        if not self._responses:
            raise AssertionError(f"FakeClient({self.provider.value}) exhausted")
        head = self._responses.pop(0)
        if isinstance(head, Exception):
            raise head
        assert isinstance(head, LLMResponse)
        return head


def make_provider(
    settings: Settings,
    clients: dict[ProviderName, _BaseClient],
) -> LLMProvider:
    """Build an LLMProvider that uses the supplied fakes for every provider."""
    http = httpx.AsyncClient()
    cache = _SQLiteCache(settings.llm_cache_path)
    return LLMProvider(settings=settings, http=http, cache=cache, clients=clients)


def make_response(
    *,
    provider: ProviderName,
    physical_model: str = "test-model",
    text: str = "ok",
    prompt_tokens: int = 7,
    completion_tokens: int = 3,
) -> LLMResponse:
    return LLMResponse(
        text=text,
        model=ModelId.INTENT_PROFILER,  # overwritten by provider.generate
        provider=provider,
        physical_model=physical_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
