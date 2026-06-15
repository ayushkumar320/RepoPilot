"""``graph_query`` — structural queries against the per-repo NetworkX graph.

Five query kinds (the only kinds the agents need):

* ``entry_points`` — module-level functions with in-degree 0 in the call
  graph. These are the natural "where do I start reading?" nodes.
* ``hubs``         — top-N nodes by total fan-in. The mental-model anchors.
* ``layers``       — Louvain community detection over the undirected
  projection. Returns one row per node tagged with its community id.
* ``callers``      — reverse-graph neighbours of ``symbol``.
* ``callees``      — forward-graph neighbours of ``symbol``.

All five run off the cached graph from ``_adjacency.load_graph`` so they
share work across one Q&A run.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

import networkx as nx
import structlog
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.tools._adjacency import load_graph
from repopilot_agents.types import GraphQueryResult

log = structlog.get_logger(__name__)


QueryKind = Literal["entry_points", "hubs", "layers", "callers", "callees"]


async def graph_query(
    kind: QueryKind,
    *,
    engine: AsyncEngine,
    repo_id: str,
    symbol: str | None = None,
    top_n: int = 20,
) -> list[GraphQueryResult]:
    """Run one of the five structural queries against the cached graph."""
    graph = await load_graph(engine=engine, repo_id=repo_id)

    if kind == "entry_points":
        return _entry_points(graph, top_n=top_n)
    if kind == "hubs":
        return _hubs(graph, top_n=top_n)
    if kind == "layers":
        return _layers(graph, top_n=top_n)
    if kind == "callers":
        if symbol is None:
            raise ValueError("callers requires symbol=")
        return _neighbours(graph, symbol, direction="in")
    if kind == "callees":
        if symbol is None:
            raise ValueError("callees requires symbol=")
        return _neighbours(graph, symbol, direction="out")
    raise ValueError(f"unknown query kind: {kind!r}")  # pragma: no cover


# ── internals ───────────────────────────────────────────────────────────────


def _call_subgraph(graph: nx.DiGraph[str]) -> nx.DiGraph[str]:
    keep = [(u, v) for u, v, d in graph.edges(data=True) if d.get("type") == "calls"]
    sub: nx.DiGraph[str] = nx.DiGraph()
    sub.add_nodes_from(graph.nodes(data=True))
    sub.add_edges_from((u, v, {"type": "calls"}) for u, v in keep)
    return sub


def _entry_points(graph: nx.DiGraph[str], *, top_n: int) -> list[GraphQueryResult]:
    sub = _call_subgraph(graph)
    out: list[GraphQueryResult] = []
    for node in sub.nodes:
        if sub.in_degree(node) == 0 and sub.out_degree(node) > 0:
            out.append(GraphQueryResult(symbol=node, kind="function", score=0.0))
    # Stable order so test snapshots don't flap.
    out.sort(key=lambda r: r.symbol)
    return out[:top_n]


def _hubs(graph: nx.DiGraph[str], *, top_n: int) -> list[GraphQueryResult]:
    sub = _call_subgraph(graph)
    scored: list[tuple[str, int]] = sorted(
        ((n, sub.in_degree(n)) for n in sub.nodes if sub.in_degree(n) > 0),
        key=lambda t: (-t[1], t[0]),
    )
    return [
        GraphQueryResult(symbol=n, kind="function", score=float(deg)) for n, deg in scored[:top_n]
    ]


def _layers(graph: nx.DiGraph[str], *, top_n: int) -> list[GraphQueryResult]:
    if graph.number_of_nodes() == 0:
        return []
    undirected = graph.to_undirected()
    try:
        communities: Iterable[set[str]] = nx.community.louvain_communities(undirected, seed=0)
    except Exception as exc:  # pragma: no cover — defensive
        log.warning("graph_query.louvain_failed", error=str(exc))
        return []
    out: list[GraphQueryResult] = []
    for cid, members in enumerate(communities):
        for member in members:
            out.append(GraphQueryResult(symbol=member, kind="function", score=float(cid)))
    out.sort(key=lambda r: (r.score, r.symbol))
    return out[:top_n]


def _neighbours(
    graph: nx.DiGraph[str], symbol: str, *, direction: Literal["in", "out"]
) -> list[GraphQueryResult]:
    if symbol not in graph:
        return []
    iter_fn = graph.predecessors if direction == "in" else graph.successors
    out: list[GraphQueryResult] = []
    for neighbour in iter_fn(symbol):
        edge = (
            graph.get_edge_data(neighbour, symbol)
            if direction == "in"
            else graph.get_edge_data(symbol, neighbour)
        )
        out.append(
            GraphQueryResult(
                symbol=neighbour,
                kind="function",
                score=0.0,
                metadata={"edge_type": str((edge or {}).get("type", ""))},
            )
        )
    out.sort(key=lambda r: r.symbol)
    return out


__all__ = ["QueryKind", "graph_query"]
