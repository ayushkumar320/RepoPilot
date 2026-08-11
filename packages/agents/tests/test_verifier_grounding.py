"""Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, cast

import pytest

from repopilot_agents.types import ChunkContent, CodeRef
from repopilot_agents.verifier import grounding as grounding_mod
from repopilot_agents.verifier.grounding import (
    _MAX_PROMPT_CHARS,
    _SYSTEM_PROMPT,
    Claim,
    VerifierVerdict,
    _Cache,
    _fit_prompt_budget,
    _parse_verdict,
    _user_prompt,
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


def test_verifier_prompt_distinguishes_absence_scopes() -> None:
    """Chunk-scoped absence is checkable; repo-scoped absence is not."""
    assert "SUPPORTED when the chunks indeed do not contain it" in _SYSTEM_PROMPT
    assert "is REJECTED" in _SYSTEM_PROMPT


def test_user_prompt_truncates_a_single_oversized_chunk() -> None:
    """One AST node can be a whole class — selecting fewer chunks can't help."""
    claim = Claim(
        text="c",
        refs=[CodeRef(file_path="big.py", start_line=1, end_line=2)],
    )

    rendered = _user_prompt(claim, [_chunk("big", _MAX_PROMPT_CHARS * 2)])

    assert len(rendered) < _MAX_PROMPT_CHARS + 500
    assert "chunk truncated for prompt size" in rendered


def test_user_prompt_caps_the_total_across_many_chunks() -> None:
    chunks = [_chunk(f"c{i}", 15_000) for i in range(6)]
    claim = Claim(text="c", refs=[CodeRef(file_path="c0.py", start_line=1, end_line=2)])

    rendered = _user_prompt(claim, chunks)

    assert len(rendered) < _MAX_PROMPT_CHARS + 500


def test_cache_evicts_the_least_recently_used_entry() -> None:
    """The verdict cache is bounded — unbounded, it grew for the process's life."""
    cache = _Cache(max_entries=2)
    verdict = VerifierVerdict(decision="supported", reason="ok")

    cache.put("a", verdict)
    cache.put("b", verdict)
    assert cache.get("a") is not None  # touching "a" makes "b" the oldest
    cache.put("c", verdict)

    assert cache.get("b") is None
    assert cache.get("a") is not None
    assert cache.get("c") is not None


# ─── The recheck against the answerer's wider context ───────────────────────
#
# The commonest rejection is not an ungrounded claim — it is a true claim
# citing the wrong [N]. One recheck against the chunks the answerer actually
# had fixes that. It is also the only code that can turn a rejected claim into
# a displayed one, so each branch below is a way trust could be granted wrongly
# (or withheld wrongly) with nothing to notice.


class _ScriptedProvider:
    """Queues verdict payloads; an Exception in the queue is raised, not returned."""

    def __init__(self, responses: list[Any]) -> None:
        self._responses = list(responses)
        self.calls = 0

    async def generate(self, model: Any, messages: Any, **kwargs: Any) -> Any:
        self.calls += 1
        if not self._responses:
            raise AssertionError("_ScriptedProvider exhausted")
        head = self._responses.pop(0)
        if isinstance(head, Exception):
            raise head
        return _Stub(head)


@dataclass(slots=True)
class _Stub:
    text: str

    @property
    def total_tokens(self) -> int:
        return 0


def _verdict_json(decision: str, reason: str) -> str:
    return json.dumps({"decision": decision, "reason": reason})


@pytest.fixture
def _chunks_for_every_ref(monkeypatch: pytest.MonkeyPatch) -> None:
    """read_chunks returns one distinct chunk per ref, without a database."""

    async def fake_read_chunks(refs: Any, **_: Any) -> list[ChunkContent]:
        return [
            ChunkContent(ref=ref, content=f"# {ref.file_path}:{ref.start_line}\nbody\n")
            for ref in refs
        ]

    monkeypatch.setattr(grounding_mod, "read_chunks", fake_read_chunks)


def _cited() -> CodeRef:
    return CodeRef(file_path="pkg/cited.py", start_line=1, end_line=4, symbol="pkg.cited.fn")


def _elsewhere() -> CodeRef:
    return CodeRef(file_path="pkg/other.py", start_line=9, end_line=20, symbol="pkg.other.fn")


@pytest.mark.asyncio
async def test_recheck_upgrades_a_claim_supported_by_the_wider_context(
    _chunks_for_every_ref: None,
) -> None:
    claim = Claim(text="the client retries on 429", refs=[_cited()])
    provider = _ScriptedProvider(
        [
            _verdict_json("rejected", "the cited chunk does not mention retries"),
            _verdict_json("supported", "ignored — the recheck writes its own reason"),
        ]
    )

    result = await verify_claim(
        claim,
        provider=cast(Any, provider),
        engine=cast(Any, object()),
        repo_id="owner/name@sha",
        fallback_refs=[_elsewhere()],
    )

    assert provider.calls == 2
    assert result.verdict.decision == "supported"
    assert claim.status == "verified"
    assert claim.verifier_note == "verified against answer context"


@pytest.mark.asyncio
async def test_recheck_that_rejects_again_keeps_the_original_reason(
    _chunks_for_every_ref: None,
) -> None:
    """A second rejection changes nothing — and the reader sees the first reason."""
    claim = Claim(text="the client retries on 429", refs=[_cited()])
    provider = _ScriptedProvider(
        [
            _verdict_json("rejected", "the cited chunk does not mention retries"),
            _verdict_json("rejected", "nor does anything else here"),
        ]
    )

    await verify_claim(
        claim,
        provider=cast(Any, provider),
        engine=cast(Any, object()),
        repo_id="owner/name@sha",
        fallback_refs=[_elsewhere()],
    )

    assert provider.calls == 2
    assert claim.status == "rejected"
    assert claim.verifier_note == "the cited chunk does not mention retries"


@pytest.mark.asyncio
async def test_recheck_outage_leaves_the_first_verdict_standing(
    _chunks_for_every_ref: None,
) -> None:
    """A transient outage on the recheck must not upgrade a rejected claim."""
    claim = Claim(text="the client retries on 429", refs=[_cited()])
    provider = _ScriptedProvider(
        [
            _verdict_json("rejected", "not supported by the cited chunk"),
            ProviderError("every provider exhausted"),
        ]
    )

    await verify_claim(
        claim,
        provider=cast(Any, provider),
        engine=cast(Any, object()),
        repo_id="owner/name@sha",
        fallback_refs=[_elsewhere()],
    )

    assert claim.status == "rejected"
    assert claim.verifier_note == "not supported by the cited chunk"


@pytest.mark.asyncio
async def test_no_recheck_when_the_fallback_adds_nothing_new(
    _chunks_for_every_ref: None,
) -> None:
    """Re-asking with the identical context would spend a call to learn nothing."""
    claim = Claim(text="the client retries on 429", refs=[_cited()])
    provider = _ScriptedProvider([_verdict_json("rejected", "not in the cited chunk")])

    await verify_claim(
        claim,
        provider=cast(Any, provider),
        engine=cast(Any, object()),
        repo_id="owner/name@sha",
        fallback_refs=[_cited()],
    )

    assert provider.calls == 1
    assert claim.status == "rejected"
