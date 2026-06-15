"""Shared loader/cache for the per-repo NetworkX graph.

Per Phase 2 decision **D5**: the adjacency JSONB sidecar (written by Phase 1
into ``graph_adjacency``) is rebuilt into ``nx.DiGraph`` once per repo and
cached in-process. Rebuild is ~20 ms for a 50 kLOC repo so it's cheap, but
doing it per call would still waste work across a single Q&A run (which can
issue many ``graph_query`` / ``graph_traverse`` calls).

The cache is keyed by ``repo_id`` only — Phase 1's idempotency on
``(repo_url, head_sha)`` already encodes the snapshot identity in that key.
"""

from __future__ import annotations

import networkx as nx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_ingestion.db import graph_adjacency as graph_table

log = structlog.get_logger(__name__)

_CACHE: dict[str, nx.DiGraph[str]] = {}


async def load_graph(*, engine: AsyncEngine, repo_id: str) -> nx.DiGraph[str]:
    """Return the cached NetworkX graph for ``repo_id``; build it on miss."""
    cached = _CACHE.get(repo_id)
    if cached is not None:
        return cached

    async with engine.connect() as conn:
        row = (
            await conn.execute(
                select(graph_table.c.adjacency).where(graph_table.c.repo_id == repo_id)
            )
        ).first()

    if row is None:
        raise LookupError(f"no graph_adjacency row for repo_id={repo_id!r}")

    adjacency = row[0]
    graph: nx.DiGraph[str] = nx.DiGraph()
    for node, buckets in adjacency.items():
        graph.add_node(node)
        for target in buckets.get("calls", []):
            graph.add_edge(node, target, type="calls")
        for target in buckets.get("imports", []):
            graph.add_edge(node, target, type="imports")
        for target in buckets.get("inherits", []):
            graph.add_edge(node, target, type="inherits")

    log.debug(
        "adjacency.loaded",
        repo_id=repo_id,
        nodes=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
    )
    _CACHE[repo_id] = graph
    return graph


def invalidate(repo_id: str) -> None:
    """Drop the cached graph for ``repo_id``. Call when re-indexing."""
    _CACHE.pop(repo_id, None)


def reset_cache() -> None:
    """Test helper — clear all cached graphs."""
    _CACHE.clear()


__all__ = ["invalidate", "load_graph", "reset_cache"]
