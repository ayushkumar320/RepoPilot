"""End-to-end Phase 1 pipeline orchestrator.

Wires: clone → parse → chunk → graph → (summarise || embed) → persist.

Two entry points:

* :func:`index_repo` does the full pipeline against live services.
* :func:`revisit_status` is the cheap ``git ls-remote`` staleness check used
  by the API when the user resubmits a known URL.

Both return a ``PipelineResult`` whose ``status`` matches the API contract
expected by Phase 4's ``POST /repos``.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import structlog

from repopilot_core.llm.provider import LLMProvider
from repopilot_core.settings import Settings
from repopilot_ingestion.chunk import Chunk, chunk_file, enrich_chunks_with_neighbors
from repopilot_ingestion.clone import (
    CloneResult,
    clone_to_tempdir,
    remote_head_sha,
)
from repopilot_ingestion.embed import EmbeddedChunk, embed_chunks
from repopilot_ingestion.graph import ModuleSource, build_graph, graph_to_adjacency
from repopilot_ingestion.parse import parse_file
from repopilot_ingestion.persist import (
    known_head_sha,
    make_engine,
    persist_index,
    repo_already_indexed,
)
from repopilot_ingestion.summary import summarise_chunks

log = structlog.get_logger(__name__)


PipelineStatus = Literal[
    "indexed",
    "already_indexed",
    "stale",
    "too_large",
]


@dataclass(frozen=True, slots=True)
class PipelineResult:
    status: PipelineStatus
    repo_id: str | None = None
    head_sha: str | None = None
    indexed_sha: str | None = None
    remote_sha: str | None = None
    loc_total: int | None = None
    chunk_count: int | None = None
    edge_count: int | None = None


async def revisit_status(*, repo_url: str, settings: Settings | None = None) -> PipelineResult:
    """Decide whether ``repo_url`` is already-current, stale, or unknown.

    Cheap — runs ``git ls-remote`` (no clone) and a single SELECT against
    ``repos``. Phase 4's UI calls this on URL paste to decide whether to
    show the "re-index?" banner.
    """
    settings = settings or Settings()
    engine = make_engine(settings)
    try:
        remote_sha = remote_head_sha(repo_url)
        indexed_sha = await known_head_sha(engine, repo_url=repo_url)
        if indexed_sha is None:
            return PipelineResult(status="stale", remote_sha=remote_sha)
        if indexed_sha == remote_sha:
            return PipelineResult(
                status="already_indexed",
                head_sha=indexed_sha,
                indexed_sha=indexed_sha,
                remote_sha=remote_sha,
            )
        return PipelineResult(status="stale", indexed_sha=indexed_sha, remote_sha=remote_sha)
    finally:
        await engine.dispose()


async def index_repo(
    repo_url: str,
    *,
    provider: LLMProvider,
    settings: Settings | None = None,
) -> PipelineResult:
    """Full ingestion pipeline. Idempotent on ``(repo_url, head_sha)``."""
    settings = settings or Settings()
    engine = make_engine(settings)
    try:
        with clone_to_tempdir(repo_url, root=settings.ingestion_clone_root) as clone:
            already = await repo_already_indexed(engine, repo_url=repo_url, head_sha=clone.head_sha)
            if already:
                log.info(
                    "pipeline.already_indexed",
                    repo_url=repo_url,
                    head_sha=clone.head_sha,
                )
                return PipelineResult(
                    status="already_indexed",
                    repo_id=clone.repo_id,
                    head_sha=clone.head_sha,
                )

            modules, chunks, loc_total = _scan_python_files(clone)

            if loc_total > settings.ingestion_max_repo_loc:
                log.warning(
                    "pipeline.too_large",
                    repo_url=repo_url,
                    loc_total=loc_total,
                    cap=settings.ingestion_max_repo_loc,
                )
                return PipelineResult(
                    status="too_large",
                    repo_id=clone.repo_id,
                    head_sha=clone.head_sha,
                    loc_total=loc_total,
                )

            graph = build_graph(modules)
            adjacency = graph_to_adjacency(graph)
            chunks = enrich_chunks_with_neighbors(chunks, adjacency)

            summarised = await summarise_chunks(chunks, provider=provider, settings=settings)
            embedded = await embed_chunks(chunks, provider=provider, settings=settings)

            embed_index: dict[tuple[str, int, int], EmbeddedChunk] = {
                (e.chunk.file_path, e.chunk.start_line, e.chunk.end_line): e for e in embedded
            }

            persist_result = await persist_index(
                engine=engine,
                repo_id=clone.repo_id,
                repo_url=repo_url,
                head_sha=clone.head_sha,
                summarised=summarised,
                embedded=embed_index,
                adjacency=adjacency,
                loc_total=loc_total,
            )
            return PipelineResult(
                status="indexed",
                repo_id=persist_result.repo_id,
                head_sha=clone.head_sha,
                loc_total=loc_total,
                chunk_count=persist_result.chunk_count,
                edge_count=persist_result.edge_count,
            )
    finally:
        await engine.dispose()


# ── internals ───────────────────────────────────────────────────────────────


def _scan_python_files(
    clone: CloneResult,
) -> tuple[list[ModuleSource], list[Chunk], int]:
    modules: list[ModuleSource] = []
    chunks: list[Chunk] = []
    loc_total = 0

    for py_path in _iter_python_files(clone.path):
        rel = py_path.relative_to(clone.path)
        module = _path_to_module(rel)
        parsed = parse_file(py_path, module=module)
        loc_total += parsed.line_count
        modules.append(ModuleSource(module=module, rel_path=str(rel), source=parsed.source))
        chunks.extend(chunk_file(parsed, rel_path=rel))
    return modules, chunks, loc_total


def _iter_python_files(root: Path) -> Iterable[Path]:
    skip_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__"}
    for path in root.rglob("*.py"):
        if any(part in skip_dirs for part in path.parts):
            continue
        yield path


def _path_to_module(rel_path: Path) -> str:
    parts = list(rel_path.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


__all__ = ["PipelineResult", "PipelineStatus", "index_repo", "revisit_status"]
