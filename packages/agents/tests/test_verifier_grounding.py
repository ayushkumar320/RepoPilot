"""Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)."""

from __future__ import annotations

from typing import Any, cast

import pytest

from repopilot_agents.types import ChunkContent, CodeRef
from repopilot_agents.verifier.grounding import (
    _MAX_PROMPT_CHARS,
    Claim,
    _fit_prompt_budget,
    _parse_verdict,
    verify_claim,
    verify_claims,
)
from repopilot_core.llm.provider import ProviderError


def test_parse_verdict_accepts_clean_json() -> None:
    v = _parse_verdict('{"decision":"supported","reason":"matches line 12"}')
    assert v is not None
    assert v.decision == "supported"


def test_parse_verdict_extracts_json_from_prose() -> None:
    v = _parse_verdict('Sure! {"decision":"rejected","reason":"no overlap"} done')
    assert v is not None
    assert v.decision == "rejected"


def test_parse_verdict_returns_none_on_garbage() -> None:
    assert _parse_verdict("definitely not JSON") is None


def test_parse_verdict_returns_none_on_invalid_decision() -> None:
    assert _parse_verdict('{"decision":"yes","reason":"x"}') is None


def test_parse_verdict_strips_closed_think_block() -> None:
    raw = (
        "<think>The claim says foo calls bar. Chunk shows `return bar()`. "
        "That is supported.</think>\n"
        '{"decision":"supported","reason":"return bar() present"}'
    )
    v = _parse_verdict(raw)
    assert v is not None
    assert v.decision == "supported"


def test_parse_verdict_survives_unclosed_think_when_json_precedes() -> None:
    # Some models emit the answer, then keep thinking without closing the tag.
    raw = '{"decision":"rejected","reason":"no overlap"}\n<think>wait, maybe'
    v = _parse_verdict(raw)
    assert v is not None
    assert v.decision == "rejected"


def test_parse_verdict_ignores_decoy_json_without_decision() -> None:
    raw = '{"note":"scratchpad"} then the real answer {"decision":"supported","reason":"line 3"}'
    v = _parse_verdict(raw)
    assert v is not None
    assert v.decision == "supported"


def test_parse_verdict_returns_none_when_only_think_block() -> None:
    # Budget exhausted inside reasoning — no JSON ever emitted → parse-fail.
    assert _parse_verdict("<think>still reasoning about the claim") is None


class _StubProvider:
    def __init__(self, raw_text: str) -> None:
        self.raw_text = raw_text
        self.call_count = 0

    async def generate(self, model: Any, messages: Any, **kwargs: Any) -> Any:
        self.call_count += 1

        class _R:
            text = self.raw_text

        return _R()


class _StubEngine:
    pass


