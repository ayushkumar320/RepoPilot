from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from repopilot_core.settings import Settings
from repopilot_ingestion.chunk import chunk_file, enrich_chunks_with_neighbors
from repopilot_ingestion.embed import embed_chunks
from repopilot_ingestion.parse import parse_file

FIXTURE = Path(__file__).parent / "fixtures" / "sample_module.py"


class RecordingEmbedProvider:
    def __init__(self) -> None:
        self.texts: list[str] = []

    async def embed(self, text: str) -> Any:
        self.texts.append(text)
        return type("Embedding", (), {"vector": [0.0] * 768})()


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
async def test_embed_chunks_uses_enriched_text_when_present(tmp_path: Path) -> None:
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

    assert provider.texts == [login.enriched_text]
    assert provider.texts[0] != login.content
