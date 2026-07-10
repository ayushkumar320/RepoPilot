"""Phase 5 context compression: keep the answerer's view lean, not the verifier's.

Compression is conservative by design: if parsing fails, the chunk is short,
or the model returns an empty/invalid selection, the caller keeps the full
chunk. ``ChunkContent.content`` remains the full source text; we annotate the
answerer-visible slice in ``kept_line_spans`` and derive a compressed view only
when building the answer prompt.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence

from pydantic import BaseModel, Field, ValidationError, field_validator

from repopilot_agents.qa.prompts import COMPRESS_SYSTEM, _render_numbered_chunk
from repopilot_agents.types import ChunkContent
from repopilot_core.llm.models import ModelId
from repopilot_core.llm.provider import LLMProvider, Message


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


class _KeepRanges(BaseModel):
    keep: list[tuple[int, int]] = Field(default_factory=list)

    @field_validator("keep")
    @classmethod
    def _ordered_ranges(cls, ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        for start, end in ranges:
            if end < start:
                raise ValueError("end must be >= start")
            out.append((start, end))
        return out


def _compression_user_prompt(question: str, chunk: ChunkContent) -> str:
    return (
        f"QUESTION:\n{question}\n\n"
        f"CHUNK ({chunk.ref.file_path}:{chunk.ref.start_line}-{chunk.ref.end_line}):\n"
        f"{_render_numbered_chunk(chunk)}"
    )


def _parse_keep_ranges(raw: str) -> list[tuple[int, int]] | None:
    match = _JSON_RE.search(raw)
    if match is None:
        return None
    try:
        parsed = _KeepRanges.model_validate(json.loads(match.group(0)))
    except (json.JSONDecodeError, ValidationError, TypeError):
        return None
    return parsed.keep


def _merge_ranges(ranges: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    if not ranges:
        return []
    ordered = sorted(ranges)
    merged: list[tuple[int, int]] = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _clip_ranges(chunk: ChunkContent, ranges: Sequence[tuple[int, int]]) -> list[tuple[int, int]]:
    start = chunk.ref.start_line
    end = chunk.ref.end_line
    kept: list[tuple[int, int]] = []
    for lo, hi in ranges:
        clipped_lo = max(start, lo)
        clipped_hi = min(end, hi)
        if clipped_hi >= clipped_lo:
            kept.append((clipped_lo, clipped_hi))
    return _merge_ranges(kept)


def render_chunk_view(chunk: ChunkContent) -> str:
    """Return the answerer-visible chunk text, respecting kept spans if any."""
    if not chunk.kept_line_spans:
        return chunk.content
    lines = chunk.content.splitlines()
    out: list[str] = []
    base = chunk.ref.start_line
    for start, end in chunk.kept_line_spans:
        rel_start = max(0, start - base)
        rel_end = min(len(lines), end - base + 1)
        if rel_end <= rel_start:
            continue
        out.extend(lines[rel_start:rel_end])
    return "\n".join(out).strip() or chunk.content


async def compress_chunk(
    question: str,
    chunk: ChunkContent,
    *,
    provider: LLMProvider,
    min_lines: int = 15,
) -> ChunkContent:
    """Return a chunk annotated with kept spans, or the original on safe skip."""
    if chunk.kind == "module":
        return chunk
    line_count = max(1, len(chunk.content.splitlines()))
    if line_count < min_lines:
        return chunk

    response = await provider.generate(
        ModelId.CODE_HEALTH,
        [
            Message("system", COMPRESS_SYSTEM),
            Message("user", _compression_user_prompt(question, chunk)),
        ],
        temperature=0.0,
        max_tokens=120,
    )
    keep = _parse_keep_ranges(response.text)
    if keep is None:
        return chunk
    clipped = _clip_ranges(chunk, keep)
    if not clipped:
        return chunk
    return chunk.model_copy(update={"kept_line_spans": clipped})


async def compress_chunks(
    question: str,
    chunks: Sequence[ChunkContent],
    *,
    provider: LLMProvider,
    min_lines: int = 15,
) -> list[ChunkContent]:
    out: list[ChunkContent] = []
    for chunk in chunks:
        out.append(await compress_chunk(question, chunk, provider=provider, min_lines=min_lines))
    return out


__all__ = ["compress_chunk", "compress_chunks", "render_chunk_view"]
