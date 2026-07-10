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
from repopilot_agents.types import ChunkContent, ChunkHit, CodeRef, Path


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

    # Keep the fast lane hermetic: attribution normally loads the ONNX
    # reranker; stub it with the same top-2 shape.
    def fake_attribute_refs(text: str, pool: Any, *, k: int = 2, **kw: Any) -> list[Any]:
        return [c.ref for c in list(pool)[:k]]

    monkeypatch.setattr(qa_graph, "attribute_refs", fake_attribute_refs)
    monkeypatch.setattr(qa_graph, "vector_search", fake_vector_search)
    monkeypatch.setattr(qa_graph, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(qa_graph, "read_chunks", fake_read_chunks)
    monkeypatch.setattr(qa_graph, "graph_traverse", fake_graph_traverse)
    monkeypatch.setattr(qa_graph, "verify_claims", fake_verify_claims)


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
            "alpha returns one.\nbeta also returns one.",
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
    assert result.retrieval_path[0].startswith("hybrid_search:")


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
async def test_compression_is_recorded_in_retrieval_path(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_compress_chunks(question: str, chunks: Any, **kw: Any) -> list[ChunkContent]:
        return [
            chunk.model_copy(
                update={"kept_line_spans": [(chunk.ref.start_line, chunk.ref.start_line)]}
            )
            for chunk in chunks
        ]

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
    assert "compress:k=2" in result.retrieval_path
