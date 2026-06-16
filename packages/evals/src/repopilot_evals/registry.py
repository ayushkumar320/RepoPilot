"""The eval registry — one row per phase-gating eval.

Every CLI / CI / status surface reads from this list, so adding a new eval
means appending one ``EvalSpec`` instead of editing N files. Keeps the
harness aligned with RepoPilot's "single source of truth" principle.

``phase`` is the phase the gate belongs to; ``needs_llm`` flags evals that
will burn LLM tokens (so free-tier mode can opt out cleanly); ``needs_indexed_repo``
flags evals that require an ingested repo in Postgres (slow-lane gate dependency).
"""

from __future__ import annotations

from dataclasses import dataclass

from pathlib import Path

from repopilot_evals.datasets import (
    DATASETS_DIR,
    dataset_path,
)


@dataclass(frozen=True, slots=True)
class EvalSpec:
    name: str
    phase: int
    dataset: str
    gate: float
    headline_metric: str
    description: str
    needs_llm: bool
    needs_indexed_repo: bool

    @property
    def dataset_path(self) -> Path:
        return dataset_path(self.dataset)

    @property
    def dataset_present(self) -> bool:
        return bool(self.dataset_path.exists())


REGISTRY: tuple[EvalSpec, ...] = (
    EvalSpec(
        name="grounding",
        phase=2,
        dataset="httpx_qa_v1.jsonl",
        gate=0.90,
        headline_metric="grounding_accuracy",
        description="Q&A grounding accuracy — claims carry verified refs and don't hallucinate on not-in-repo questions.",
        needs_llm=True,
        needs_indexed_repo=True,
    ),
    EvalSpec(
        name="verifier",
        phase=2,
        dataset="verifier_quality_v1.jsonl",
        gate=0.92,
        headline_metric="accuracy",
        description="Verifier accuracy — supported/rejected decisions against hand-labeled (claim, chunk) pairs.",
        needs_llm=True,
        needs_indexed_repo=False,
    ),
    EvalSpec(
        name="intent_profiler",
        phase=3,
        dataset="intent_profiling_v1.jsonl",
        gate=0.90,
        headline_metric="per_field_accuracy",
        description="Intent Profiler — per-field accuracy on (free-text intent → IntentProfile) extractions.",
        needs_llm=True,
        needs_indexed_repo=False,
    ),
    EvalSpec(
        name="planner",
        phase=3,
        dataset="planner_correctness_v1.jsonl",
        gate=0.90,
        headline_metric="active_capabilities_f1",
        description="Capability Planner — F1 on activated-capabilities set + exact-match on output_shape. Deterministic; no LLM.",
        needs_llm=False,
        needs_indexed_repo=False,
    ),
)


def get_spec(name: str) -> EvalSpec:
    for spec in REGISTRY:
        if spec.name == name:
            return spec
    raise KeyError(f"unknown eval: {name!r}. Known: {[s.name for s in REGISTRY]}")


__all__ = ["DATASETS_DIR", "EvalSpec", "REGISTRY", "get_spec"]
