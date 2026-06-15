"""Batched async embedder over chunks via the central ``LLMProvider``.

The provider's ``embed()`` is per-text. This module spreads N chunk-embeds
across ``ingestion_embed_concurrency`` workers using ``asyncio.Semaphore``.
Caching, fallback, and 429 backoff live inside ``LLMProvider`` — this layer
is just orchestration.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass

import structlog

from repopilot_core.llm.provider import EmbeddingResponse, LLMProvider
from repopilot_core.settings import Settings
from repopilot_ingestion.chunk import Chunk

log = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class EmbeddedChunk:
    chunk: Chunk
    vector: list[float]


async def embed_chunks(
    chunks: Sequence[Chunk],
    *,
    provider: LLMProvider,
    settings: Settings,
) -> list[EmbeddedChunk]:
    """Embed every chunk; results are returned in the same order as ``chunks``."""
    sem = asyncio.Semaphore(max(1, settings.ingestion_embed_concurrency))

    async def one(chunk: Chunk) -> EmbeddedChunk:
        async with sem:
            response: EmbeddingResponse = await provider.embed(chunk.content)
            return EmbeddedChunk(chunk=chunk, vector=response.vector)

    log.info("embed.start", count=len(chunks))
    embedded = await asyncio.gather(*(one(c) for c in chunks))
    log.info("embed.done", count=len(embedded))
    return list(embedded)


__all__ = ["EmbeddedChunk", "embed_chunks"]
