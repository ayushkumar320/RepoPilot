"""Dataset loading helpers for phase-gating evals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from repopilot_agents.types import ChunkContent, CodeRef

DATASETS_DIR = Path(__file__).resolve().parent / "datasets"


class GroundingEvalRow(BaseModel):
    question: str = Field(min_length=1)
    expected_refs: list[CodeRef] = Field(default_factory=list)
    expected_answer_keywords: list[str] = Field(default_factory=list)
    not_in_repo: bool = False


class VerifierEvalRow(BaseModel):
    claim: str = Field(min_length=1)
    expected_verdict: Literal["supported", "rejected"]
    refs: list[CodeRef] = Field(default_factory=list)
    chunks: list[ChunkContent] = Field(default_factory=list)


def dataset_path(name: str) -> Path:
    return DATASETS_DIR / name


def load_jsonl_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"{path}:{lineno} must be a JSON object")
        rows.append(payload)
    return rows


def load_grounding_dataset(path: Path) -> list[GroundingEvalRow]:
    return [GroundingEvalRow.model_validate(row) for row in load_jsonl_rows(path)]


def load_verifier_dataset(path: Path) -> list[VerifierEvalRow]:
    rows = [VerifierEvalRow.model_validate(row) for row in load_jsonl_rows(path)]
    for idx, row in enumerate(rows, start=1):
        if not row.refs and not row.chunks:
            raise ValueError(
                f"{path}:{idx} verifier dataset rows must include either refs or embedded chunks"
            )
    return rows


def take_rows[T](rows: list[T], limit: int | None) -> list[T]:
    materialized = list(rows)
    if limit is None:
        return materialized
    return materialized[:limit]


__all__ = [
    "DATASETS_DIR",
    "GroundingEvalRow",
    "VerifierEvalRow",
    "dataset_path",
    "load_grounding_dataset",
    "load_jsonl_rows",
    "load_verifier_dataset",
    "take_rows",
]
