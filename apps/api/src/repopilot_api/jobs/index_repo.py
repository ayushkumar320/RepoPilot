"""arq worker function for the Phase 1 ingestion pipeline.

The actual pipeline logic lives in ``repopilot_ingestion.pipeline`` so it
stays unit-testable without arq. This module is the thin wiring that arq
picks up — startup/shutdown hooks build the shared ``LLMProvider`` once and
re-use it across jobs.
"""

from __future__ import annotations

from typing import Any, ClassVar

import structlog

from repopilot_core.llm.provider import LLMProvider
from repopilot_core.settings import get_settings
from repopilot_ingestion.pipeline import PipelineResult
from repopilot_ingestion.pipeline import index_repo as _index_repo

log = structlog.get_logger(__name__)


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    ctx["settings"] = settings
    ctx["llm"] = LLMProvider.build(settings=settings)
    log.info("arq.startup")


async def shutdown(ctx: dict[str, Any]) -> None:
    llm: LLMProvider | None = ctx.get("llm")
    if llm is not None:
        await llm.aclose()
    log.info("arq.shutdown")


async def index_repo(ctx: dict[str, Any], repo_url: str) -> dict[str, Any]:
    """arq job: index a GitHub repo end-to-end. Returns a JSON-able status dict."""
    result: PipelineResult = await _index_repo(
        repo_url, provider=ctx["llm"], settings=ctx["settings"]
    )
    return {
        "status": result.status,
        "repo_id": result.repo_id,
        "head_sha": result.head_sha,
        "indexed_sha": result.indexed_sha,
        "remote_sha": result.remote_sha,
        "loc_total": result.loc_total,
        "chunk_count": result.chunk_count,
        "edge_count": result.edge_count,
    }


class WorkerSettings:
    """arq discovery target. Run with: ``arq repopilot_api.jobs.index_repo.WorkerSettings``."""

    functions: ClassVar[list[Any]] = [index_repo]
    on_startup: ClassVar[Any] = startup
    on_shutdown: ClassVar[Any] = shutdown
