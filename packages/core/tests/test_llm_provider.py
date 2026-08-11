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
    TruncatedReasoningError,
    _backoff_delay,
    _extract_openai_compatible_text,
    _parse_retry_after,
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


async def test_qa_primary_spills_to_qa_fallback_after_chain_exhaustion(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    # QA_PRIMARY chain (2026-07-21, catalog-verified): Groq llama-3.3, Cerebras
    # zai-glm-4.7, Cerebras gemma-4-31b, Groq llama-3.1-8b-instant. After the
    # full chain 429s the caller spills to QA_FALLBACK, which starts on Groq
    # qwen/qwen3.6-27b.
    groq = FakeClient(
        ProviderName.GROQ,
        [
            RateLimitError("storm"),  # QA_PRIMARY: llama-3.3-70b-versatile
            RateLimitError("storm"),  # QA_PRIMARY: llama-3.1-8b-instant
            make_response(
                provider=ProviderName.GROQ,
                physical_model="qwen/qwen3.6-27b",
                text="fallback-answer",
                prompt_tokens=9,
                completion_tokens=4,
            ),
        ],
    )
    cerebras = FakeClient(
        ProviderName.CEREBRAS,
        [
            RateLimitError("storm"),  # QA_PRIMARY: zai-glm-4.7
            RateLimitError("storm"),  # QA_PRIMARY: gemma-4-31b
        ],
    )
    provider = make_provider(
        tmp_settings,
        {
            ProviderName.GROQ: groq,
            ProviderName.CEREBRAS: cerebras,
        },
    )

    response = await provider.generate(ModelId.QA_PRIMARY, _msgs(), retry_429_attempts=1)

    assert response.text == "fallback-answer"
    assert response.model == ModelId.QA_PRIMARY
    assert response.provider == ProviderName.GROQ
    assert response.physical_model == "qwen/qwen3.6-27b"
    assert provider.tokens_used[ModelId.QA_PRIMARY] == 13
    assert [call[0] for call in groq.calls] == [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "qwen/qwen3.6-27b",
    ]
    assert [call[0] for call in cerebras.calls] == [
        "zai-glm-4.7",
        "gemma-4-31b",
    ]


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


# ─── Retry-After handling ──────────────────────────────────────────────────


def test_parse_retry_after_variants() -> None:
    from datetime import UTC, datetime, timedelta
    from email.utils import format_datetime

    # delta-seconds form
    assert _parse_retry_after("7") == 7.0
    assert _parse_retry_after("  0.5 ") == 0.5
    # missing / garbage / non-positive → None (fall back to jittered backoff)
    assert _parse_retry_after(None) is None
    assert _parse_retry_after("") is None
    assert _parse_retry_after("soon") is None
    assert _parse_retry_after("0") is None
    assert _parse_retry_after("-3") is None
    # HTTP-date form ~30s in the future resolves to a positive delta
    future = format_datetime(datetime.now(UTC) + timedelta(seconds=30))
    parsed = _parse_retry_after(future)
    assert parsed is not None and 20.0 < parsed <= 31.0


async def test_retry_after_header_overrides_backoff(tmp_settings, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """A provider-supplied Retry-After (capped) wins over the jittered backoff."""
    import asyncio as _asyncio

    settings = tmp_settings.model_copy(
        update={
            "llm_backoff_base_seconds": 0.0,
            "llm_backoff_max_seconds": 0.0,
            "llm_retry_after_cap_seconds": 60.0,
            "llm_max_429_retries": 3,
        }
    )
    slept: list[float] = []

    async def _fake_sleep(delay: float) -> None:
        slept.append(delay)

    monkeypatch.setattr(_asyncio, "sleep", _fake_sleep)

    groq = FakeClient(
        ProviderName.GROQ,
        [
            RateLimitError("burst", retry_after=7.0),
            make_response(provider=ProviderName.GROQ),
        ],
    )
    provider = make_provider(settings, {ProviderName.GROQ: groq})

    response = await provider.generate(ModelId.INTENT_PROFILER, _msgs())

    assert response.text == "ok"
    # Jittered backoff would be 0.0; Retry-After forces the honest 7s wait.
    assert slept == [7.0]


async def test_retry_after_is_capped(tmp_settings, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """A hostile/huge Retry-After can't stall the run past the cap."""
    import asyncio as _asyncio

    settings = tmp_settings.model_copy(
        update={
            "llm_backoff_base_seconds": 0.0,
            "llm_backoff_max_seconds": 0.0,
            "llm_retry_after_cap_seconds": 30.0,
            "llm_max_429_retries": 3,
        }
    )
    slept: list[float] = []

    async def _fake_sleep(delay: float) -> None:
        slept.append(delay)

    monkeypatch.setattr(_asyncio, "sleep", _fake_sleep)

    groq = FakeClient(
        ProviderName.GROQ,
        [
            RateLimitError("burst", retry_after=9999.0),
            make_response(provider=ProviderName.GROQ),
        ],
    )
    provider = make_provider(settings, {ProviderName.GROQ: groq})

    await provider.generate(ModelId.INTENT_PROFILER, _msgs())
    assert slept == [30.0]


# ─── Opt-in HF chat fallback ───────────────────────────────────────────────


async def test_hf_chat_fallback_used_when_enabled(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    """With llm_hf_chat_fallback on, a Groq+Cerebras storm falls through to HF."""
    settings = tmp_settings.model_copy(update={"llm_hf_chat_fallback": True})
    groq = FakeClient(ProviderName.GROQ, [RateLimitError("storm")] * 50)
    cerebras = FakeClient(ProviderName.CEREBRAS, [RateLimitError("storm")] * 50)
    hf = FakeClient(
        ProviderName.HUGGINGFACE,
        [
            make_response(
                provider=ProviderName.HUGGINGFACE,
                physical_model="meta-llama/Llama-3.3-70B-Instruct",
                text="hf-rescued",
            )
        ],
    )
    provider = make_provider(
        settings,
        {
            ProviderName.GROQ: groq,
            ProviderName.CEREBRAS: cerebras,
            ProviderName.HUGGINGFACE: hf,
        },
    )

    response = await provider.generate(ModelId.INTENT_PROFILER, _msgs())

    assert response.text == "hf-rescued"
    assert response.provider == ProviderName.HUGGINGFACE
    assert len(hf.calls) == 1


async def test_hf_chat_fallback_off_by_default(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    """Default (flag off): a Groq+Cerebras storm raises rather than touching HF."""
    groq = FakeClient(ProviderName.GROQ, [RateLimitError("storm")] * 50)
    cerebras = FakeClient(ProviderName.CEREBRAS, [RateLimitError("storm")] * 50)
    hf = FakeClient(ProviderName.HUGGINGFACE, [])  # raises if called
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
    assert hf.calls == []


def test_extract_openai_compatible_text_accepts_string_content() -> None:
    text = _extract_openai_compatible_text({"choices": [{"message": {"content": "hello"}}]})
    assert text == "hello"


def test_extract_openai_compatible_text_accepts_block_content() -> None:
    text = _extract_openai_compatible_text(
        {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"type": "output_text", "text": "hello "},
                            {"type": "output_text", "text": "world"},
                        ]
                    }
                }
            ]
        }
    )
    assert text == "hello world"


