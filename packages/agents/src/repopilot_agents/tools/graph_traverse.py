"""``graph_traverse`` — BFS over the per-repo dependency graph.

The "complete-the-context" half of hybrid retrieval. Given a start symbol and
a set of edge types, walks the graph up to ``max_depth`` and returns the full
set of paths. Each ``Path.steps`` is an ordered list of ``CodeRef``s; line
spans on those refs are populated by a chunk lookup so the Q&A node can hand
the paths straight to ``read_chunks``.

Hop budget defaults to 3, which matches the Q&A subgraph's outer-loop budget
in ``docs/03_ARCHITECTURE.md``: any single traversal is bounded so the
sufficiency judge always converges.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence

import structlog
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.tools._adjacency import load_graph
from repopilot_agents.types import CodeRef, Path
from repopilot_ingestion.db import chunks as chunks_table

log = structlog.get_logger(__name__)


async def graph_traverse(
    start: str,
    *,
    engine: AsyncEngine,
    repo_id: str,
    edge_types: Sequence[str] = ("calls",),
    max_depth: int = 3,
) -> list[Path]:
    """BFS from ``start`` along the requested edge types; return all paths up to depth."""
    if max_depth <= 0:
        return []
    graph = await load_graph(engine=engine, repo_id=repo_id)
    if start not in graph:
        log.debug("graph_traverse.unknown_start", start=start)
        return []

    allowed = set(edge_types)
    paths: list[list[str]] = []
    queue: deque[list[str]] = deque([[start]])

    while queue:
        chain = queue.popleft()
        if len(chain) - 1 >= max_depth:
            continue
        tail = chain[-1]
        for _, target, data in graph.out_edges(tail, data=True):
            if data.get("type") not in allowed:
                continue
            if target in chain:
                continue  # cycle guard
            new_chain = [*chain, target]
            paths.append(new_chain)
            queue.append(new_chain)

    if not paths:
        return []

    all_symbols = {sym for chain in paths for sym in chain}
    refs_by_symbol = await _resolve_refs(engine=engine, repo_id=repo_id, symbols=all_symbols)

    out: list[Path] = []
    for chain in paths:
        steps = [
            refs_by_symbol.get(sym)
            or CodeRef(file_path="<unresolved>", start_line=1, end_line=1, symbol=sym)
            for sym in chain
        ]
        out.append(Path(steps=steps, edge_types=list(allowed)))
    log.debug("graph_traverse.done", start=start, paths=len(out))
    return out


async def _resolve_refs(
    *, engine: AsyncEngine, repo_id: str, symbols: set[str]
) -> dict[str, CodeRef]:
    if not symbols:
        return {}
    sym_list = list(symbols)
    query = select(
        chunks_table.c.symbol,
        chunks_table.c.file_path,
        chunks_table.c.start_line,
        chunks_table.c.end_line,
    ).where(
        and_(
            chunks_table.c.repo_id == repo_id,
            or_(*[chunks_table.c.symbol == s for s in sym_list]),
        )
    )
    # A long function is stored as several chunks under one symbol (see
    # ``chunk.MAX_CHUNK_LINES``). Order so the first row is its opening part,
    # and let ``setdefault`` below keep that one — otherwise the symbol
    # resolves to whichever part the planner happened to return. This must
    # chain off the select, not off the where clause (an AND expression has no
    # ``.order_by``, which raised AttributeError at query build time).
    query = query.order_by(chunks_table.c.file_path, chunks_table.c.start_line)
    async with engine.connect() as conn:
        rows = (await conn.execute(query)).all()

    out: dict[str, CodeRef] = {}
    for symbol, file_path, start_line, end_line in rows:
        out.setdefault(
            symbol,
            CodeRef(
                file_path=file_path,
                start_line=int(start_line),
                end_line=int(end_line),
                symbol=symbol,
            ),
        )
    return out


__all__ = ["graph_traverse"]
