"""Language-agnostic source and repository-context chunking.

Python keeps its tree-sitter structural chunker. Other supported languages are
indexed as bounded, overlapping line windows so retrieval remains useful while
every citation still resolves to an exact file and line span.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import structlog

from repopilot_ingestion.chunk import Chunk

log = structlog.get_logger(__name__)


SOURCE_LANGUAGES: dict[str, str] = {
    ".bash": "shell",
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".cxx": "cpp",
    ".go": "go",
    ".h": "c",
    ".hpp": "cpp",
    ".java": "java",
    ".js": "javascript",
    ".jsx": "javascript",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".mjs": "javascript",
    ".php": "php",
    ".rb": "ruby",
    ".rs": "rust",
    ".scala": "scala",
    ".sh": "shell",
    ".svelte": "svelte",
    ".swift": "swift",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".vue": "vue",
    ".zsh": "shell",
}

SKIP_DIRECTORIES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".next",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "out",
        "target",
        "vendor",
        "venv",
    }
)

_EXACT_CONTEXT_NAMES = frozenset(
    {
        "cargo.toml",
        "composer.json",
        "docker-compose.yaml",
        "docker-compose.yml",
        "dockerfile",
        "gemfile",
        "go.mod",
        "makefile",
        "package.json",
        "package.swift",
        "pom.xml",
        "pyproject.toml",
        "setup.cfg",
        "settings.gradle",
        "settings.gradle.kts",
        "tsconfig.json",
    }
)


def iter_generic_files(root: Path) -> Iterable[tuple[Path, str]]:
    """Yield supported non-Python source and high-value context files in stable order."""
    candidates: list[tuple[Path, str]] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRECTORIES for part in rel.parts[:-1]):
            continue
        language = SOURCE_LANGUAGES.get(path.suffix.lower())
        if language is None:
            language = _context_language(path.name)
        if language is not None:
            candidates.append((path, language))
    yield from sorted(candidates, key=lambda item: item[0].relative_to(root).as_posix())


def chunk_text_file(
    path: Path,
    *,
    root: Path,
    language: str,
    max_file_bytes: int,
    max_chunk_lines: int,
    max_chunk_chars: int,
    overlap_lines: int,
) -> tuple[list[Chunk], int]:
    """Return bounded text chunks and line count for one supported file.

    Binary, oversized, and generated/minified files are rejected rather than
    injecting low-quality or unbounded content into retrieval prompts.
    """
    rel = path.relative_to(root).as_posix()
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise RuntimeError(f"could not stat indexable file {rel}: {exc}") from exc
    if size > max_file_bytes:
        log.info("generic_chunk.skip_oversized", file_path=rel, size=size, cap=max_file_bytes)
        return [], 0

    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise RuntimeError(f"could not read indexable file {rel}: {exc}") from exc
    if b"\x00" in raw:
        log.info("generic_chunk.skip_binary", file_path=rel)
        return [], 0

    source = raw.decode("utf-8", errors="replace")
    lines = source.splitlines(keepends=True)
    if not lines and source:
        lines = [source]
    if not lines:
        return [], 0
    if any(len(line) > max_chunk_chars for line in lines):
        log.info("generic_chunk.skip_generated", file_path=rel, reason="line_too_long")
        return [], 0

    chunks: list[Chunk] = []
    start_index = 0
    while start_index < len(lines):
        end_index = start_index
        char_count = 0
        while end_index < len(lines) and end_index - start_index < max_chunk_lines:
            next_size = len(lines[end_index])
            if end_index > start_index and char_count + next_size > max_chunk_chars:
                break
            char_count += next_size
            end_index += 1

        content = "".join(lines[start_index:end_index])
        if content.strip():
            start_line = start_index + 1
            end_line = end_index
            symbol = f"{language}:{rel}:{start_line}"
            chunks.append(
                Chunk(
                    file_path=rel,
                    symbol=symbol,
                    kind="module",
                    start_line=start_line,
                    end_line=end_line,
                    content=content,
                    enriched_text=f"# language: {language}\n# file: {rel}\n{content}",
                    signature=f"{language} file {rel}",
                )
            )

        if end_index >= len(lines):
            break
        next_start = end_index - overlap_lines
        start_index = max(start_index + 1, next_start)

    return chunks, len(lines)


def _context_language(name: str) -> str | None:
    lowered = name.lower()
    if lowered.startswith("readme") and lowered.endswith((".md", ".markdown", ".txt")):
        return "markdown"
    if lowered.startswith("requirements") and lowered.endswith(".txt"):
        return "requirements"
    if lowered in _EXACT_CONTEXT_NAMES:
        suffix = Path(lowered).suffix.lstrip(".")
        return suffix or lowered
    if lowered.startswith("build.gradle"):
        return "gradle"
    return None


__all__ = ["SKIP_DIRECTORIES", "SOURCE_LANGUAGES", "chunk_text_file", "iter_generic_files"]
