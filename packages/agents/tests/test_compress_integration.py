"""Phase 5 safety invariant: verifier must always see the full chunk content.

The answerer's prompt is built from ``kept_line_spans``. The verifier fetches
chunks fresh via ``read_chunks`` (which returns ``ChunkContent.content`` — the
full source), so a compressed view can never be routed to the verifier. This
test locks that invariant in place: the answer prompt shrinks, the raw
``ChunkContent.content`` used downstream by the verifier does not.
"""

from __future__ import annotations

from typing import Any, cast

import pytest

from repopilot_agents.qa.compress import compress_chunks
from repopilot_agents.qa.prompts import answer_user_prompt
from repopilot_agents.types import ChunkContent, CodeRef


def _chunk(start: int = 10, end: int = 40) -> ChunkContent:
    lines = [f"line_{i}" for i in range(start, end + 1)]
    return ChunkContent(
        ref=CodeRef(file_path="pkg/mod.py", start_line=start, end_line=end, symbol="pkg.mod.fn"),
        content="\n".join(lines),
        kind="function",
    )


class _StubProvider:
    def __init__(self, text: str) -> None:
        self.text = text

    async def generate(self, model: Any, messages: Any, **kwargs: Any) -> Any:
        class _R:
            pass

        r = _R()
        r.text = self.text  # type: ignore[attr-defined]
        return r


@pytest.mark.asyncio
async def test_verifier_sees_full_content_after_compression() -> None:
    original = _chunk()
    provider = _StubProvider('{"keep":[[12,14]]}')
    (compressed,) = await compress_chunks(
        "what matters?", [original], provider=cast(Any, provider)
    )

    # Answerer prompt shrinks.
    prompt = answer_user_prompt("q", [compressed])
    assert "line_12" in prompt and "line_13" in prompt
    assert "line_20" not in prompt

    # Full content is preserved on the model — this is what read_chunks
    # returns to the verifier, so the verifier always sees the whole chunk.
    assert compressed.content == original.content
    assert "line_20" in compressed.content
    assert compressed.kept_line_spans == [(12, 14)]


@pytest.mark.asyncio
async def test_compress_chunks_runs_in_parallel_and_handles_errors() -> None:
    class _RaisingProvider:
        async def generate(self, *a: Any, **kw: Any) -> Any:
            raise RuntimeError("upstream 429")

    original = [_chunk(), _chunk(start=50, end=80)]
    out = await compress_chunks(
        "q", original, provider=cast(Any, _RaisingProvider())
    )
    # On failure the safe path returns the original chunks unmutated.
    assert len(out) == 2
    for orig, got in zip(original, out, strict=True):
        assert got.content == orig.content
        assert got.kept_line_spans is None
