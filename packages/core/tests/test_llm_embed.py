"""Tests for ``LLMProvider.embed()`` — cache hit, fresh embed, dim contract."""

from __future__ import annotations

from typing import Any

import pytest

from repopilot_core.llm.models import ModelBinding, ModelId, ProviderName
from repopilot_core.llm.provider import EmbeddingResponse, _BaseClient

from .conftest import make_provider


class FakeEmbedder(_BaseClient):
    """Test double — bypasses the sentence-transformers model load and
    returns canned embeddings."""

    provider = ProviderName.HUGGINGFACE

    def __init__(self, vectors: list[list[float]]) -> None:
        self._vectors = list(vectors)
        self.calls: list[tuple[str, str]] = []

    async def chat(self, *args: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise AssertionError("chat not expected during embed test")

    async def embed(self, binding: ModelBinding, text: str) -> EmbeddingResponse:
        self.calls.append((binding.physical_model, text))
        head = self._vectors.pop(0)
        return EmbeddingResponse(
            vector=head,
            model=ModelId.EMBEDDINGS,
            provider=self.provider,
            physical_model=binding.physical_model,
        )


@pytest.mark.asyncio
async def test_embed_returns_vector(tmp_settings: Any) -> None:
    fake = FakeEmbedder(vectors=[[0.1, 0.2, 0.3]])
    provider = make_provider(tmp_settings, clients={}, embedder=fake)

    response = await provider.embed("hello world")

    assert response.vector == [0.1, 0.2, 0.3]
    assert response.dim == 3
    assert response.model == ModelId.EMBEDDINGS
    assert response.provider == ProviderName.HUGGINGFACE
    assert response.cached is False
    assert fake.calls == [("nomic-ai/nomic-embed-text-v1.5", "hello world")]
    await provider.aclose()


@pytest.mark.asyncio
async def test_embed_cache_hit_skips_provider(tmp_settings: Any) -> None:
    fake = FakeEmbedder(vectors=[[0.4, 0.5]])
    provider = make_provider(tmp_settings, clients={}, embedder=fake)

    first = await provider.embed("same text")
    second = await provider.embed("same text")

    assert first.vector == [0.4, 0.5]
    assert second.vector == [0.4, 0.5]
    assert second.cached is True
    # FakeEmbedder would raise on a second call because the queue is empty.
    assert len(fake.calls) == 1
    await provider.aclose()
