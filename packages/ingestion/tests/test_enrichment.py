from __future__ import annotations

from pathlib import Path

import pytest

from repopilot_core.llm.models import ModelId, ProviderName
from repopilot_core.llm.provider import (
    EMBED_DOCUMENT_PREFIX,
    EmbeddingResponse,
    ProviderError,
)
from repopilot_core.settings import Settings
from repopilot_ingestion.chunk import chunk_file, enrich_chunks_with_neighbors
from repopilot_ingestion.embed import embed_chunks, embedding_text
from repopilot_ingestion.parse import parse_file

FIXTURE = Path(__file__).parent / "fixtures" / "sample_module.py"


class RecordingEmbedProvider:
    def __init__(self) -> None:
        self.texts: list[str] = []
        self.batch_sizes: list[int] = []

    async def embed_many(
        self,
        texts: list[str],
        *,
        batch_size: int,
    ) -> list[EmbeddingResponse]:
        self.texts.extend(texts)
        self.batch_sizes.append(batch_size)
        return [
            EmbeddingResponse(
                vector=[0.0] * 768,
                model=ModelId.EMBEDDINGS,
                provider=ProviderName.HUGGINGFACE,
                physical_model="test",
            )
            for _ in texts
        ]


def test_parse_extracts_decorators_signature_and_docstring_tokens() -> None:
    parsed = parse_file(FIXTURE, module="sample")

    login = next(sym for sym in parsed.symbols if sym.qualified_name == "sample.login")
    assert login.decorators == ('@route("/login")',)
    assert login.signature.startswith("def login(")
    assert "redirect_url" in login.signature
    assert login.docstring_tokens == ("Validate", "session", "csrf", "redirect")

    kennel = next(sym for sym in parsed.symbols if sym.qualified_name == "sample.Kennel")
    assert kennel.decorators == ('@route("/kennel")',)
    assert kennel.signature == "class Kennel(Dog):"
    assert "feed" in kennel.method_names


def test_chunk_enriched_text_keeps_raw_content_separate() -> None:
    parsed = parse_file(FIXTURE, module="sample")
    chunks = chunk_file(parsed, rel_path=FIXTURE.name)

    login = next(chunk for chunk in chunks if chunk.symbol == "sample.login")
    assert login.content.startswith('@route("/login")')
    assert login.enriched_text is not None
    assert '# decorators: @route("/login")' in login.enriched_text
    assert "# signature: def login(" in login.enriched_text
    assert "# docstring keywords: Validate, session, csrf, redirect" in login.enriched_text
    assert login.content != login.enriched_text


def test_neighbor_symbols_are_added_from_graph_adjacency() -> None:
    parsed = parse_file(FIXTURE, module="sample")
    chunks = chunk_file(parsed, rel_path=FIXTURE.name)
    enriched = enrich_chunks_with_neighbors(
        chunks,
        {
            "sample.Kennel.feed": {
                "calls": ["sample.Dog.fetch", "sample.route"],
                "called_by": [],
                "imports": [],
                "imported_by": [],
                "inherits": [],
                "inherited_by": [],
            }
        },
    )

    feed = next(chunk for chunk in enriched if chunk.symbol == "sample.Kennel.feed")
    assert feed.neighbor_symbols == ("sample.Dog.fetch", "sample.route")
    assert feed.enriched_text is not None
    assert "# neighbors: sample.Dog.fetch, sample.route" in feed.enriched_text
    assert "return self.fetch" in feed.content


@pytest.mark.asyncio
async def test_embed_chunks_uses_raw_content_by_default(tmp_path: Path) -> None:
    parsed = parse_file(FIXTURE, module="sample")
    chunks = chunk_file(parsed, rel_path=FIXTURE.name)
    login = next(chunk for chunk in chunks if chunk.symbol == "sample.login")
    provider = RecordingEmbedProvider()

    await embed_chunks(
        [login],
        provider=provider,  # type: ignore[arg-type]
        settings=Settings(
            repopilot_env="test",
            llm_cache_path=tmp_path / "llm.sqlite",
            ingestion_embed_concurrency=1,
        ),
    )

    sent = provider.texts[0]
    assert sent.startswith(EMBED_DOCUMENT_PREFIX)
    assert "# file: sample_module.py" in sent
    assert "# symbol: sample.login" in sent
    assert sent.endswith(login.content)
    assert login.enriched_text is not None
    assert login.enriched_text not in sent
    assert provider.batch_sizes == [8]


@pytest.mark.asyncio
async def test_embed_chunks_can_opt_into_enriched_text(tmp_path: Path) -> None:
    parsed = parse_file(FIXTURE, module="sample")
    chunks = chunk_file(parsed, rel_path=FIXTURE.name)
    login = next(chunk for chunk in chunks if chunk.symbol == "sample.login")
    provider = RecordingEmbedProvider()

    await embed_chunks(
        [login],
        provider=provider,  # type: ignore[arg-type]
        settings=Settings(
            repopilot_env="test",
            llm_cache_path=tmp_path / "llm.sqlite",
            ingestion_embed_concurrency=1,
            ingestion_embed_enriched_text=True,
        ),
    )

    assert provider.texts[0].endswith(login.enriched_text or "")
    assert provider.texts[0] != login.content


@pytest.mark.asyncio
async def test_embed_batch_failure_skips_only_the_bad_chunk(tmp_path: Path) -> None:
    parsed = parse_file(FIXTURE, module="sample")
    chunks = chunk_file(parsed, rel_path=FIXTURE.name)[:3]

    class SelectiveProvider(RecordingEmbedProvider):
        async def embed_many(
            self,
            texts: list[str],
            *,
            batch_size: int,
        ) -> list[EmbeddingResponse]:
            self.texts.extend(texts)
            self.batch_sizes.append(batch_size)
            if embedding_text(chunks[1], settings=settings) in texts:
                raise ProviderError("bad chunk")
            return [
                EmbeddingResponse(
                    vector=[0.25] * 768,
                    model=ModelId.EMBEDDINGS,
                    provider=ProviderName.HUGGINGFACE,
                    physical_model="test",
                )
                for _ in texts
            ]

    settings = Settings(
        repopilot_env="test",
        llm_cache_path=tmp_path / "llm.sqlite",
        ingestion_embed_batch_size=16,
    )
    provider = SelectiveProvider()
    embedded = await embed_chunks(
        chunks,
        provider=provider,  # type: ignore[arg-type]
        settings=settings,
    )

    # The rejected chunk is dropped, never given a fabricated vector: a
    # hash-derived vector would place it at a meaningless point in the corpus
    # while still counting as indexed.
    assert len(embedded) == len(chunks) - 1
    assert [e.chunk.symbol for e in embedded] == [chunks[0].symbol, chunks[2].symbol]
    assert all(e.vector == [0.25] * 768 for e in embedded)
