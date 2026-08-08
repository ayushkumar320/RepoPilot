"""End-to-end Q&A tests against fully stubbed dependencies.

We monkey-patch the three I/O tools (``vector_search``, ``graph_traverse``,
``read_chunks``) and the verifier, so the test runs in the fast lane without
Postgres. The control flow — hop budget, sufficiency loop,
hallucination short-circuit — is what we're actually exercising.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from repopilot_agents.qa import graph as qa_graph
from repopilot_agents.qa.graph import NOT_FOUND_SENTINEL, answer_question
from repopilot_agents.qa.query_spec import fallback_query_spec
from repopilot_agents.state import IntentProfile
from repopilot_agents.types import ChunkContent, ChunkHit, CodeRef, Path
from repopilot_core.settings import get_settings


def _ref(symbol: str, line: int = 1) -> CodeRef:
    return CodeRef(file_path=f"{symbol}.py", start_line=line, end_line=line + 5, symbol=symbol)


def _chunk(symbol: str, content: str) -> ChunkContent:
    return ChunkContent(ref=_ref(symbol), content=content, kind="function")


class _ScriptedProvider:
    """Returns canned text responses in queue order."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.call_count = 0

    async def generate(self, model: Any, messages: Any, **kwargs: Any) -> Any:
        self.call_count += 1
        if not self._responses:
            raise AssertionError("provider exhausted")
        text = self._responses.pop(0)

        class _R:
            pass

        r = _R()
        r.text = text  # type: ignore[attr-defined]
        return r

    async def embed(self, text: str, *, model: Any = None) -> Any:
        raise AssertionError("embed should be patched out in these tests")


@pytest.fixture(autouse=True)
def _patch_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_vector_search(question: str, **kw: Any) -> list[ChunkHit]:
        return [
            ChunkHit(ref=_ref("alpha"), distance=0.1, kind="function"),
            ChunkHit(ref=_ref("beta"), distance=0.2, kind="function"),
        ]

    # The Q&A graph calls hybrid_search by default (Phase 3); return the same
    # canned hits so the loop-logic tests stay retrieval-agnostic.
    async def fake_hybrid_search(question: str, **kw: Any) -> list[ChunkHit]:
        return await fake_vector_search(question, **kw)

    async def fake_read_chunks(refs: Any, **kw: Any) -> list[ChunkContent]:
        return [
            ChunkContent(
                ref=ref,
                content=f"def {ref.symbol}():\n    return 1\n",
                kind="function",
            )
            for ref in refs
        ]

    async def fake_graph_traverse(start: str, **kw: Any) -> list[Path]:
        return [Path(steps=[_ref(start), _ref("gamma")], edge_types=["calls"])]

    async def fake_verify_claims(claims: Any, **kw: Any) -> list[Any]:
        from repopilot_agents.verifier.grounding import VerifierVerdict, _VerifyResult

        out: list[Any] = []
        for c in claims:
            c.status = "verified"
            out.append(
                _VerifyResult(
                    claim=c,
                    verdict=VerifierVerdict(decision="supported", reason="ok"),
                )
            )
        return out

    monkeypatch.setattr(qa_graph, "vector_search", fake_vector_search)
    monkeypatch.setattr(qa_graph, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(qa_graph, "read_chunks", fake_read_chunks)
    monkeypatch.setattr(qa_graph, "graph_traverse", fake_graph_traverse)
    monkeypatch.setattr(qa_graph, "verify_claims", fake_verify_claims)

    async def fake_build_query_spec(question: str, **kw: Any) -> Any:
        return fallback_query_spec(question)

    monkeypatch.setattr(qa_graph, "build_query_spec", fake_build_query_spec)


@pytest.mark.asyncio
async def test_hallucination_short_circuit_returns_not_found_sentinel() -> None:
    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "I couldn't find that in the repo.",
        ]
    )
    result = await answer_question(
        "What is the unicorn module?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
    )
    assert result.answer == NOT_FOUND_SENTINEL
    assert result.claims == []