def test_extract_openai_compatible_text_falls_back_to_choice_text() -> None:
    text = _extract_openai_compatible_text({"choices": [{"text": "fallback"}]})
    assert text == "fallback"


def test_extract_openai_compatible_text_raises_on_missing_text() -> None:
    with pytest.raises(ProviderError):
        _extract_openai_compatible_text({"choices": [{"message": {}}]})


# ─── Reasoning models that spend the whole budget thinking ─────────────────


def test_extract_flags_length_truncation_distinctly() -> None:
    """finish_reason 'length' with no content is a budget problem, not a bad payload."""
    payload = {"choices": [{"finish_reason": "length", "message": {"reasoning": "thinking…"}}]}

    with pytest.raises(TruncatedReasoningError):
        _extract_openai_compatible_text(payload)


async def test_llm_retries_same_binding_with_double_the_budget(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    groq = FakeClient(
        ProviderName.GROQ,
        [
            TruncatedReasoningError("all reasoning, no answer"),
            make_response(provider=ProviderName.GROQ, text="answer-after-widening"),
        ],
    )
    provider = make_provider(tmp_settings, {ProviderName.GROQ: groq})

    response = await provider.generate(ModelId.INTENT_PROFILER, _msgs(), max_tokens=4096)

    assert response.text == "answer-after-widening"
    assert [c[2]["max_tokens"] for c in groq.calls] == [4096, 8192]


async def test_llm_falls_through_when_widening_does_not_help(tmp_settings) -> None:  # type: ignore[no-untyped-def]
    """Two truncations mean the model, not the budget — try the next binding."""
    groq = FakeClient(ProviderName.GROQ, [TruncatedReasoningError("thinking")] * 2)
    cerebras = FakeClient(
        ProviderName.CEREBRAS,
        [make_response(provider=ProviderName.CEREBRAS, text="fallback-ok")],
    )
    provider = make_provider(
        tmp_settings,
        {ProviderName.GROQ: groq, ProviderName.CEREBRAS: cerebras},
    )

    response = await provider.generate(ModelId.INTENT_PROFILER, _msgs(), max_tokens=1024)

    assert response.text == "fallback-ok"
    assert len(groq.calls) == 2, "one widened retry, then move on"
