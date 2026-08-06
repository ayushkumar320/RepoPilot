"""Fast-lane tests for how the query spec reaches retrieval."""

from __future__ import annotations

from typing import Any, cast

import pytest

from repopilot_agents.qa import graph as qa_graph
from repopilot_agents.qa.query_spec import QuerySpec
from repopilot_agents.types import ChunkHit, CodeRef


def _hit(symbol: str, distance: float) -> ChunkHit:
    return ChunkHit(
        ref=CodeRef(file_path=f"{symbol}.py", start_line=1, end_line=5, symbol=symbol),
        distance=distance,
        kind="function",
    )


@pytest.mark.asyncio
async def test_query_spec_feeds_the_sparse_lane_not_a_dense_fan_out(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The dense lane sees the raw question and nothing else.

    Fanning dense retrieval out over paraphrases and fusing the pools is what
    cost Phase 2 its recall (httpx 0.949 -> 0.817). The spec's identifiers are
    still used — appended to the BM25 query, where they can only add matches.
    """
    seen: list[dict[str, Any]] = []

    async def fake_build_query_spec(question: str, **kw: Any) -> QuerySpec:
        return QuerySpec(
            raw_text=question,
            rewrites=["lexical redirect method", "location header flow"],
            extracted_symbols=["Client.send", "max_redirects"],
            intent_class="procedural",
            needs_multi_hop=True,
        )

    async def fake_hybrid_search(query: str, **kw: Any) -> list[ChunkHit]:
        seen.append({"query": query, "sparse_query": kw.get("sparse_query")})
        return [_hit("alpha", 0.1)]

    monkeypatch.setattr(qa_graph, "build_query_spec", fake_build_query_spec)
    monkeypatch.setattr(qa_graph, "hybrid_search", fake_hybrid_search)

    path: list[str] = []
    hits = await qa_graph._initial_retrieval(
        "How are redirects handled?",
        engine=cast(Any, None),
        provider=cast(Any, None),
        repo_id="repo",
        k=8,
        recall_k=50,
        exclude_path_prefixes=(),
        use_hybrid=True,
        use_query_understanding=True,
        retrieval_path=path,
    )

    assert len(seen) == 1, "one retrieval, no paraphrase fan-out"
    assert seen[0]["query"] == "How are redirects handled?"
    assert seen[0]["sparse_query"] == "How are redirects handled? Client.send max_redirects"
    assert [hit.ref.symbol for hit in hits] == ["alpha"]
    assert path[0].startswith("query_spec:symbols=2")


@pytest.mark.asyncio
async def test_initial_retrieval_applies_single_extracted_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_prefixes: list[str | None] = []

    async def fake_build_query_spec(question: str, **kw: Any) -> QuerySpec:
        return QuerySpec(
            raw_text=question,
            extracted_paths=["src/httpx/_client.py"],
            intent_class="where_is",
        )

    async def fake_vector_search(query: str, **kw: Any) -> list[ChunkHit]:
        seen_prefixes.append(kw["path_prefix"])
        return [_hit("client", 0.1)]

    monkeypatch.setattr(qa_graph, "build_query_spec", fake_build_query_spec)
    monkeypatch.setattr(qa_graph, "vector_search", fake_vector_search)

    hits = await qa_graph._initial_retrieval(
        "Where is the client?",
        engine=cast(Any, None),
        provider=cast(Any, None),
        repo_id="repo",
        k=8,
        recall_k=None,
        exclude_path_prefixes=(),
        use_hybrid=False,
        use_query_understanding=True,
        retrieval_path=[],
    )

    assert [hit.ref.symbol for hit in hits] == ["client"]
    assert seen_prefixes == ["src/httpx/_client.py"]
