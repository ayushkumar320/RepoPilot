"""Chunk summaries via ``llama-3.1-8b-instant`` (ModelId.CODE_HEALTH).

Cached at the provider layer (SQLite, keyed on prompt). Per the prompt budget
in ``docs/00_CLAUDE_BUILD_GUIDE.md``, the summary prompt stays well under 2k
input tokens — the chunk itself is the dominant input.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

import structlog

from repopilot_core.llm.models import ModelId
from repopilot_core.llm.provider import LLMProvider, Message, ProviderError
from repopilot_core.settings import Settings
from repopilot_ingestion.chunk import Chunk

log = structlog.get_logger(__name__)


_SYSTEM = (
    "You are a code summariser. Produce a single sentence that names what the "
    "given repository chunk does and why a reader would care. No markdown. No "
    "filler. If you cannot tell from the snippet, say 'unknown'."
)


@dataclass(frozen=True, slots=True)
class SummarisedChunk:
    chunk: Chunk
    summary: str


def _prompt(chunk: Chunk) -> list[Message]:
    user = (
        f"Symbol: {chunk.symbol}\n"
        f"Kind: {chunk.kind}\n"
        f"File: {chunk.file_path}\n"
        f"Lines: {chunk.start_line}-{chunk.end_line}\n\n"
        f"```text\n{chunk.content.rstrip()}\n```"
    )
    return [Message("system", _SYSTEM), Message("user", user)]


async def summarise_chunks(
    chunks: Sequence[Chunk],
    *,
    provider: LLMProvider | None,
    settings: Settings,
) -> list[SummarisedChunk]:
    if provider is None:
        return [SummarisedChunk(chunk=c, summary="unknown") for c in chunks]
    """Summarise every chunk concurrently, bounded by the configured semaphore.

    In local/dev usage the chat providers may be rate-limited or out of quota.
    Summaries are helpful but not critical for indexing, so we degrade each
    failed chunk to ``"unknown"`` instead of aborting the whole pipeline.
    """
    concurrency = max(1, settings.ingestion_summary_concurrency)
    circuit_open = False
    circuit_lock = asyncio.Lock()

    async def one(chunk: Chunk) -> SummarisedChunk:
        nonlocal circuit_open
        async with circuit_lock:
            if circuit_open:
                return SummarisedChunk(chunk=chunk, summary="unknown")
        try:
            response = await provider.generate(
                ModelId.CODE_HEALTH,
                _prompt(chunk),
                retry_429_attempts=1,
                temperature=0.0,
                max_tokens=120,
            )
            summary = response.text.strip() or "unknown"
        except ProviderError as exc:
            async with circuit_lock:
                circuit_open = True
            log.warning(
                "summary.chunk_fallback_unknown",
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                symbol=chunk.symbol,
                error=str(exc),
            )
            summary = "unknown"
        return SummarisedChunk(chunk=chunk, summary=summary)

    queue: asyncio.Queue[tuple[int, Chunk] | None] = asyncio.Queue(maxsize=concurrency * 2)
    results: list[SummarisedChunk | None] = [None] * len(chunks)

    async def worker() -> None:
        while True:
            item = await queue.get()
            try:
                if item is None:
                    return
                index, chunk = item
                results[index] = await one(chunk)
            finally:
                queue.task_done()

    log.info("summary.start", count=len(chunks))
    workers = [asyncio.create_task(worker()) for _ in range(min(concurrency, len(chunks)))]
    try:
        for index, chunk in enumerate(chunks):
            await queue.put((index, chunk))
        for _ in workers:
            await queue.put(None)
        await queue.join()
        await asyncio.gather(*workers)
    finally:
        for task in workers:
            if not task.done():
                task.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    if any(result is None for result in results):
        raise RuntimeError("summary worker queue completed with missing results")
    out = [result for result in results if result is not None]
    log.info("summary.done", count=len(out))
    return out


__all__ = ["SummarisedChunk", "summarise_chunks"]
