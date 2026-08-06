"""True batched embedding orchestration over repository chunks."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import structlog

from repopilot_core.llm.provider import EMBED_DOCUMENT_PREFIX, LLMProvider, ProviderError
from repopilot_core.settings import Settings
from repopilot_ingestion.chunk import Chunk
from repopilot_ingestion.db import EMBEDDING_DIM

log = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class EmbeddedChunk:
    chunk: Chunk
    vector: list[float]


def embedding_text(chunk: Chunk, *, settings: Settings) -> str:
    """The exact string sent to the embedder for ``chunk``.

    Two things are prepended to the body, and neither touches ``Chunk.content``
    — the stored text and its line range must keep matching the file, because
    the code viewer, the verifier, and compression all index into them.

    * The nomic document prefix (see ``EMBED_DOCUMENT_PREFIX``).
    * A two-line locator. A method body embedded bare says nothing about where
      it lives or what owns it: ``send`` is a different thing in ``Client`` and
      in ``AsyncTransport``, and the body alone cannot tell them apart. This is
      deliberately narrower than the Phase 6 enrichment that regressed dense
      recall — path and dotted name only, no decorators, docstring keywords, or
      neighbour lists.
    """
    body = (
        chunk.enriched_text
        if settings.ingestion_embed_enriched_text and chunk.enriched_text is not None
        else chunk.content
    )
    return f"{EMBED_DOCUMENT_PREFIX}# file: {chunk.file_path}\n# symbol: {chunk.symbol}\n{body}"


async def embed_chunks(
    chunks: Sequence[Chunk],
    *,
    provider: LLMProvider,
    settings: Settings,
) -> list[EmbeddedChunk]:
    """Embed every chunk; results are returned in the same order as ``chunks``."""
    items = [(chunk, embedding_text(chunk, settings=settings)) for chunk in chunks]

    log.info("embed.start", count=len(chunks))
    embedded = await _embed_items(
        items,
        provider=provider,
        batch_size=settings.ingestion_embed_batch_size,
    )
    if len(embedded) != len(items):
        log.warning("embed.incomplete", requested=len(items), embedded=len(embedded))
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

        chunk, _ = items[0]
        # No fabricated vector. A hash-derived vector used to be stored here,
        # which put the chunk at a meaningless position in the corpus and let
        # ``repo_already_indexed`` report a complete index — silent data loss
        # that no metric could name. Skipping leaves the chunk row in place, so
        # BM25 and the graph still find it, and the miss is visible in the log
        # and in the embedded/chunk count gap.
        log.warning(
            "embed.chunk_failed_skipped",
            file_path=chunk.file_path,
            start_line=chunk.start_line,
            end_line=chunk.end_line,
            error=str(exc),
        )
        return []


__all__ = ["EmbeddedChunk", "embed_chunks"]
