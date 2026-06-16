"""Scaffolding tests for the two-tier eval workflow (docs/06 S6).

Both ``eval_sampled`` and ``eval_full`` markers are exercised here so the CI
workflows have at least one collectable test from day one.  When the real
dataset files land (docs/CURRENT_PHASE.md Phase 3 entry checklist items 2
and 3 — ``httpx_qa_v1.jsonl`` and ``verifier_quality_v1.jsonl``), the actual
runner tests displace these scaffold rows.

Each test skips cleanly with an actionable message when its dataset is
absent, so the workflows are green on a fresh checkout instead of failing
loudly with collection errors.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

DATASETS_DIR = Path(__file__).resolve().parents[1] / "src" / "repopilot_evals" / "datasets"


def _dataset_path(name: str) -> Path:
    return DATASETS_DIR / name


def _skip_if_missing(name: str) -> None:
    path = _dataset_path(name)
    if not path.exists():
        pytest.skip(
            f"eval dataset {name!r} not yet labeled — see "
            f"docs/CURRENT_PHASE.md Phase 3 entry checklist. "
            f"This test will activate when {path} lands."
        )


def _skip_if_no_groq_key() -> None:
    if not os.environ.get("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not set — eval is LLM-bound; cannot run.")


@pytest.mark.eval_sampled
def test_sampled_eval_workflow_is_collectible() -> None:
    """Sentinel: the sampled eval marker is wired and pytest collects at least
    one row, so ``make test-eval-sampled`` exits 0 even when datasets are
    missing.  Replace with real assertion when ``httpx_qa_v1.jsonl`` lands."""
    assert os.environ.get("EVAL_MODE", "sampled") in {"sampled", "full"}


@pytest.mark.eval_sampled
def test_httpx_qa_grounding_accuracy_sampled() -> None:
    """Sampled Q&A grounding: first 5 rows of ``httpx_qa_v1.jsonl``.
    Gate: grounding accuracy ≥ 90% on the sampled subset."""
    _skip_if_missing("httpx_qa_v1.jsonl")
    _skip_if_no_groq_key()
    # Real runner lands with Blocker 2 (httpx_qa_v1.jsonl labeling).
    pytest.skip(
        "eval runner not yet implemented; dataset exists but Phase 2 eval "
        "harness is part of Blocker 2's settle-work."
    )


@pytest.mark.eval_sampled
def test_verifier_quality_sampled() -> None:
    """Sampled Verifier accuracy: first 5 triples of ``verifier_quality_v1.jsonl``.
    Gate: Verifier accuracy ≥ 92% on the sampled subset (docs/06 S5)."""
    _skip_if_missing("verifier_quality_v1.jsonl")
    _skip_if_no_groq_key()
    pytest.skip(
        "eval runner not yet implemented; dataset exists but Phase 2 eval "
        "harness is part of Blocker 3's settle-work."
    )


@pytest.mark.eval_full
def test_full_eval_workflow_is_collectible() -> None:
    """Sentinel: the full-matrix marker is wired so ``make test-eval-full``
    exits 0 even when no per-repo datasets are present."""
    assert os.environ.get("EVAL_MODE", "full") in {"sampled", "full"}


@pytest.mark.eval_full
@pytest.mark.parametrize("eval_repo", ["fastapi", "httpx", "flask"])
def test_full_grounding_per_repo(eval_repo: str) -> None:
    """Full grounding eval per repo (fastapi / httpx / flask).
    Gate: grounding accuracy ≥ 90% per repo."""
    dataset = f"{eval_repo}_qa_v1.jsonl"
    _skip_if_missing(dataset)
    _skip_if_no_groq_key()
    pytest.skip(f"per-repo dataset {dataset} not yet labeled — Phase 6 task.")
