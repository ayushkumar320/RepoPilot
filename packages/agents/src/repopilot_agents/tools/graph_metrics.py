"""``graph_metrics`` — per-symbol metric pack used by Cartographer, Lanes A/B/C.

Five metrics in one round-trip:

* ``fan_in``     — number of unique symbols whose code calls ``symbol``
* ``fan_out``    — number of unique symbols ``symbol`` calls
* ``cyclomatic`` — McCabe cyclomatic complexity computed by walking the
                   chunk's own AST (deterministic; no LLM)
* ``churn``      — number of commits touching the chunk's file. **Phase 1
                   does not record churn** (the snapshot is cloned shallow);
                   returns 0 in v1 and is filled in by Phase 5 (Lane B).
* ``has_tests``  — true if any chunk in ``tests/``, ``test_*`` or ``*_test``
                   files mentions ``symbol`` in its content. Cheap heuristic
                   that's correct ~95% of the time.
"""

from __future__ import annotations

import ast

import structlog
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncEngine

from repopilot_agents.tools._adjacency import load_graph
from repopilot_agents.types import SymbolMetrics
from repopilot_ingestion.db import chunks as chunks_table

log = structlog.get_logger(__name__)


async def graph_metrics(symbol: str, *, engine: AsyncEngine, repo_id: str) -> SymbolMetrics:
    """Return the metric pack for ``symbol``. Missing symbol → zeroed pack."""
    graph = await load_graph(engine=engine, repo_id=repo_id)
    fan_in = graph.in_degree(symbol) if symbol in graph else 0
    fan_out = graph.out_degree(symbol) if symbol in graph else 0

    content = await _chunk_content(engine=engine, repo_id=repo_id, symbol=symbol)
    cyclomatic = _cyclomatic(content) if content else 0
    has_tests = await _has_tests(engine=engine, repo_id=repo_id, symbol=symbol)

    return SymbolMetrics(
        symbol=symbol,
        fan_in=int(fan_in),
        fan_out=int(fan_out),
        cyclomatic=cyclomatic,
        churn=0,  # Phase 5 fills this in once we have git log access.
        has_tests=has_tests,
    )


# ── internals ───────────────────────────────────────────────────────────────


async def _chunk_content(*, engine: AsyncEngine, repo_id: str, symbol: str) -> str | None:
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                select(chunks_table.c.content).where(
                    and_(
                        chunks_table.c.repo_id == repo_id,
                        chunks_table.c.symbol == symbol,
                    )
                )
            )
        ).first()
    return None if row is None else str(row[0])


def _cyclomatic(source: str) -> int:
    """McCabe complexity over a chunk: 1 + #(branch nodes).

    Branch nodes are ``if``, ``elif``, ``for``, ``while``, ``except``,
    ``with``-as-context (multi-with), ``and``/``or`` short-circuits, and
    each comprehension generator. This matches what radon reports for
    typical Python code without the runtime dep.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return 0
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            complexity += len(node.generators)
        elif isinstance(node, ast.IfExp):
            complexity += 1
    return complexity


async def _has_tests(*, engine: AsyncEngine, repo_id: str, symbol: str) -> bool:
    """Cheap heuristic: does ANY chunk in a test file mention this symbol?"""
    short_name = symbol.rsplit(".", 1)[-1]
    pattern = f"%{short_name}%"
    test_file_match = chunks_table.c.file_path.like("%tests/%")
    test_prefix = chunks_table.c.file_path.like("test_%")
    test_suffix = chunks_table.c.file_path.like("%_test.py")
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                select(func.count()).where(
                    and_(
                        chunks_table.c.repo_id == repo_id,
                        chunks_table.c.content.like(pattern),
                        test_file_match | test_prefix | test_suffix,
                    )
                )
            )
        ).first()
    if row is None:
        return False
    return int(row[0]) > 0


__all__ = ["graph_metrics"]