@pytest.mark.asyncio
async def test_grounded_answer_produces_verified_claims() -> None:
    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "alpha returns one. [0]\nbeta also returns one. [1]",
        ]
    )
    result = await answer_question(
        "What do alpha and beta return?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
    )
    assert "alpha returns one" in result.answer
    assert len(result.claims) == 2
    assert all(c.status == "verified" for c in result.claims)
    assert any(entry.startswith("hybrid_search:") for entry in result.retrieval_path)


@pytest.mark.asyncio
async def test_uncited_claim_is_unverified_and_skips_verifier() -> None:
    """A claim with no [N] citation must not be pinned to pool[0] and
    verified against it — it should come back "unverified" without ever
    reaching the verifier, and raise no objection."""
    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "alpha returns one. [0]\nbeta does something else entirely.",
        ]
    )
    result = await answer_question(
        "What do alpha and beta return?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
    )
    assert len(result.claims) == 2
    cited, uncited = result.claims
    assert cited.status == "verified"
    assert uncited.status == "unverified"
    assert uncited.verifier_note == qa_graph.UNCITED_CLAIM_REASON
    # Still schema-valid: refs non-empty, just not checked against them.
    assert uncited.refs
    assert result.objections == []


@pytest.mark.asyncio
async def test_section_headers_are_not_claims() -> None:
    """The structured answer format uses '## ' headers. They assert nothing,
    so they must never become claims or reach the verifier."""
    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "## How it works\nalpha returns one. [0]\n## Where to look next\nRead beta next. [1]",
        ]
    )
    result = await answer_question(
        "How does alpha work?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
    )
    assert [c.text for c in result.claims] == ["alpha returns one.", "Read beta next."]
    assert "## How it works" in result.answer


@pytest.mark.asyncio
async def test_detailed_answer_mentioning_missing_evidence_is_kept() -> None:
    """A long answer that says it couldn't find one thing is still an answer.

    Saying "I couldn't find a test for it" on one line must not collapse the
    whole reply down to the not-found sentinel.
    """
    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "alpha returns one. [0]\n"
            "I couldn't find a test covering the error path in these chunks. [1]",
        ]
    )
    result = await answer_question(
        "How does alpha work?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
    )
    assert result.answer != NOT_FOUND_SENTINEL
    assert len(result.claims) == 2


@pytest.mark.asyncio
async def test_stage_timings_are_recorded() -> None:
    """P1 instrumentation: every stage the run touched reports wall-clock."""
    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "alpha returns one. [0]",
        ]
    )
    result = await answer_question(
        "What does alpha return?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
    )
    timings = result.stage_timings_ms
    # Stages this path must have run.
    for stage in ("retrieval", "sufficiency", "answer", "verify"):
        assert stage in timings, f"{stage} not timed"
        assert timings[stage] >= 0.0
    # Stages it never reached stay absent rather than reporting a bogus 0.
    assert "expand" not in timings
    assert set(timings) <= set(qa_graph.STAGES)


@pytest.mark.asyncio
async def test_stage_timings_accumulate_across_hops() -> None:
    """sufficiency/expand run once per hop; their timings must sum, not overwrite."""
    provider = _ScriptedProvider(
        [
            '{"decision":"insufficient","reason":"more","next_symbol":"alpha"}',
            '{"decision":"insufficient","reason":"more","next_symbol":"beta"}',
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "alpha returns one. [0]",
        ]
    )
    result = await answer_question(
        "What does alpha return?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
    )
    assert result.hops == 2
    assert "expand" in result.stage_timings_ms


@pytest.mark.asyncio
async def test_hop_budget_enforced_at_three() -> None:
    insufficient = '{"decision":"insufficient","reason":"more needed","next_symbol":"alpha"}'
    provider = _ScriptedProvider(
        [
            insufficient,
            insufficient,
            insufficient,
            "final answer line one.",  # answer after exhausting hops
        ]
    )
    result = await answer_question(
        "trace alpha deeper",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
    )
    assert result.hops == 3
    # 3 sufficiency calls + 1 answer call = 4
    assert provider.call_count == 4


