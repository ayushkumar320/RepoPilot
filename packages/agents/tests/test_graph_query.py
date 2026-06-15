"""Tests for ``graph_query``: entry points, hubs, callers/callees, layers.

Exercises ``_adjacency.load_graph`` via the cache by pre-warming the cache,
which lets these tests run in the fast lane without a live Postgres.
"""

from __future__ import annotations

import networkx as nx
import pytest

from repopilot_agents.tools import _adjacency
from repopilot_agents.tools.graph_query import graph_query

REPO_ID = "test/repo@sha"


def _prime_cache() -> None:
    g: nx.DiGraph[str] = nx.DiGraph()
    g.add_node("m.a", kind="function")
    g.add_node("m.b", kind="function")
    g.add_node("m.c", kind="function")
    g.add_node("m.d", kind="function")
    # call edges: a -> b, a -> c, b -> c, d -> c (c is the hub; a, d entry-points)
    g.add_edge("m.a", "m.b", type="calls")
    g.add_edge("m.a", "m.c", type="calls")
    g.add_edge("m.b", "m.c", type="calls")
    g.add_edge("m.d", "m.c", type="calls")
    _adjacency._CACHE[REPO_ID] = g


@pytest.mark.asyncio
async def test_entry_points() -> None:
    _prime_cache()
    out = await graph_query("entry_points", engine=None, repo_id=REPO_ID)  # type: ignore[arg-type]
    syms = {r.symbol for r in out}
    assert syms == {"m.a", "m.d"}


@pytest.mark.asyncio
async def test_hubs_ranked_by_fan_in() -> None:
    _prime_cache()
    out = await graph_query("hubs", engine=None, repo_id=REPO_ID, top_n=2)  # type: ignore[arg-type]
    assert out[0].symbol == "m.c"
    assert out[0].score == 3.0  # in-degree of c


@pytest.mark.asyncio
async def test_callers_of_c() -> None:
    _prime_cache()
    out = await graph_query("callers", engine=None, repo_id=REPO_ID, symbol="m.c")  # type: ignore[arg-type]
    syms = {r.symbol for r in out}
    assert syms == {"m.a", "m.b", "m.d"}


@pytest.mark.asyncio
async def test_callees_of_a() -> None:
    _prime_cache()
    out = await graph_query("callees", engine=None, repo_id=REPO_ID, symbol="m.a")  # type: ignore[arg-type]
    syms = {r.symbol for r in out}
    assert syms == {"m.b", "m.c"}


@pytest.mark.asyncio
async def test_callers_requires_symbol() -> None:
    _prime_cache()
    with pytest.raises(ValueError):
        await graph_query("callers", engine=None, repo_id=REPO_ID)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_layers_returns_one_row_per_node() -> None:
    _prime_cache()
    out = await graph_query("layers", engine=None, repo_id=REPO_ID, top_n=10)  # type: ignore[arg-type]
    assert {r.symbol for r in out} == {"m.a", "m.b", "m.c", "m.d"}
