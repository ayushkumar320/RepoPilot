"""TDD gate: chunks land on AST boundaries; content matches source exactly."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from repopilot_ingestion.chunk import chunk_file
from repopilot_ingestion.parse import parse_file

FIXTURE = Path(__file__).parent / "fixtures" / "sample_module.py"


def _source_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def test_chunks_on_ast_boundaries() -> None:
    """Every function/class/method chunk starts on a def/class line."""
    parsed = parse_file(FIXTURE, module="sample")
    chunks = chunk_file(parsed, rel_path=FIXTURE.name)
    lines = _source_lines(FIXTURE)

    starters = {"def ", "async def ", "class "}
    for chunk in chunks:
        if chunk.kind == "module":
            continue
        first_line = lines[chunk.start_line - 1].lstrip()
        assert any(first_line.startswith(s) for s in starters), (
            f"chunk {chunk.symbol} starts mid-statement at line {chunk.start_line}: {first_line!r}"
        )
        assert chunk.end_line >= chunk.start_line


def test_chunk_content_matches_source_for_functions_and_methods() -> None:
    """For non-class chunks, ``chunk.content`` is the exact source slice."""
    parsed = parse_file(FIXTURE, module="sample")
    chunks = chunk_file(parsed, rel_path=FIXTURE.name)
    lines = _source_lines(FIXTURE)
    sampleable = [c for c in chunks if c.kind in {"function", "method", "module"}]
    assert len(sampleable) >= 3

    rng = random.Random(0)
    sample = rng.sample(sampleable, k=min(len(sampleable), 5))
    for chunk in sample:
        expected = "".join(lines[chunk.start_line - 1 : chunk.end_line])
        if chunk.kind == "module":
            # Module chunk concatenates *only* the non-occupied lines, which
            # may be non-contiguous — verify each emitted line came from source.
            for line in chunk.content.splitlines(keepends=True):
                assert line in expected or line in "".join(lines), (
                    f"module-chunk line not from source: {line!r}"
                )
        else:
            assert chunk.content == expected, (
                f"chunk {chunk.symbol} mismatch: start={chunk.start_line} end={chunk.end_line}"
            )


def test_class_chunk_omits_method_bodies() -> None:
    """Class chunks must not contain method bodies; the methods get their own."""
    parsed = parse_file(FIXTURE, module="sample")
    chunks = chunk_file(parsed, rel_path=FIXTURE.name)
    class_chunks = [c for c in chunks if c.kind == "class" and c.symbol.endswith("Dog")]
    assert len(class_chunks) == 1
    dog = class_chunks[0]
    assert "woof" not in dog.content
    assert "fetched" not in dog.content
    # The method names should be listed.
    assert "speak" in dog.content
    assert "fetch" in dog.content


def test_method_chunks_are_independent() -> None:
    parsed = parse_file(FIXTURE, module="sample")
    chunks = chunk_file(parsed, rel_path=FIXTURE.name)
    method_chunks = [c for c in chunks if c.kind == "method"]
    assert {c.symbol for c in method_chunks} >= {
        "sample.Animal.speak",
        "sample.Dog.speak",
        "sample.Dog.fetch",
    }
    fetch = next(c for c in method_chunks if c.symbol == "sample.Dog.fetch")
    assert "def fetch" in fetch.content
    assert "fetched" in fetch.content


@pytest.mark.parametrize("symbol", ["sample.top_level_function", "sample.async_helper"])
def test_top_level_functions_are_chunked(symbol: str) -> None:
    parsed = parse_file(FIXTURE, module="sample")
    chunks = chunk_file(parsed, rel_path=FIXTURE.name)
    syms = {c.symbol for c in chunks if c.kind == "function"}
    assert symbol in syms
