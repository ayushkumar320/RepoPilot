"""Shared runtime helpers for eval runners."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from repopilot_core.llm.provider import LLMProvider
from repopilot_core.settings import Settings, get_settings
from repopilot_ingestion.db import repos as repos_table


@dataclass(slots=True)
class EvalContext:
    settings: Settings
    engine: AsyncEngine
    provider: LLMProvider

    async def aclose(self) -> None:
        await self.provider.aclose()
        await self.engine.dispose()


def build_eval_context(settings: Settings | None = None) -> EvalContext:
    resolved = settings or get_settings()
    engine = create_async_engine(resolved.postgres_dsn, pool_pre_ping=True)
    provider = LLMProvider.build(settings=resolved)
    return EvalContext(settings=resolved, engine=engine, provider=provider)


async def resolve_repo_id(
    engine: AsyncEngine, *, repo_slug: str, repo_id: str | None = None
) -> str:
    if repo_id is not None:
        return repo_id

    stmt = (
        select(repos_table.c.id)
        .where(repos_table.c.url.ilike(f"%/{repo_slug}"))
        .order_by(desc(repos_table.c.indexed_at))
        .limit(1)
    )
    async with engine.connect() as conn:
        resolved = await conn.scalar(stmt)
    if resolved is None:
        raise LookupError(
            f"no indexed repo found for slug {repo_slug!r}; set an explicit repo_id or index it first"
        )
    return str(resolved)


__all__ = ["EvalContext", "build_eval_context", "resolve_repo_id"]