@pytest.mark.asyncio
async def test_empty_graph_expansion_stops_without_repeating(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def empty_graph_traverse(start: str, **kw: Any) -> list[Path]:
        return []

    monkeypatch.setattr(qa_graph, "graph_traverse", empty_graph_traverse)
    provider = _ScriptedProvider(
        [
            '{"decision":"insufficient","reason":"more needed","next_symbol":"tech_stack"}',
            "The repository uses TypeScript. [0]",
        ]
    )

    result = await answer_question(
        "what is the tech stack?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
    )

    assert result.hops == 0
    assert result.retrieval_path.count("graph_traverse:empty") == 1
    assert provider.call_count == 2


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_rerank_pool_size_comes_from_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """``Settings.rerank_max_pool`` must actually reach the rerank call.

    Regression test for dead config: until 2026-08-04 the QA path read
    ``rerank.pipeline.DEFAULT_MAX_POOL`` directly, so changing the setting
    silently did nothing and the pool was pinned at 50 regardless. Pool size
    is the dominant latency lever, so "the knob does nothing" was expensive.
    """
    seen: dict[str, object] = {}

    async def many_hits(question: str, **kw: Any) -> list[ChunkHit]:
        return [
            ChunkHit(ref=_ref(f"sym{i}", line=i + 1), distance=0.01 * i, kind="function")
            for i in range(40)
        ]

    def spy_rerank(
        query: str, hits: Any, contents: Any, **kw: Any
    ) -> list[tuple[ChunkHit, ChunkContent]]:
        seen["n_hits"] = len(hits)
        seen["max_pool"] = kw.get("max_pool")
        seen["lambda_"] = kw.get("lambda_")
        return list(zip(hits, contents, strict=True))[: kw.get("k", 8)]

    monkeypatch.setattr(qa_graph, "hybrid_search", many_hits)
    monkeypatch.setattr(qa_graph, "vector_search", many_hits)
    monkeypatch.setattr(qa_graph, "rerank_and_diversify", spy_rerank)
    base = get_settings()
    monkeypatch.setattr(
        qa_graph,
        "get_settings",
        lambda: base.model_copy(update={"rerank_max_pool": 12, "rerank_lambda": 0.5}),
    )

    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "sym0 returns one. [0]",
        ]
    )
    result = await answer_question(
        "What does sym0 return?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
        k=8,
        recall_k=50,
    )

    assert seen["n_hits"] == 12, "pool slice ignored settings.rerank_max_pool"
    assert seen["max_pool"] == 12
    assert seen["lambda_"] == 0.5, "settings.rerank_lambda ignored"
    assert "rerank:pool=12:k=8" in result.retrieval_path


@pytest.mark.asyncio
async def test_persona_priorities_unlock_the_paths_they_need(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A reader who asks about tests must be able to retrieve ``tests/``.

    The contributor persona's prompt demands the test that guards each edit
    site while the default recall lane excluded ``tests/`` as noise, so the
    answer could only hedge.
    """
    seen: dict[str, Any] = {}

    async def spy_search(question: str, **kw: Any) -> list[ChunkHit]:
        seen["exclude"] = list(kw.get("exclude_path_prefixes") or [])
        return [ChunkHit(ref=_ref("sym0", line=1), distance=0.1, kind="function")]

    monkeypatch.setattr(qa_graph, "hybrid_search", spy_search)
    monkeypatch.setattr(qa_graph, "vector_search", spy_search)

    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "sym0 returns one. [0]",
        ]
    )
    await answer_question(
        "What guards sym0?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
        intent_profile=IntentProfile(
            raw_text="first-time contributor preparing a pull request",
            focus_keywords=["tests", "contributing"],
        ),
    )

    assert "tests/" not in seen["exclude"]
    assert "docs/" not in seen["exclude"]
    # Priorities unlock only what they name — examples/ stays filtered out.
    assert "examples/" in seen["exclude"]


@pytest.mark.asyncio
async def test_reasoning_block_never_reaches_the_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``<think>`` output is the model's scratchpad, not part of the answer."""

    async def one_hit(question: str, **kw: Any) -> list[ChunkHit]:
        return [ChunkHit(ref=_ref("sym0", line=1), distance=0.1, kind="function")]

    monkeypatch.setattr(qa_graph, "hybrid_search", one_hit)
    monkeypatch.setattr(qa_graph, "vector_search", one_hit)

    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "<think>Thinking Process: restate the prompt, list constraints.</think>\n"
            "## How it works\nsym0 returns one. [0]",
        ]
    )
    result = await answer_question(
        "What does sym0 return?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
    )

    assert "<think>" not in result.answer
    assert "Thinking Process" not in result.answer
    assert result.answer.startswith("## How it works")


