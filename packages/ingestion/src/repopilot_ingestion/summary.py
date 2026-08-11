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


#: Consecutive provider failures that stop the summariser for the rest of the
#: run. One failure used to be enough, which meant a single 429 at high
#: concurrency downgraded every remaining chunk to a fallback summary. A real
#: exhaustion still trips it within a few chunks.
CIRCUIT_TRIP_FAILURES = 5

#: Marks a summary the model never produced. Written by ``_fallback_summary``
#: and read back by ``is_placeholder_summary`` — the two must not drift, or the
#: re-summarise pass silently stops finding anything to fix.
SUMMARY_UNAVAILABLE_SUFFIX = " (summary unavailable)"


def is_placeholder_summary(summary: str | None) -> bool:
    """Whether ``summary`` stands in for one the summariser could not produce.

    ``None`` counts: a chunk written before summaries existed, or by a run that
    failed before reaching them, is in exactly the same position.
    """
    return summary is None or summary.endswith(SUMMARY_UNAVAILABLE_SUFFIX)


def _fallback_summary(chunk: Chunk) -> str:
    """Deterministic stand-in when the summariser can't run (e.g. every provider
    is exhausted). More useful than the literal ``"unknown"`` — it still tells
    the reader what the chunk is, from AST facts we already have.
    """
    name = chunk.symbol.rsplit(".", 1)[-1] if chunk.symbol else chunk.file_path
    kind = chunk.kind.replace("_", " ")
    return f"{kind} `{name}` in {chunk.file_path}{SUMMARY_UNAVAILABLE_SUFFIX}"


async def summarise_chunks(
    chunks: Sequence[Chunk],
    *,
    provider: LLMProvider | None,
    settings: Settings,
) -> list[SummarisedChunk]:
    if provider is None:
        return [SummarisedChunk(chunk=c, summary=_fallback_summary(c)) for c in chunks]
    """Summarise every chunk concurrently, bounded by the configured semaphore.

    In local/dev usage the chat providers may be rate-limited or out of quota.
    Summaries are helpful but not critical for indexing, so we degrade each
    failed chunk to ``"unknown"`` instead of aborting the whole pipeline.
    """
    concurrency = max(1, settings.ingestion_summary_concurrency)
    circuit_open = False
    consecutive_failures = 0
    circuit_lock = asyncio.Lock()

    async def one(chunk: Chunk) -> SummarisedChunk:
        nonlocal circuit_open, consecutive_failures
        async with circuit_lock:
            if circuit_open:
                return SummarisedChunk(chunk=chunk, summary=_fallback_summary(chunk))
        try:
            response = await provider.generate(
                ModelId.CODE_HEALTH,
                _prompt(chunk),
                retry_429_attempts=1,
                temperature=0.0,
                max_tokens=120,
            )
            summary = response.text.strip() or _fallback_summary(chunk)
            async with circuit_lock:
                consecutive_failures = 0
        except ProviderError as exc:
            async with circuit_lock:
                consecutive_failures += 1
                circuit_open = consecutive_failures >= CIRCUIT_TRIP_FAILURES
            log.warning(
                "summary.chunk_fallback_unknown",
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                symbol=chunk.symbol,
                error=str(exc),
            )
            summary = _fallback_summary(chunk)
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


__all__ = [
    "CIRCUIT_TRIP_FAILURES",
    "SUMMARY_UNAVAILABLE_SUFFIX",
    "SummarisedChunk",
    "is_placeholder_summary",
    "summarise_chunks",
]