@pytest.mark.asyncio
async def test_verify_claims_bounds_concurrency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The semaphore must cap in-flight verifier calls at max_concurrency."""
    import asyncio

    from repopilot_agents.verifier import grounding as g

    async def fake_read_chunks(refs: Any, *, engine: Any, repo_id: str) -> list[ChunkContent]:
        return [ChunkContent(ref=CodeRef(file_path="x.py", start_line=1, end_line=2), content="c")]

    monkeypatch.setattr(g, "read_chunks", fake_read_chunks)

    in_flight = 0
    peak = 0

    class _SlowProvider:
        async def generate(self, model: Any, messages: Any, **kwargs: Any) -> Any:
            nonlocal in_flight, peak
            in_flight += 1
            peak = max(peak, in_flight)
            await asyncio.sleep(0.01)
            in_flight -= 1

            class _R:
                text = '{"decision":"supported","reason":"ok"}'

            return _R()

    # Distinct refs so the verdict cache never collapses the calls.
    claims = [
        Claim(text=f"claim {i}", refs=[CodeRef(file_path=f"f{i}.py", start_line=1, end_line=2)])
        for i in range(10)
    ]
    await verify_claims(
        claims,
        provider=cast(Any, _SlowProvider()),
        engine=cast(Any, _StubEngine()),
        repo_id="r",
        max_concurrency=3,
    )
    assert peak <= 3


@pytest.mark.asyncio
async def test_verify_claim_rejects_when_refs_have_no_chunks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_read_chunks(refs: Any, *, engine: Any, repo_id: str) -> list[ChunkContent]:
        return []

    from repopilot_agents.verifier import grounding as g

    monkeypatch.setattr(g, "read_chunks", fake_read_chunks)
    provider = _StubProvider('{"decision":"supported","reason":"x"}')
    claim = Claim(
        text="foo calls bar",
        refs=[CodeRef(file_path="x.py", start_line=1, end_line=2)],
    )
    result = await verify_claim(
        claim,
        provider=cast(Any, provider),
        engine=cast(Any, _StubEngine()),
        repo_id="repo",
    )
    assert result.verdict.decision == "rejected"
    assert claim.status == "rejected"
    assert provider.call_count == 0  # short-circuit; no LLM call


@pytest.mark.asyncio
async def test_verify_claim_parse_fail_rejects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_read_chunks(refs: Any, *, engine: Any, repo_id: str) -> list[ChunkContent]:
        return [
            ChunkContent(
                ref=CodeRef(file_path="x.py", start_line=1, end_line=2),
                content="def foo(): return bar()",
            )
        ]

    from repopilot_agents.verifier import grounding as g

    monkeypatch.setattr(g, "read_chunks", fake_read_chunks)
    provider = _StubProvider("nonsense response with no JSON")
    claim = Claim(
        text="foo calls bar",
        refs=[CodeRef(file_path="x.py", start_line=1, end_line=2)],
    )
    result = await verify_claim(
        claim,
        provider=cast(Any, provider),
        engine=cast(Any, _StubEngine()),
        repo_id="repo",
    )
    assert result.verdict.decision == "rejected"
    assert result.verdict.reason == "verifier_parse_error"
    assert claim.status == "rejected"


@pytest.mark.asyncio
async def test_verify_claim_provider_error_marks_unverified_not_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_read_chunks(refs: Any, *, engine: Any, repo_id: str) -> list[ChunkContent]:
        return [
            ChunkContent(
                ref=CodeRef(file_path="x.py", start_line=1, end_line=2),
                content="def foo(): return bar()",
            )
        ]

    from repopilot_agents.verifier import grounding as g

    monkeypatch.setattr(g, "read_chunks", fake_read_chunks)

    class _FailingProvider:
        async def generate(self, model: Any, messages: Any, **kwargs: Any) -> Any:
            raise ProviderError(
                "all providers failed for verifier: RateLimitError('cerebras returned 429')"
            )

    claim = Claim(
        text="foo calls bar",
        refs=[CodeRef(file_path="x.py", start_line=1, end_line=2)],
    )
    result = await verify_claim(
        claim,
        provider=cast(Any, _FailingProvider()),
        engine=cast(Any, _StubEngine()),
        repo_id="repo",
    )
    assert result.verdict.decision == "rejected"
    assert result.verdict.reason == "verifier_provider_error"
    # A provider outage is transient infra, not a grounding failure: the claim
    # is marked "unverified" (retryable), NOT "rejected"/"flagged".
    assert claim.status == "unverified"
    assert result.objection is None


@pytest.mark.asyncio
async def test_verify_claims_cache_hit_skips_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_read_chunks(refs: Any, *, engine: Any, repo_id: str) -> list[ChunkContent]:
        return [
            ChunkContent(
                ref=CodeRef(file_path="x.py", start_line=1, end_line=2),
                content="def foo(): return bar()",
            )
        ]

    from repopilot_agents.verifier import grounding as g

    monkeypatch.setattr(g, "read_chunks", fake_read_chunks)
    provider = _StubProvider('{"decision":"supported","reason":"line 1 shows it"}')
    claim1 = Claim(
        text="foo calls bar",
        refs=[CodeRef(file_path="x.py", start_line=1, end_line=2)],
    )
    claim2 = Claim(
        text="foo calls bar",
        refs=[CodeRef(file_path="x.py", start_line=1, end_line=2)],
    )
    results = await verify_claims(
        [claim1, claim2],
        provider=cast(Any, provider),
        engine=cast(Any, _StubEngine()),
        repo_id="r",
    )
    assert provider.call_count == 1  # second call hit the cache
    assert results[0].verdict.decision == "supported"
    assert results[1].cached


@pytest.mark.asyncio
async def test_verify_claim_uses_full_chunk_content_even_when_compressed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    full_content = "line 1 keep\nline 2 contradicting detail\nline 3 keep"

    async def fake_read_chunks(refs: Any, *, engine: Any, repo_id: str) -> list[ChunkContent]:
        return [
            ChunkContent(
                ref=CodeRef(file_path="x.py", start_line=1, end_line=3),
                content=full_content,
                kept_line_spans=[(1, 1), (3, 3)],
            )
        ]

    from repopilot_agents.verifier import grounding as g

    monkeypatch.setattr(g, "read_chunks", fake_read_chunks)

    class _InspectProvider:
        async def generate(self, model: Any, messages: Any, **kwargs: Any) -> Any:
            user_text = messages[1].content
            assert "line 2 contradicting detail" in user_text
            assert "<source file=x.py:1-3" in user_text

            class _R:
                text = '{"decision":"supported","reason":"ok"}'

            return _R()

    claim = Claim(
        text="foo calls bar",
        refs=[CodeRef(file_path="x.py", start_line=1, end_line=3)],
    )
    result = await verify_claim(
        claim,
        provider=cast(Any, _InspectProvider()),
        engine=cast(Any, _StubEngine()),
        repo_id="repo",
    )
    assert result.verdict.decision == "supported"


def _chunk(name: str, size: int) -> ChunkContent:
    return ChunkContent(
        ref=CodeRef(file_path=f"{name}.py", start_line=1, end_line=2),
        content="x" * size,
    )


def test_fit_prompt_budget_drops_extras_that_would_overflow() -> None:
    """A 413 from an oversized body costs a wasted call and a failover."""
    cited = [_chunk("cited", 30_000)]
    extra = [_chunk("small", 5_000), _chunk("huge", 50_000), _chunk("late", 1_000)]

    fitted = _fit_prompt_budget(cited, extra)

    assert [c.ref.file_path for c in fitted] == ["cited.py", "small.py"]
    assert sum(len(c.content) for c in fitted) <= _MAX_PROMPT_CHARS


def test_fit_prompt_budget_always_keeps_cited_chunks() -> None:
    cited = [_chunk("cited", _MAX_PROMPT_CHARS + 1)]

    assert _fit_prompt_budget(cited, [_chunk("extra", 10)]) == cited
