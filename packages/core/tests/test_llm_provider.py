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


# ─── Test 3 — forced-429 storm falls back to Hugging Face (THE GATE) ────────


async def test_llm_forced_429_storm_falls_back_to_huggingface(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    """Groq is 429ing indefinitely. The provider must reach Hugging Face
    and return a real response.

    Note: the v1 RESOLUTION chain for ``INTENT_PROFILER`` is Groq → HF
    (the Cerebras tier was removed in the 2026-06-16 harness session —
    the available Cerebras free-tier models didn't match the llama
    bindings). The Cerebras client is still wired in here so that the
    test continues to exercise the "skip a configured provider that
    isn't in the per-model chain" branch.
    """
    groq = FakeClient(
        ProviderName.GROQ,
        [RateLimitError("storm")] * 50,
    )
    cerebras = FakeClient(
        ProviderName.CEREBRAS,
        [RateLimitError("storm")] * 50,
    )
    hf_resp = make_response(
        provider=ProviderName.HUGGINGFACE,
        physical_model="meta-llama/Llama-3.3-70B-Instruct",
        text="fallback-ok",
        prompt_tokens=11,
        completion_tokens=4,
    )
    hf = FakeClient(ProviderName.HUGGINGFACE, [hf_resp])

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
    assert response.provider == ProviderName.HUGGINGFACE
    assert response.cached is False
    assert elapsed < 30.0, f"took {elapsed:.2f}s — gate is <30s"

    # Each provider actually in the INTENT_PROFILER chain must have been
    # tried up to its retry budget before the chain advanced — we don't
    # allow a shortcut. Cerebras is not in the chain so it must NOT be
    # called.
    assert len(groq.calls) == tmp_settings.llm_max_429_retries
    assert len(cerebras.calls) == 0
    assert len(hf.calls) == 1


async def test_llm_chain_exhausted_raises_provider_error(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    groq = FakeClient(ProviderName.GROQ, [RateLimitError("storm")] * 50)
    cerebras = FakeClient(ProviderName.CEREBRAS, [RateLimitError("storm")] * 50)
    hf = FakeClient(ProviderName.HUGGINGFACE, [RateLimitError("storm")] * 50)

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


async def test_llm_retry_override_caps_provider_attempts(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    groq = FakeClient(ProviderName.GROQ, [RateLimitError("storm")] * 50)
    hf = FakeClient(
        ProviderName.HUGGINGFACE,
        [
            make_response(
                provider=ProviderName.HUGGINGFACE,
                physical_model="meta-llama/Llama-3.3-70B-Instruct",
                text="fallback-ok",
            )
        ],
    )
    provider = make_provider(
        tmp_settings,
        {
            ProviderName.GROQ: groq,
            ProviderName.HUGGINGFACE: hf,
        },
    )

    response = await provider.generate(
        ModelId.INTENT_PROFILER,
        _msgs(),
        retry_429_attempts=1,
    )

    assert response.text == "fallback-ok"
    assert len(groq.calls) == 1
    assert len(hf.calls) == 1


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


async def test_verifier_uses_groq_with_hf_fallback(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    """VERIFIER resolves to Groq first then Hugging Face — Cerebras must not be touched."""
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
    cerebras = FakeClient(ProviderName.CEREBRAS, [])  # raise if called
    hf = FakeClient(ProviderName.HUGGINGFACE, [])  # raise if called
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
    # Verifier has no Cerebras binding, and HF is only reached on Groq failure.
    assert cerebras.calls == []
    assert hf.calls == []


async def test_real_httpx_429_path(tmp_settings, respx_mock) -> None:  # type: ignore[no-untyped-def]
    """End-to-end with a real httpx client and respx mocks for the HTTP layer.

    This proves the OpenAI-compatible client surface actually parses 429s
    and propagates RateLimitError — no internal short-circuit. The HF
    Inference Providers gateway is OpenAI-compatible so the same client
    handles all three.
    """
    # Groq is 429; Cerebras is the same shape; HF Inference Providers answers.
    respx_mock.post("https://api.groq.com/openai/v1/chat/completions").mock(
        return_value=httpx.Response(429, json={"error": "slow down"})
    )
    respx_mock.post("https://api.cerebras.ai/v1/chat/completions").mock(
        return_value=httpx.Response(429, json={"error": "slow down"})
    )
    respx_mock.post("https://router.huggingface.co/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "real-huggingface"}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 7},
            },
        )
    )

    provider = LLMProvider.build(settings=tmp_settings)
    try:
        response = await provider.generate(ModelId.INTENT_PROFILER, _msgs())
    finally:
        await provider.aclose()

    assert response.text == "real-huggingface"
    assert response.provider == ProviderName.HUGGINGFACE
    assert provider.tokens_used[ModelId.INTENT_PROFILER] == 19
