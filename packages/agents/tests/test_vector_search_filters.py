"""RAG Phase 1: ``vector_search`` pool widening + metadata filters.

The pgvector SQL itself stays in the slow/integration lane (see conftest);
here we test the pure SQL composition (``build_search_sql``), the bind
parameters actually sent, and the ``recall_k`` / ``k`` semantics — via a
stub connection that records what would hit Postgres.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from repopilot_agents.tools.vector_search import (
    NON_SOURCE_PATH_PREFIXES,
    build_search_sql,
    vector_search,
)

# ── build_search_sql (pure) ─────────────────────────────────────────────────


def test_default_sql_filters_only_by_repo() -> None:
    sql = build_search_sql(kind=None, path_prefix=None, path_glob=None, exclude_path_prefixes=())
    assert "c.repo_id = :repo_id" in sql
    assert "c.kind = :kind" not in sql
    assert "LIKE :path_prefix" not in sql
    assert "SIMILAR TO" not in sql
    assert "NOT LIKE" not in sql
    assert "LIMIT :limit" in sql


def test_kind_and_path_filters_compose() -> None:
    sql = build_search_sql(
        kind="function",
        path_prefix="httpx/_transports/",
        path_glob="%(_api|_client)%.py",
        exclude_path_prefixes=(),
    )
    assert "c.kind = :kind" in sql
    assert "c.file_path LIKE :path_prefix || '%'" in sql
    assert "c.file_path SIMILAR TO :path_glob" in sql


def test_exclude_prefixes_render_one_clause_each() -> None:
    sql = build_search_sql(
        kind=None,
        path_prefix=None,
        path_glob=None,
        exclude_path_prefixes=NON_SOURCE_PATH_PREFIXES,
    )
    assert sql.count("NOT LIKE") == len(NON_SOURCE_PATH_PREFIXES)
    for i in range(len(NON_SOURCE_PATH_PREFIXES)):
        assert f":exclude_{i}" in sql


def test_non_source_prefixes_match_labeling_noise_filter() -> None:
    # Mirror of evals/tools/propose_labels.py — gold labels are source-only.
    assert NON_SOURCE_PATH_PREFIXES == ("tests/", "examples/", "docs/", "docs_src/", "scripts/")


# ── vector_search parameter plumbing (stub connection) ─────────────────────


@dataclass
class _StubEmbedding:
    vector: list[float]


class _StubProvider:
    async def embed(self, text: str) -> _StubEmbedding:
        return _StubEmbedding(vector=[0.1, 0.2])


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


async def _run(**kwargs: Any) -> dict[str, Any]:
    engine = _RecordingEngine()
    await vector_search(
        "how are redirects handled?",
        engine=engine,  # type: ignore[arg-type]
        provider=_StubProvider(),  # type: ignore[arg-type]
        repo_id="r1",
        **kwargs,
    )
    return engine.log


@pytest.mark.asyncio
async def test_default_limit_is_k() -> None:
    log = await _run()
    assert log["params"]["limit"] == 8


@pytest.mark.asyncio
async def test_recall_k_overrides_k_for_pool_size() -> None:
    log = await _run(k=8, recall_k=50)
    assert log["params"]["limit"] == 50


@pytest.mark.asyncio
async def test_filter_params_are_bound_not_inlined() -> None:
    log = await _run(
        kind="function",
        path_prefix="httpx/",
        exclude_path_prefixes=("tests/", "docs/"),
    )
    params = log["params"]
    assert params["kind"] == "function"
    assert params["path_prefix"] == "httpx/"
    assert params["exclude_0"] == "tests/"
    assert params["exclude_1"] == "docs/"
    # No filter value may be spliced into the SQL text itself.
    assert "tests/" not in log["sql"]
    assert "function" not in log["sql"].replace("c.kind = :kind", "")


@pytest.mark.asyncio
async def test_empty_query_and_zero_limit_short_circuit() -> None:
    engine = _RecordingEngine()
    provider = _StubProvider()
    assert (
        await vector_search(
            "  ",
            engine=engine,  # type: ignore[arg-type]
            provider=provider,  # type: ignore[arg-type]
            repo_id="r1",
        )
        == []
    )
    assert (
        await vector_search(
            "q",
            engine=engine,  # type: ignore[arg-type]
            provider=provider,  # type: ignore[arg-type]
            repo_id="r1",
            recall_k=0,
        )
        == []
    )
    assert engine.log == {}
