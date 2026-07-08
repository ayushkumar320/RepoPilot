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


# ─── Test 3 — forced-429 storm falls back to Cerebras (THE GATE) ────────────


async def test_llm_forced_429_storm_falls_back_to_cerebras(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    """Groq is 429ing indefinitely. The provider must reach Cerebras and
    return a real response.

    Post-2026-07-07: HF is no longer in the chat resolution chain (its free
    tier exhausts on a single bench run). The chat chain is Groq → Cerebras;
    if BOTH are 429, `ProviderError` is raised instead of silently draining
    HF credits.
    """
    groq = FakeClient(
        ProviderName.GROQ,
        [RateLimitError("storm")] * 50,
    )
    cerebras_resp = make_response(
        provider=ProviderName.CEREBRAS,
        physical_model="llama-3.3-70b",
        text="fallback-ok",
        prompt_tokens=11,
        completion_tokens=4,
    )
    cerebras = FakeClient(ProviderName.CEREBRAS, [cerebras_resp])
    # HF client is wired but must NEVER be called for chat models.
    hf = FakeClient(ProviderName.HUGGINGFACE, [])

    provider = make_provider(
        tmp_settings,
        {
            ProviderName.GROQ: groq,
            ProviderName.CEREBRAS: cerebras,
            ProviderName.HUGGINGFACE: hf,
        },
    )

    started = asyncio.get_event_loop().time()
    response = await asyncio.wait_for(
        provider.generate(ModelId.INTENT_PROFILER, _msgs()),
        timeout=30.0,
    )
    elapsed = asyncio.get_event_loop().time() - started

    assert response.text == "fallback-ok"
    assert response.provider == ProviderName.CEREBRAS
    assert response.cached is False
    assert elapsed < 30.0, f"took {elapsed:.2f}s — gate is <30s"

    # Groq exhausts its retry budget before the chain advances to Cerebras.
    # HF is not in any chat chain and must NOT be called.
    assert len(groq.calls) == tmp_settings.llm_max_429_retries
    assert len(cerebras.calls) == 1
    assert len(hf.calls) == 0


async def test_llm_chain_exhausted_raises_provider_error(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    groq = FakeClient(ProviderName.GROQ, [RateLimitError("storm")] * 50)
    cerebras = FakeClient(ProviderName.CEREBRAS, [RateLimitError("storm")] * 50)
    # HF wired but not in the chat chain — must never be reached.
    hf = FakeClient(ProviderName.HUGGINGFACE, [])

    provider = make_provider(
        tmp_settings,
        {
            ProviderName.GROQ: groq,
            ProviderName.CEREBRAS: cerebras,
            ProviderName.HUGGINGFACE: hf,
        },
    )

    with pytest.raises(ProviderError):
        await provider.generate(ModelId.INTENT_PROFILER, _msgs())

    assert len(hf.calls) == 0


async def test_llm_retry_override_caps_provider_attempts(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    groq = FakeClient(ProviderName.GROQ, [RateLimitError("storm")] * 50)
    cerebras = FakeClient(
        ProviderName.CEREBRAS,
        [
            make_response(
                provider=ProviderName.CEREBRAS,
                physical_model="llama-3.3-70b",
                text="fallback-ok",
            )
        ],
    )
    provider = make_provider(
        tmp_settings,
        {
            ProviderName.GROQ: groq,
            ProviderName.CEREBRAS: cerebras,
        },
    )

    response = await provider.generate(
        ModelId.INTENT_PROFILER,
        _msgs(),
        retry_429_attempts=1,
    )

    assert response.text == "fallback-ok"
    assert len(groq.calls) == 1
    assert len(cerebras.calls) == 1


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


async def test_verifier_uses_groq_with_cerebras_fallback(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    """VERIFIER resolves to Groq first, Cerebras on 429 — HF is NOT in the chain."""
    groq = FakeClient(
        ProviderName.GROQ,
        [
            make_response(
                provider=ProviderName.GROQ,
                physical_model="qwen/qwen3-32b",
                text="verified",
            )
        ],
    )
    cerebras = FakeClient(ProviderName.CEREBRAS, [])  # would raise if called
    hf = FakeClient(
        ProviderName.HUGGINGFACE, []
    )  # would raise if called — HF is not in the chat chain
    provider = make_provider(
        tmp_settings,
        {
            ProviderName.GROQ: groq,
            ProviderName.CEREBRAS: cerebras,
            ProviderName.HUGGINGFACE: hf,
        },
    )

    response = await provider.generate(ModelId.VERIFIER, _msgs())
    assert response.provider == ProviderName.GROQ
    # Groq answers on first try; Cerebras is present but not needed. HF must
    # never be called for a chat model.
    assert cerebras.calls == []
    assert hf.calls == []
    assert hf.calls == []


async def test_real_httpx_429_path(tmp_settings, respx_mock) -> None:  # type: ignore[no-untyped-def]
    """End-to-end with a real httpx client and respx mocks for the HTTP layer.

    Proves the OpenAI-compatible client surface actually parses 429s and
    propagates RateLimitError — no internal short-circuit. Post-2026-07-07:
    HF is not in the chat chain, so Cerebras is the terminal fallback.
    """
    # Groq is 429; Cerebras answers 200. The HF route is registered but must
    # never be reached — the chat resolution chain stops at Cerebras.
    hf_route = respx_mock.post("https://router.huggingface.co/v1/chat/completions").mock(
        return_value=httpx.Response(500, json={"error": "should not be called"})
    )
    respx_mock.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(429, json={"error": "slow down"})
    )
    respx_mock.post("https://api.cerebras.ai/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "real-cerebras"}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 7},
            },
        )
    )

    provider = LLMProvider.build(settings=tmp_settings)
    try:
        response = await provider.generate(ModelId.INTENT_PROFILER, _msgs())
    finally:
        await provider.aclose()

    assert response.text == "real-cerebras"
    assert response.provider == ProviderName.CEREBRAS
    assert provider.tokens_used[ModelId.INTENT_PROFILER] == 19
    assert hf_route.call_count == 0, "HF must never be called for chat models"
