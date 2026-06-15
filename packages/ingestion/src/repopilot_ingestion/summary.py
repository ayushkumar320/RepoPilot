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
from repopilot_core.llm.provider import LLMProvider, Message
from repopilot_core.settings import Settings
from repopilot_ingestion.chunk import Chunk

log = structlog.get_logger(__name__)


_SYSTEM = (
    "You are a code summariser. Produce a single sentence that names what the "
    "given Python symbol does and why a reader would care. No markdown. No "
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
        f"```python\n{chunk.content.rstrip()}\n```"
    )
    return [Message("system", _SYSTEM), Message("user", user)]


async def summarise_chunks(
    chunks: Sequence[Chunk],
    *,
    provider: LLMProvider,
    settings: Settings,
) -> list[SummarisedChunk]:
    """Summarise every chunk concurrently, bounded by the configured semaphore."""
    sem = asyncio.Semaphore(max(1, settings.ingestion_summary_concurrency))

    async def one(chunk: Chunk) -> SummarisedChunk:
        async with sem:
            response = await provider.generate(
                ModelId.CODE_HEALTH,
                _prompt(chunk),
                temperature=0.0,
                max_tokens=120,
            )
            return SummarisedChunk(chunk=chunk, summary=response.text.strip())

    log.info("summary.start", count=len(chunks))
    out = await asyncio.gather(*(one(c) for c in chunks))
    log.info("summary.done", count=len(out))
    return list(out)


__all__ = ["SummarisedChunk", "summarise_chunks"]
