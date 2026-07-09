"""Cross-encoder reranker over (query, chunk) pairs via ``fastembed``.

Unlike the bi-encoder (dense) lane — which embeds query and chunk separately
and compares vectors — a cross-encoder reads the concatenated pair and scores
relevance directly. Slower per pair, far more accurate; that's why it runs on
the small post-retrieval pool, never the corpus.

Model choice: ``Xenova/ms-marco-MiniLM-L-6-v2`` (~80 MB ONNX, CPU) scores
~460 pairs/s on an M-series Mac — a 30-chunk pool costs ~65 ms, well inside
the phase's latency budget. ``BAAI/bge-reranker-base`` (1.04 GB) is the
configurable quality fallback if the self-test says MiniLM is mismatched to
code (spec §6). Configured via ``settings.rerank_model``.

Chunks are scored as ``symbol + newline + content`` — the symbol prefix is
the known fix for rerankers under-ranking code (docs/rag/04 §6).

Scores are cached in-process by ``sha256(model + query + text)``; at ~460
pairs/s a persistent cache isn't worth the plumbing.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:  # pragma: no cover - typing only
    from repopilot_agents.types import ChunkContent

log = structlog.get_logger(__name__)

DEFAULT_RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"


def rerank_text(chunk: ChunkContent) -> str:
    """The text the cross-encoder sees for one chunk (symbol-prefixed)."""
    symbol = chunk.ref.symbol or ""
    return f"{symbol}\n{chunk.content}" if symbol else chunk.content


class CrossEncoderReranker:
    """Lazy-loading, score-caching wrapper around ``fastembed.TextCrossEncoder``."""

    def __init__(self, model_name: str = DEFAULT_RERANK_MODEL) -> None:
        self.model_name = model_name
        self._encoder: Any = None
        self._cache: dict[str, float] = {}

    def _ensure_loaded(self) -> Any:
        if self._encoder is None:
            from fastembed.rerank.cross_encoder import TextCrossEncoder

            log.info("rerank.model_loading", model=self.model_name)
            self._encoder = TextCrossEncoder(self.model_name)
        return self._encoder

    def _key(self, query: str, text: str) -> str:
        return hashlib.sha256(f"{self.model_name}\x00{query}\x00{text}".encode()).hexdigest()

    def score(self, query: str, texts: list[str]) -> list[float]:
        """Relevance score per text (higher = more relevant). Cached per pair."""
        if not texts:
            return []
        keys = [self._key(query, t) for t in texts]
        missing = [
            (i, t) for i, (k, t) in enumerate(zip(keys, texts, strict=True)) if k not in self._cache
        ]
        if missing:
            encoder = self._ensure_loaded()
            fresh = list(encoder.rerank(query, [t for _, t in missing]))
            for (i, _), s in zip(missing, fresh, strict=True):
                self._cache[keys[i]] = float(s)
        return [self._cache[k] for k in keys]


_SHARED: CrossEncoderReranker | None = None


def shared_reranker(model_name: str = DEFAULT_RERANK_MODEL) -> CrossEncoderReranker:
    """Process-wide reranker so the ONNX model loads once."""
    global _SHARED
    if _SHARED is None or _SHARED.model_name != model_name:
        _SHARED = CrossEncoderReranker(model_name)
    return _SHARED


__all__ = ["DEFAULT_RERANK_MODEL", "CrossEncoderReranker", "rerank_text", "shared_reranker"]
