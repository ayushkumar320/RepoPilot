"""Structural chunker — one chunk per function and per class.

Per the Phase 1 spec (``docs/04_BUILD_PLAN.md``):

* Class chunks include the class signature, the docstring, and the *names* of
  child methods — but **not** method bodies.
* Method chunks are independent. The chunker emits one per method as if it
  were a top-level function.
* Module chunks: one chunk per file holding only imports + top-level
  assignments (i.e., the slice of the file outside any def/class). This is
  what the deterministic tools layer reads when answering "what does this
  module declare?" without paying for an entire 500-line file.
* No chunk starts or ends mid-statement. Boundaries come from the AST.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from repopilot_ingestion.parse import ParsedFile, ParsedSymbol

ChunkKind = Literal["module", "function", "class", "method"]


@dataclass(frozen=True, slots=True)
class Chunk:
    """One indexable unit of source. Line numbers are 1-based, inclusive."""

    file_path: str
    symbol: str
    kind: ChunkKind
    start_line: int
    end_line: int
    content: str
    enriched_text: str | None = None
    signature: str | None = None
    decorators: tuple[str, ...] = ()
    docstring_tokens: tuple[str, ...] = ()
    neighbor_symbols: tuple[str, ...] = ()


def chunk_file(parsed: ParsedFile, *, rel_path: str | Path | None = None) -> list[Chunk]:
    """Chunk a parsed file into one ``Chunk`` per function/class/method (+ module).

    ``rel_path`` is the path stored on each chunk; defaults to ``parsed.path``.
    Pass the repo-relative path when persisting.
    """
    file_path = str(rel_path) if rel_path is not None else str(parsed.path)
    lines = parsed.source.splitlines(keepends=True)
    out: list[Chunk] = []

    # Cover the file with non-overlapping spans of top-level symbols so the
    # module chunk can include exactly the lines not occupied by any class or
    # top-level function.
    top_level_spans: list[tuple[int, int]] = []
    for sym in parsed.symbols:
        if sym.kind == "method":
            continue  # method spans live inside their class
        top_level_spans.append((sym.start_line, sym.end_line))

    module_lines = _module_residue_lines(len(lines), top_level_spans)
    if module_lines:
        module_content = "".join(lines[i - 1] for i in module_lines)
        if module_content.strip():
            out.append(
                Chunk(
                    file_path=file_path,
                    symbol=parsed.module or _module_symbol_from_path(file_path),
                    kind="module",
                    start_line=module_lines[0],
                    end_line=module_lines[-1],
                    content=module_content,
                    signature=f"module {parsed.module or _module_symbol_from_path(file_path)}",
                )
            )

    for sym in parsed.symbols:
        if sym.kind == "class":
            content = _class_header_content(sym, lines)
            out.append(
                Chunk(
                    file_path=file_path,
                    symbol=sym.qualified_name,
                    kind="class",
                    start_line=sym.start_line,
                    end_line=_class_header_end_line(sym, lines),
                    content=content,
                    enriched_text=_build_enriched_text(
                        symbol=sym.qualified_name,
                        kind="class",
                        signature=sym.signature,
                        decorators=sym.decorators,
                        docstring_tokens=sym.docstring_tokens,
                        neighbor_symbols=sym.bases + sym.method_names,
                        body=content,
                    ),
                    signature=sym.signature,
                    decorators=sym.decorators,
                    docstring_tokens=sym.docstring_tokens,
                    neighbor_symbols=sym.bases + sym.method_names,
                )
            )
        elif sym.kind in {"function", "method"}:
            content = _slice_lines(lines, sym.start_line, sym.end_line)
            out.append(
                Chunk(
                    file_path=file_path,
                    symbol=sym.qualified_name,
                    kind=sym.kind,
                    start_line=sym.start_line,
                    end_line=sym.end_line,
                    content=content,
                    enriched_text=_build_enriched_text(
                        symbol=sym.qualified_name,
                        kind=sym.kind,
                        signature=sym.signature,
                        decorators=sym.decorators,
                        docstring_tokens=sym.docstring_tokens,
                        neighbor_symbols=(),
                        body=content,
                    ),
                    signature=sym.signature,
                    decorators=sym.decorators,
                    docstring_tokens=sym.docstring_tokens,
                )
            )

    return out


# ── internals ───────────────────────────────────────────────────────────────


def _slice_lines(lines: list[str], start: int, end: int) -> str:
    return "".join(lines[start - 1 : end])


def _module_residue_lines(total_lines: int, occupied: list[tuple[int, int]]) -> list[int]:
    """Return the sorted 1-based line numbers NOT covered by any occupied span."""
    occupied_sorted = sorted(occupied)
    blocked: set[int] = set()
    for start, end in occupied_sorted:
        blocked.update(range(start, end + 1))
    return [i for i in range(1, total_lines + 1) if i not in blocked]


def _class_header_end_line(sym: ParsedSymbol, lines: list[str]) -> int:
    """End line for a class chunk: signature + docstring + method-name listing.

    For Phase 1 we keep the class chunk's *content* synthetic (built below)
    but the persisted ``end_line`` points at the last line of the class so
    callers can resolve refs to the whole class span when needed.
    """
    return sym.end_line


def _class_header_content(sym: ParsedSymbol, lines: list[str]) -> str:
    """Build the class chunk text: ``class X(Bases): docstring + method listing``."""
    bases = f"({', '.join(sym.bases)})" if sym.bases else ""
    pieces: list[str] = [f"class {sym.name}{bases}:"]
    if sym.docstring is not None:
        # Indent docstring one level under the class.
        for line in sym.docstring.splitlines() or [""]:
            pieces.append(f"    {line}")
    if sym.method_names:
        pieces.append("")
        pieces.append("    # methods:")
        for m in sym.method_names:
            pieces.append(f"    #   - {m}")
    return "\n".join(pieces) + "\n"


def _module_symbol_from_path(path: str) -> str:
    p = path.replace("\\", "/")
    if p.endswith(".py"):
        p = p[:-3]
    return p.replace("/", ".").lstrip(".")


def _build_enriched_text(
    *,
    symbol: str,
    kind: str,
    signature: str | None,
    decorators: tuple[str, ...],
    docstring_tokens: tuple[str, ...],
    neighbor_symbols: tuple[str, ...],
    body: str,
) -> str:
    prefix: list[str] = []
    if kind == "method":
        parts = symbol.split(".")
        if len(parts) >= 2:
            prefix.append(f"# class: {parts[-2]}")
    prefix.append(f"# symbol: {symbol}")
    prefix.append(f"# kind: {kind}")
    if decorators:
        prefix.append("# decorators: " + ", ".join(decorators))
    if signature:
        prefix.append("# signature: " + " ".join(signature.split()))
    if neighbor_symbols:
        prefix.append("# neighbors: " + ", ".join(neighbor_symbols[:5]))
    if docstring_tokens:
        prefix.append("# docstring keywords: " + ", ".join(docstring_tokens))
    if not prefix:
        return body
    return "\n".join(prefix) + "\n" + body


def enrich_chunks_with_neighbors(
    chunks: list[Chunk],
    adjacency: dict[str, dict[str, list[str]]],
    *,
    limit: int = 5,
) -> list[Chunk]:
    """Return chunks with graph neighbor symbols folded into ``enriched_text``.

    ``content`` remains raw source. The synthetic lines are only for embedding
    and BM25 indexing.
    """
    out: list[Chunk] = []
    for chunk in chunks:
        neighbors = _neighbor_symbols_for_chunk(chunk, adjacency, limit=limit)
        combined_neighbors = tuple(dict.fromkeys((*chunk.neighbor_symbols, *neighbors)))
        enriched_text = _build_enriched_text(
            symbol=chunk.symbol,
            kind=chunk.kind,
            signature=chunk.signature,
            decorators=chunk.decorators,
            docstring_tokens=chunk.docstring_tokens,
            neighbor_symbols=combined_neighbors,
            body=chunk.content,
        )
        out.append(
            Chunk(
                file_path=chunk.file_path,
                symbol=chunk.symbol,
                kind=chunk.kind,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                content=chunk.content,
                enriched_text=enriched_text,
                signature=chunk.signature,
                decorators=chunk.decorators,
                docstring_tokens=chunk.docstring_tokens,
                neighbor_symbols=combined_neighbors,
            )
        )
    return out


def _neighbor_symbols_for_chunk(
    chunk: Chunk,
    adjacency: dict[str, dict[str, list[str]]],
    *,
    limit: int,
) -> tuple[str, ...]:
    buckets = adjacency.get(chunk.symbol, {})
    if chunk.kind in {"function", "method"}:
        candidates = buckets.get("calls", [])
    elif chunk.kind == "class":
        candidates = [*buckets.get("inherits", []), *buckets.get("calls", [])]
    else:
        candidates = buckets.get("imports", [])
    return tuple(dict.fromkeys(candidates))[:limit]


__all__ = ["Chunk", "ChunkKind", "chunk_file", "enrich_chunks_with_neighbors"]
