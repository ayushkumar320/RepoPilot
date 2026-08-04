"""True batched embedding orchestration over repository chunks."""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from dataclasses import dataclass

import structlog

from repopilot_core.llm.provider import LLMProvider, ProviderError
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
    items = [
        (
            chunk,
            chunk.enriched_text
            if settings.ingestion_embed_enriched_text and chunk.enriched_text is not None
            else chunk.content,
        )
        for chunk in chunks
    ]

    log.info("embed.start", count=len(chunks))
    embedded = await _embed_items(
        items,
        provider=provider,
        batch_size=settings.ingestion_embed_batch_size,
    )
    log.info("embed.done", count=len(embedded))
    return embedded


async def _embed_items(
    items: Sequence[tuple[Chunk, str]],
    *,
    provider: LLMProvider,
    batch_size: int,
) -> list[EmbeddedChunk]:
    if not items:
        return []
    try:
        responses = await provider.embed_many(
            [text for _, text in items],
            batch_size=batch_size,
        )
        if len(responses) != len(items):
            raise ProviderError(
                f"embed provider returned {len(responses)} responses for {len(items)} chunks"
            )
        if any(response.dim != EMBEDDING_DIM for response in responses):
            raise ProviderError(
                f"embed provider returned a vector dimension other than {EMBEDDING_DIM}"
            )
        return [
            EmbeddedChunk(chunk=chunk, vector=response.vector)
            for (chunk, _), response in zip(items, responses, strict=True)
        ]
    except ProviderError as exc:
        if len(items) > 1:
            midpoint = len(items) // 2
            left = await _embed_items(
                items[:midpoint],
                provider=provider,
                batch_size=batch_size,
            )
            right = await _embed_items(
                items[midpoint:],
                provider=provider,
                batch_size=batch_size,
            )
            return [*left, *right]

        chunk, embedding_text = items[0]
        log.warning(
            "embed.chunk_failed_using_fallback",
            file_path=chunk.file_path,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            error=str(exc),
        )
        return [
            EmbeddedChunk(
                chunk=chunk,
                vector=_stable_fallback_vector(embedding_text),
            )
        ]


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
