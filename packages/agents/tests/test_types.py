"""Validator tests for the shared Phase 2 types."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from repopilot_agents.types import ChunkHit, CodeRef, Path


def test_coderef_rejects_end_before_start() -> None:
    with pytest.raises(ValidationError):
        CodeRef(file_path="x.py", start_line=5, end_line=2)


def test_coderef_accepts_equal_lines() -> None:
    ref = CodeRef(file_path="x.py", start_line=3, end_line=3)
    assert ref.start_line == ref.end_line == 3


def test_path_requires_at_least_one_step() -> None:
    with pytest.raises(ValidationError):
        Path(steps=[])


def test_path_depth_is_steps_minus_one() -> None:
    refs = [CodeRef(file_path="a.py", start_line=1, end_line=2) for _ in range(3)]
    path = Path(steps=refs)
    assert path.depth == 2


def test_chunk_hit_distance_must_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        ChunkHit(
            ref=CodeRef(file_path="a.py", start_line=1, end_line=2),
            distance=-0.01,
        )
