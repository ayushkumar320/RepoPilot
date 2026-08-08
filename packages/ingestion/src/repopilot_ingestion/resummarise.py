"""Re-run summaries over an existing snapshot, without re-indexing it.

Every chunk indexed while the chat providers were rate-limited carries a
placeholder summary instead of a real one. Symbols, spans, embeddings and graph
edges from those runs are all correct — only the summaries are missing, and a
full re-index to recover them would rebuild several minutes of work that is
already right.

Nothing here touches embeddings, and that is safe rather than lucky:
``embed.embedding_text`` builds its input from ``content`` / ``enriched_text``
and never reads ``summary``. Summaries reach the reader through the answer
prompt, so rewriting one changes what the model is told and not where the chunk
sits in vector space.

Usage::

    uv run python -m repopilot_ingestion.resummarise <repo_id> [--dry-run]

``repo_id`` is the snapshot id (``owner/name@sha``); pass ``--all`` to sweep
every snapshot that has placeholders.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from typing import cast

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from repopilot_core.llm.provider import LLMProvider
from repopilot_core.settings import Settings, get_settings
from repopilot_ingestion.chunk import Chunk, ChunkKind
from repopilot_ingestion.db import chunks as chunks_table
from repopilot_ingestion.persist import make_engine
from repopilot_ingestion.summary import is_placeholder_summary, summarise_chunks

log = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ResummariseResult:
    """What one pass actually changed.

    ``still_placeholder`` is the number that came back from the summariser
    still unusable — the provider was exhausted again. It is reported rather
    than folded into ``rewritten`` so that a run against a dead quota cannot
    look like a successful one.
    """

    repo_id: str
    examined: int
    rewritten: int
    still_placeholder: int

    @property
    def complete(self) -> bool:
        return self.examined > 0 and self.still_placeholder == 0


async def _placeholder_chunks(
    conn: AsyncConnection, repo_id: str
) -> list[tuple[int, Chunk]]:  # pragma: no cover - thin query wrapper
    rows = (
        await conn.execute(
            select(
                chunks_table.c.id,
                chunks_table.c.file_path,
                chunks_table.c.symbol,
                chunks_table.c.kind,
                chunks_table.c.start_line,
                chunks_table.c.end_line,
                chunks_table.c.content,
                chunks_table.c.summary,
            ).where(chunks_table.c.repo_id == repo_id)
        )
    ).fetchall()

    out: list[tuple[int, Chunk]] = []
    for row_id, file_path, symbol, kind, start_line, end_line, content, summary in rows:
        # Filtered here rather than in SQL: `is_placeholder_summary` is the one
        # definition of what a placeholder is, and a LIKE pattern beside it
        # would be a second one to keep in step.
        if not is_placeholder_summary(summary):
            continue
        out.append(
            (
                int(row_id),
                Chunk(
                    file_path=str(file_path),
                    symbol=str(symbol),
                    kind=cast("ChunkKind", str(kind)),
                    start_line=int(start_line),
                    end_line=int(end_line),
                    content=str(content),
                ),
            )
        )
    return out


async def resummarise_repo(
    repo_id: str,
    *,
    provider: LLMProvider | None,
    settings: Settings,
    engine: AsyncEngine | None = None,
    dry_run: bool = False,
) -> ResummariseResult:
    """Replace placeholder summaries for one snapshot. Returns what changed."""
    owned = engine is None
    engine = engine or make_engine(settings)
    try:
        async with engine.connect() as conn:
            pending = await _placeholder_chunks(conn, repo_id)

        if not pending or dry_run:
            return ResummariseResult(
                repo_id=repo_id,
                examined=len(pending),
                rewritten=0,
                still_placeholder=len(pending),
            )

        log.info("resummarise.start", repo_id=repo_id, chunks=len(pending))
        summarised = await summarise_chunks(
            [chunk for _, chunk in pending], provider=provider, settings=settings
        )

        rewritten = 0
        still = 0
        async with engine.begin() as conn:
            for (row_id, _), result in zip(pending, summarised, strict=True):
                # Writing a fallback over a fallback is a no-op that would
                # still report as progress. Leave the row alone and count it.
                if is_placeholder_summary(result.summary):
                    still += 1
                    continue
                await conn.execute(
                    update(chunks_table)
                    .where(chunks_table.c.id == row_id)
                    .values(summary=result.summary)
                )
                rewritten += 1
    finally:
        if owned:
            await engine.dispose()

    log.info(
        "resummarise.done",
        repo_id=repo_id,
        examined=len(pending),
        rewritten=rewritten,
        still_placeholder=still,
    )
    return ResummariseResult(
        repo_id=repo_id,
        examined=len(pending),
        rewritten=rewritten,
        still_placeholder=still,
    )


async def snapshots_with_placeholders(engine: AsyncEngine) -> list[str]:
    """Snapshot ids holding at least one placeholder summary."""
    async with engine.connect() as conn:
        rows = (
            await conn.execute(select(chunks_table.c.repo_id, chunks_table.c.summary))
        ).fetchall()
    return sorted({str(r) for r, s in rows if is_placeholder_summary(s)})


async def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_id", nargs="?", help="snapshot id, e.g. owner/name@sha")
    parser.add_argument("--all", action="store_true", help="every snapshot with placeholders")
    parser.add_argument(
        "--dry-run", action="store_true", help="report what would change, write nothing"
    )
    args = parser.parse_args()
    if not args.repo_id and not args.all:
        parser.error("pass a repo_id or --all")

    settings = get_settings()
    engine = make_engine(settings)
    provider = None if args.dry_run else LLMProvider.build(settings=settings)
    try:
        targets = await snapshots_with_placeholders(engine) if args.all else [str(args.repo_id)]
        if not targets:
            print("No snapshot has placeholder summaries.")
            return 0

        failed = False
        for repo_id in targets:
            result = await resummarise_repo(
                repo_id,
                provider=provider,
                settings=settings,
                engine=engine,
                dry_run=args.dry_run,
            )
            verb = "would rewrite" if args.dry_run else "rewrote"
            print(
                f"{result.repo_id}: {result.examined} placeholder(s), "
                f"{verb} {result.rewritten}, {result.still_placeholder} still unavailable"
            )
            # A run that changed nothing because the provider is exhausted is a
            # failure, not a no-op — exit non-zero so a caller can retry later.
            if not args.dry_run and result.examined and not result.rewritten:
                failed = True
        return 1 if failed else 0
    finally:
        if provider is not None:
            await provider.aclose()
        await engine.dispose()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(asyncio.run(_main()))
