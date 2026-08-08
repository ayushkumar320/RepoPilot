"""Cross-encoder reranker over (query, chunk) pairs via ``fastembed``.

Unlike the bi-encoder (dense) lane — which embeds query and chunk separately
and compares vectors — a cross-encoder reads the concatenated pair and scores
relevance directly. Slower per pair, far more accurate; that's why it runs on
the small post-retrieval pool, never the corpus.

Model choice: ``Xenova/ms-marco-MiniLM-L-6-v2`` (~80 MB ONNX, CPU) scores
~460 pairs/s on an M-series Mac. ``BAAI/bge-reranker-base`` (1.04 GB) is the
configurable quality fallback. Configured via ``settings.rerank_model``.

Chunks are scored as ``symbol + newline + content`` so code symbols contribute
directly to the pair score.

Scores are cached in-process by ``sha256(model + query + text)``; at ~460
pairs/s a persistent cache isn't worth the plumbing.
"""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path
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
        # The startup warm-up runs in a worker thread. Without this lock the
        # first question, arriving mid-download, sees `_encoder is None` and
        # builds a *second* TextCrossEncoder — paying the ~91 MB load twice
        # concurrently. The lock makes the request wait on the warm-up instead.
        self._load_lock = threading.Lock()

    def _build_encoder(self) -> Any:
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        log.info("rerank.model_loading", model=self.model_name)
        # fastembed defaults its cache to tempfile.gettempdir(); macOS reaps
        # /var/folders/... periodically, which leaves a half-populated snapshot
        # dir and makes the ONNX load fail with NO_SUCHFILE. Keep the weights
        # under the user cache dir so a tmp sweep can't gut them.
        cache_dir = Path.home() / ".cache" / "repopilot" / "fastembed"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return TextCrossEncoder(self.model_name, cache_dir=str(cache_dir))

    def _ensure_loaded(self) -> Any:
        if self._encoder is None:
            with self._load_lock:
                if self._encoder is None:
                    self._encoder = self._build_encoder()
        return self._encoder

    def warm(self) -> None:
        """Load the ONNX model now (downloads ~91 MB on a cold cache).

        Blocking and slow on first run — call it off the event loop (API
        startup does, via ``asyncio.to_thread``) so the first user question
        doesn't pay the download while the request socket waits.
        """
        self._ensure_loaded()

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
