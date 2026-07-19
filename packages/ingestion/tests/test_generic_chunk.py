from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from repopilot_core.settings import Settings
from repopilot_ingestion import pipeline as pipeline_mod
from repopilot_ingestion.clone import CloneResult
from repopilot_ingestion.generic_chunk import chunk_text_file, iter_generic_files


def _chunk(path: Path, root: Path, *, language: str = "typescript"):
    return chunk_text_file(
        path,
        root=root,
        language=language,
        max_file_bytes=10_000,
        max_chunk_lines=3,
        max_chunk_chars=1_000,
        overlap_lines=1,
    )


def test_discovers_supported_languages_and_repository_context(tmp_path: Path) -> None:
    (tmp_path / "index.ts").write_text("export const answer = 42;\n", encoding="utf-8")
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Example\n", encoding="utf-8")
    (tmp_path / "package.json").write_text('{"name":"example"}\n', encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"not indexed")

    found = [(path.relative_to(tmp_path).as_posix(), language) for path, language in iter_generic_files(tmp_path)]

    assert found == [
        ("README.md", "markdown"),
        ("index.ts", "typescript"),
        ("main.go", "go"),
        ("package.json", "json"),
    ]


def test_skips_dependency_build_and_symlink_content(tmp_path: Path) -> None:
    for directory in ("node_modules", "vendor", "dist", ".git"):
        path = tmp_path / directory
        path.mkdir()
        (path / "ignored.ts").write_text("export const ignored = true;\n", encoding="utf-8")
    (tmp_path / "kept.ts").write_text("export const kept = true;\n", encoding="utf-8")

    assert [path.name for path, _ in iter_generic_files(tmp_path)] == ["kept.ts"]


def test_chunks_with_overlap_and_truthful_line_spans(tmp_path: Path) -> None:
    path = tmp_path / "server.ts"
    path.write_text("one\ntwo\nthree\nfour\nfive\nsix\n", encoding="utf-8")

    chunks, line_count = _chunk(path, tmp_path)

    assert line_count == 6
    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [(1, 3), (3, 5), (5, 6)]
    assert chunks[0].content == "one\ntwo\nthree\n"
    assert chunks[1].content == "three\nfour\nfive\n"
    assert all(chunk.file_path == "server.ts" for chunk in chunks)
    assert all(chunk.kind == "module" for chunk in chunks)
    assert all("# language: typescript" in (chunk.enriched_text or "") for chunk in chunks)


def test_rejects_oversized_binary_and_minified_files(tmp_path: Path) -> None:
    oversized = tmp_path / "oversized.ts"
    oversized.write_text("x" * 101, encoding="utf-8")
    binary = tmp_path / "binary.js"
    binary.write_bytes(b"const x = 1;\x00more")
    minified = tmp_path / "minified.js"
    minified.write_text("x" * 1_001, encoding="utf-8")

    common = {
        "root": tmp_path,
        "language": "typescript",
        "max_chunk_lines": 10,
        "max_chunk_chars": 1_000,
        "overlap_lines": 1,
    }
    assert chunk_text_file(oversized, max_file_bytes=100, **common) == ([], 0)
    assert chunk_text_file(binary, max_file_bytes=10_000, **common) == ([], 0)
    assert chunk_text_file(minified, max_file_bytes=10_000, **common) == ([], 0)


def _clone(root: Path) -> CloneResult:
    return CloneResult(
        repo_url="https://github.com/example/repo",
        head_sha="a" * 40,
        path=root,
        owner="example",
        name="repo",
    )


def test_parallel_and_serial_repository_scans_are_identical(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    (tmp_path / "index.ts").write_text("export const answer = 42;\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Example\nTypeScript and Python.\n", encoding="utf-8")
    base = Settings(repopilot_env="test", llm_cache_path=tmp_path / "llm.sqlite")

    serial = pipeline_mod._scan_repository_files(
        _clone(tmp_path),
        settings=base.model_copy(update={"ingestion_scan_workers": 1}),
    )
    parallel = pipeline_mod._scan_repository_files(
        _clone(tmp_path),
        settings=base.model_copy(update={"ingestion_scan_workers": 4}),
    )

    assert parallel == serial
    assert [chunk.file_path for chunk in parallel[1]] == sorted(
        chunk.file_path for chunk in parallel[1]
    )


def test_scan_scheduler_is_bounded_by_worker_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for index in range(12):
        (tmp_path / f"file_{index:02}.ts").write_text("x" * (index + 1), encoding="utf-8")
    settings = Settings(repopilot_env="test", llm_cache_path=tmp_path / "llm.sqlite")
    jobs = pipeline_mod._discover_scan_jobs(tmp_path)
    active = 0
    max_active = 0
    lock = threading.Lock()

    def fake_scan(job, *, root, settings):  # type: ignore[no-untyped-def]
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.01)
        with lock:
            active -= 1
        return pipeline_mod._ScannedFile(
            order=job.order,
            rel_path=job.rel_path.as_posix(),
            module_source=None,
            chunks=(),
            line_count=1,
        )

    monkeypatch.setattr(pipeline_mod, "_scan_one_file", fake_scan)
    results = pipeline_mod._run_scan_jobs(jobs, root=tmp_path, settings=settings, workers=3)

    assert len(results) == 12
    assert 1 < max_active <= 3
    assert [result.order for result in results] == list(range(12))


def test_scan_failure_names_repository_relative_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "bad.ts").write_text("broken", encoding="utf-8")
    settings = Settings(repopilot_env="test", llm_cache_path=tmp_path / "llm.sqlite")
    jobs = pipeline_mod._discover_scan_jobs(tmp_path)

    def fail(job, *, root, settings):  # type: ignore[no-untyped-def]
        raise ValueError("parse failed")

    monkeypatch.setattr(pipeline_mod, "_scan_one_file", fail)
    with pytest.raises(RuntimeError, match=r"failed to scan bad\.ts: parse failed"):
        pipeline_mod._run_scan_jobs(jobs, root=tmp_path, settings=settings, workers=2)
