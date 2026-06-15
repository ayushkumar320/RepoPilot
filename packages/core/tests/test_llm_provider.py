"""Phase 0 TDD tests 1–4 for `LLMProvider`.

Each test is one of the gates from `docs/05_PHASE_PROMPTS.md` § Phase 0 prompt.
Test 5 (settings) lives in `test_settings.py`.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest

from repopilot_core.llm.models import ModelId, ProviderName
from repopilot_core.llm.provider import (
    LLMProvider,
    Message,
    ProviderError,
    RateLimitError,
    _backoff_delay,
)

from .conftest import FakeClient, make_provider, make_response

# `asyncio_mode = auto` in pyproject means async tests are picked up automatically.


# ─── Helpers ───────────────────────────────────────────────────────────────


def _msgs() -> list[Message]:
    return [Message("user", "hello")]


# ─── Test 1 — cache hit avoids second call ─────────────────────────────────


async def test_llm_cache_hit_avoids_api_call(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    groq = FakeClient(
        ProviderName.GROQ,
        [make_response(provider=ProviderName.GROQ, physical_model="llama-3.3-70b-versatile")],
    )
    provider = make_provider(tmp_settings, {ProviderName.GROQ: groq})

    r1 = await provider.generate(ModelId.INTENT_PROFILER, _msgs())
    r2 = await provider.generate(ModelId.INTENT_PROFILER, _msgs())

    assert r1.text == "ok"
    assert r1.cached is False
    assert r2.cached is True
    assert len(groq.calls) == 1, "second identical call must NOT hit the provider"


# ─── Test 2 — 429 backoff retries then succeeds ────────────────────────────


async def test_llm_429_backoff_retries(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    groq = FakeClient(
        ProviderName.GROQ,
        [
            RateLimitError("first burst"),
            RateLimitError("second burst"),
            make_response(provider=ProviderName.GROQ),
        ],
    )
    provider = make_provider(tmp_settings, {ProviderName.GROQ: groq})

    response = await provider.generate(ModelId.INTENT_PROFILER, _msgs())

    assert response.text == "ok"
    assert response.provider == ProviderName.GROQ
    assert len(groq.calls) == 3, "should have retried twice before succeeding"


def test_backoff_delay_is_bounded() -> None:
    for attempt in range(10):
        delay = _backoff_delay(attempt, base=0.5, cap=8.0)
        assert 0.0 <= delay <= 8.0


# ─── Test 3 — forced-429 storm falls back to Ollama (THE GATE) ─────────────


async def test_llm_forced_429_storm_falls_back_to_ollama(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    """Groq is 429ing indefinitely; Cerebras is 429ing indefinitely.
    The provider must reach Ollama and return a real response.

    The fallback chain code is NOT bypassed — each upstream provider exhausts
    its retry budget before the chain advances. The forced-429 budget is
    `llm_max_429_retries` per provider.
    """
    groq = FakeClient(
        ProviderName.GROQ,
        [RateLimitError("storm")] * 50,
    )
    cerebras = FakeClient(
        ProviderName.CEREBRAS,
        [RateLimitError("storm")] * 50,
    )
    ollama_resp = make_response(
        provider=ProviderName.OLLAMA,
        physical_model="qwen2.5-coder:7b",
        text="fallback-ok",
        prompt_tokens=11,
        completion_tokens=4,
    )
    ollama = FakeClient(ProviderName.OLLAMA, [ollama_resp])

    provider = make_provider(
        tmp_settings,
        {
            ProviderName.GROQ: groq,
            ProviderName.CEREBRAS: cerebras,
            ProviderName.OLLAMA: ollama,
        },
    )

    started = asyncio.get_event_loop().time()
    response = await asyncio.wait_for(
        provider.generate(ModelId.INTENT_PROFILER, _msgs()),
        timeout=30.0,
    )
    elapsed = asyncio.get_event_loop().time() - started

    assert response.text == "fallback-ok"
    assert response.provider == ProviderName.OLLAMA
    assert response.cached is False
    assert elapsed < 30.0, f"took {elapsed:.2f}s — gate is <30s"

    # Each upstream provider must have been *tried* up to its retry budget
    # before the chain advanced — we don't allow a shortcut.
    assert len(groq.calls) == tmp_settings.llm_max_429_retries
    assert len(cerebras.calls) == tmp_settings.llm_max_429_retries
    assert len(ollama.calls) == 1


async def test_llm_chain_exhausted_raises_provider_error(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    groq = FakeClient(ProviderName.GROQ, [RateLimitError("storm")] * 50)
    cerebras = FakeClient(ProviderName.CEREBRAS, [RateLimitError("storm")] * 50)
    ollama = FakeClient(ProviderName.OLLAMA, [RateLimitError("storm")] * 50)

    provider = make_provider(
        tmp_settings,
        {
            ProviderName.GROQ: groq,
            ProviderName.CEREBRAS: cerebras,
            ProviderName.OLLAMA: ollama,
        },
    )

    with pytest.raises(ProviderError):
        await provider.generate(ModelId.INTENT_PROFILER, _msgs())


# ─── Test 4 — tokens_used counter increments ───────────────────────────────


async def test_llm_token_counter_increments(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    groq = FakeClient(
        ProviderName.GROQ,
        [
            make_response(provider=ProviderName.GROQ, prompt_tokens=10, completion_tokens=5),
            make_response(provider=ProviderName.GROQ, prompt_tokens=4, completion_tokens=1),
        ],
    )
    provider = make_provider(tmp_settings, {ProviderName.GROQ: groq})

    await provider.generate(ModelId.INTENT_PROFILER, _msgs())
    await provider.generate(ModelId.INTENT_PROFILER, [Message("user", "second question")])

    assert provider.tokens_used[ModelId.INTENT_PROFILER] == 10 + 5 + 4 + 1


# ─── Cross-cutting — sanity ────────────────────────────────────────────────


async def test_ollama_only_models_skip_groq(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    """VERIFIER and EMBEDDINGS resolve to Ollama only — Groq must not be touched."""
    groq = FakeClient(ProviderName.GROQ, [])  # raise if called
    ollama = FakeClient(
        ProviderName.OLLAMA,
        [
            make_response(
                provider=ProviderName.OLLAMA,
                physical_model="qwen2.5-coder:7b",
                text="verified",
            )
        ],
    )
    provider = make_provider(
        tmp_settings,
        {ProviderName.GROQ: groq, ProviderName.OLLAMA: ollama},
    )

    response = await provider.generate(ModelId.VERIFIER, _msgs())
    assert response.provider == ProviderName.OLLAMA
    assert groq.calls == []


async def test_real_httpx_429_path(tmp_settings, respx_mock) -> None:  # type: ignore[no-untyped-def]
    """End-to-end with a real httpx client and respx mocks for the HTTP layer.

    This proves the OpenAI-compatible client surface actually parses 429s
    and propagates RateLimitError — no internal short-circuit.
    """
    # Groq is 429; Cerebras is the same shape; Ollama answers.
    respx_mock.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(429, json={"error": "slow down"})
    )
    respx_mock.post("https://api.cerebras.ai/v1/chat/completions").mock(
        return_value=httpx.Response(429, json={"error": "slow down"})
    )
    respx_mock.post("http://ollama.local/api/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "message": {"content": "real-ollama"},
                "prompt_eval_count": 12,
                "eval_count": 7,
            },
        )
    )

    provider = LLMProvider.build(settings=tmp_settings)
    try:
        response = await provider.generate(ModelId.INTENT_PROFILER, _msgs())
    finally:
        await provider.aclose()

    assert response.text == "real-ollama"
    assert response.provider == ProviderName.OLLAMA
    assert provider.tokens_used[ModelId.INTENT_PROFILER] == 19
