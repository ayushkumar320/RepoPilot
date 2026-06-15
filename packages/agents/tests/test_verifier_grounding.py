"""Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)."""

from __future__ import annotations

from typing import Any, cast

import pytest

from repopilot_agents.types import ChunkContent, CodeRef
from repopilot_agents.verifier.grounding import (
    Claim,
    _parse_verdict,
    verify_claim,
    verify_claims,
)


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