@pytest.mark.asyncio
async def test_rerank_failure_degrades_instead_of_killing_the_answer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A broken cross-encoder must cost ordering, not the whole answer.

    A wiped/partial ONNX cache raised out of ``rerank_and_diversify`` and took
    the question down to the API's keyword-only deterministic fallback.
    """

    async def many_hits(question: str, **kw: Any) -> list[ChunkHit]:
        return [
            ChunkHit(ref=_ref(f"sym{i}", line=i + 1), distance=0.01 * i, kind="function")
            for i in range(40)
        ]

    def boom(query: str, hits: Any, contents: Any, **kw: Any) -> list[Any]:
        raise RuntimeError("NO_SUCHFILE: model.onnx missing")

    monkeypatch.setattr(qa_graph, "hybrid_search", many_hits)
    monkeypatch.setattr(qa_graph, "vector_search", many_hits)
    monkeypatch.setattr(qa_graph, "rerank_and_diversify", boom)

    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "sym0 returns one. [0]",
        ]
    )
    result = await answer_question(
        "What does sym0 return?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
        k=8,
        recall_k=50,
    )

    assert "rerank_skipped:RuntimeError" in result.retrieval_path
    assert result.claims, "answer should still be produced without the reranker"


@pytest.mark.asyncio
async def test_compression_is_off_by_default_even_when_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """P2: ``use_compress=True`` alone must not compress while the flag is off.

    Phase 5 measured +5.6% token reduction against a -40% gate, so the default
    is off and ``compress_enabled`` is the single authority. A caller asking
    for compression gets none, and the retrieval path says so by omission.
    """
    called = False

    async def fake_compress_chunks(question: str, chunks: Any, **kw: Any) -> list[ChunkContent]:
        nonlocal called
        called = True
        return list(chunks)

    monkeypatch.setattr(qa_graph, "compress_chunks", fake_compress_chunks)
    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "alpha returns one.",
        ]
    )
    result = await answer_question(
        "What does alpha return?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
        use_compress=True,
    )
    assert not called, "compression ran despite compress_enabled being off"
    assert not any(step.startswith("compress:") for step in result.retrieval_path)


@pytest.mark.asyncio
async def test_compression_is_recorded_in_retrieval_path(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_compress_chunks(question: str, chunks: Any, **kw: Any) -> list[ChunkContent]:
        return [
            chunk.model_copy(
                update={"kept_line_spans": [(chunk.ref.start_line, chunk.ref.start_line)]}
            )
            for chunk in chunks
        ]

    monkeypatch.setattr(qa_graph, "compress_chunks", fake_compress_chunks)
    # ``compress_enabled`` defaults to off (Phase 5 measured +5.6% against a
    # -40% gate), so this test states the flag it exercises instead of
    # inheriting it -- otherwise flipping the default silently guts the test.
    base = get_settings()
    monkeypatch.setattr(
        qa_graph,
        "get_settings",
        lambda: base.model_copy(update={"compress_enabled": True}),
    )
    provider = _ScriptedProvider(
        [
            '{"decision":"sufficient","reason":"enough","next_symbol":""}',
            "alpha returns one.",
        ]
    )
    result = await answer_question(
        "What does alpha return?",
        engine=cast(Any, None),
        provider=cast(Any, provider),
        repo_id="repo",
        use_compress=True,
    )
    assert "compress:k=2" in result.retrieval_path
