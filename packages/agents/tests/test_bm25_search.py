"""RAG Phase 3: ``bm25_search`` SQL composition + param plumbing.

The Postgres FTS execution stays in the slow/integration lane; here we test
the pure SQL composition (``build_bm25_sql``), the bound parameters, and the
empty-query short-circuit — via a stub connection that records what would hit
Postgres. Mirrors ``test_vector_search_filters.py``.
"""

from __future__ import annotations

from typing import Any

import pytest

from repopilot_agents.tools.bm25_search import bm25_search, build_bm25_sql, clean_query


def test_clean_query_strips_stopwords_keeps_identifiers() -> None:
    assert clean_query("Where is the GZipDecoder class defined?") == "GZipDecoder class defined"
    # Identifiers with underscores survive intact.
    assert clean_query("how does handle_async_request work") == "handle_async_request work"
    # All-stopword query collapses to empty (→ bm25_search short-circuits).
    assert clean_query("where is the") == ""


def test_default_sql_uses_simple_analyzer_and_repo_filter() -> None:
    sql = build_bm25_sql(kind=None, path_prefix=None, exclude_path_prefixes=())
    assert "plainto_tsquery('simple', :q)" in sql
    # OR-semantics: '&' rewritten to '|' so any term can match (not all).
    assert "replace(plainto_tsquery('simple', :q)::text, '&', '|')::tsquery" in sql
    assert "c.content_tsv @@ " in sql
    assert "c.repo_id = :repo_id" in sql
    # Field-weighted ranking: {D,C,B,A} array favouring band A (the symbol).
    assert "ts_rank_cd('{0.1, 0.2, 0.4, 1.0}', c.content_tsv" in sql
    assert "c.kind = :kind" not in sql
    assert "NOT LIKE" not in sql


def test_filters_compose() -> None:
    sql = build_bm25_sql(
        kind="function",
        path_prefix="httpx/",
        exclude_path_prefixes=("tests/", "docs/"),
    )
    assert "c.kind = :kind" in sql
    assert "c.file_path LIKE :path_prefix || '%'" in sql
    assert sql.count("NOT LIKE") == 2
    assert ":exclude_0" in sql and ":exclude_1" in sql


class _RecordingConn:
    def __init__(self, log: dict[str, Any]) -> None:
        self._log = log

    async def execute(self, sql: Any, params: dict[str, Any]) -> Any:
        self._log["sql"] = str(sql)
        self._log["params"] = params

        class _Result:
            @staticmethod
            def all() -> list[Any]:
                return []

        return _Result()

    async def __aenter__(self) -> _RecordingConn:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None


class _RecordingEngine:
    def __init__(self) -> None:
        self.log: dict[str, Any] = {}

    def connect(self) -> _RecordingConn:
        return _RecordingConn(self.log)


@pytest.mark.asyncio
async def test_query_and_filters_are_bound_not_inlined() -> None:
    engine = _RecordingEngine()
    await bm25_search(
        "HTTPTransport handle_request",
        engine=engine,  # type: ignore[arg-type]
        repo_id="r1",
        k=50,
        kind="function",
        exclude_path_prefixes=("tests/",),
    )
    params = engine.log["params"]
    assert params["q"] == "HTTPTransport handle_request"
    assert params["repo_id"] == "r1"
    assert params["k"] == 50
    assert params["kind"] == "function"
    assert params["exclude_0"] == "tests/"
    # The query text must never be spliced into the SQL string itself.
    assert "HTTPTransport" not in engine.log["sql"]


@pytest.mark.asyncio
async def test_blank_query_and_zero_k_short_circuit() -> None:
    engine = _RecordingEngine()
    assert await bm25_search("   ", engine=engine, repo_id="r1") == []  # type: ignore[arg-type]
    assert await bm25_search("q", engine=engine, repo_id="r1", k=0) == []  # type: ignore[arg-type]
    assert engine.log == {}
