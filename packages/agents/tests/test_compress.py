"""Phase 5 compression tests: safe parsing, clipping, and answerer-only view."""

from __future__ import annotations

from typing import Any, cast

import pytest

from repopilot_agents.qa.compress import compress_chunk, render_chunk_view
from repopilot_agents.qa.prompts import answer_user_prompt
from repopilot_agents.types import ChunkContent, CodeRef


def _chunk(*, start: int = 10, end: int = 29, kind: str = "function") -> ChunkContent:
    lines = [f"line_{i}" for i in range(start, end + 1)]
    return ChunkContent(
        ref=CodeRef(file_path="pkg/mod.py", start_line=start, end_line=end, symbol="pkg.mod.fn"),
        content="\n".join(lines),
        kind=kind,
    )


class _StubProvider:
    def __init__(self, text: str) -> None:
        self.text = text
        self.call_count = 0

    async def generate(self, model: Any, messages: Any, **kwargs: Any) -> Any:
        self.call_count += 1

        class _R:
            pass

        r = _R()
        r.text = self.text  # type: ignore[attr-defined]
        return r


@pytest.mark.asyncio
async def test_compress_chunk_keeps_clipped_merged_ranges() -> None:
    provider = _StubProvider('{"keep":[[8,12],[13,15],[20,22],[50,60]]}')
    chunk = await compress_chunk("what matters?", _chunk(), provider=cast(Any, provider))
    assert chunk.kept_line_spans == [(10, 15), (20, 22)]
    assert render_chunk_view(chunk) == "\n".join(
        ["line_10", "line_11", "line_12", "line_13", "line_14", "line_15", "line_20", "line_21", "line_22"]
    )


@pytest.mark.asyncio
async def test_compress_chunk_falls_back_on_invalid_json() -> None:
    provider = _StubProvider("not json")
    original = _chunk()
    chunk = await compress_chunk("what matters?", original, provider=cast(Any, provider))
    assert chunk.kept_line_spans is None
    assert chunk.content == original.content


@pytest.mark.asyncio
async def test_compress_chunk_skips_short_or_module_chunks() -> None:
    provider = _StubProvider('{"keep":[[10,11]]}')
    short = await compress_chunk("q", _chunk(start=1, end=5), provider=cast(Any, provider))
    module = await compress_chunk("q", _chunk(kind="module"), provider=cast(Any, provider))
    assert short.kept_line_spans is None
    assert module.kept_line_spans is None
    assert provider.call_count == 0


def test_answer_prompt_uses_compressed_view_only() -> None:
    chunk = _chunk().model_copy(update={"kept_line_spans": [(10, 11), (20, 20)]})
    prompt = answer_user_prompt("what matters?", [chunk])
    assert "line_10" in prompt
    assert "line_11" in prompt
    assert "line_20" in prompt
    assert "line_12" not in prompt
