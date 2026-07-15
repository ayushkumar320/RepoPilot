"""Batched async embedder over chunks via the central ``LLMProvider``.

The provider's ``embed()`` is per-text. This module spreads N chunk-embeds
across ``ingestion_embed_concurrency`` workers using ``asyncio.Semaphore``.
Caching, fallback, and 429 backoff live inside ``LLMProvider`` — this layer
is just orchestration.
"""

from __future__ import annotations

import asyncio
import hashlib
import math
from collections.abc import Sequence
from dataclasses import dataclass

import structlog

from repopilot_core.llm.provider import EmbeddingResponse, LLMProvider, ProviderError
from repopilot_core.settings import Settings
from repopilot_ingestion.chunk import Chunk
from repopilot_ingestion.db import EMBEDDING_DIM

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
        embedding_text = (
            chunk.enriched_text
            if settings.ingestion_embed_enriched_text and chunk.enriched_text is not None
            else chunk.content
        )
        async with sem:
            try:
                response: EmbeddingResponse = await provider.embed(embedding_text)
                return EmbeddedChunk(chunk=chunk, vector=response.vector)
            except ProviderError as exc:
                log.warning(
                    "embed.chunk_failed_using_fallback",
                    file_path=chunk.file_path,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    error=str(exc),
                )
                return EmbeddedChunk(chunk=chunk, vector=_stable_fallback_vector(embedding_text))

    log.info("embed.start", count=len(chunks))
    embedded = []
    for c in chunks:
        res = await one(c)
        embedded.append(res)
    log.info("embed.done", count=len(embedded))
    return embedded


def _stable_fallback_vector(text: str) -> list[float]:
    """Return a deterministic normalized vector when the local embedder rejects a chunk."""
    seed = hashlib.sha256(text.encode("utf-8", errors="ignore")).digest()
    values: list[float] = []
    counter = 0
    while len(values) < EMBEDDING_DIM:
        digest = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        for byte in digest:
            values.append((byte / 127.5) - 1.0)
            if len(values) == EMBEDDING_DIM:
                break
        counter += 1
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


__all__ = ["EmbeddedChunk", "embed_chunks"]
