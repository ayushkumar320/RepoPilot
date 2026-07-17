"""``ArchaeologistState`` and the Pydantic v2 schema it composes.

This is the Phase 3 keystone: a single shared state object every LangGraph
node sees. The schema mirrors ``docs/03_ARCHITECTURE.md`` § "State schema
(Pydantic v2)" verbatim; if the doc and this file disagree, the doc wins
and this file is the bug.

Design rules (enforced both here and in code review — see
``docs/03_ARCHITECTURE.md`` § "State rules"):

1. Validators do real work. ``Claim.refs`` empty, ``Insight.so_what`` empty,
   ``Insight.goal_link`` empty all fail validation. The whole point is to
   surface broken upstream agents at construction time, not at render time.
2. Append-only collections use ``Annotated[list[X], add]`` so LangGraph's
   reducer composes diffs from node returns rather than letting nodes
   mutate each other's slots in place.
3. There is **no** ``purpose`` enum. Everything goal-shaped flows through
   ``IntentProfile`` / ``CapabilityPlan``.

``CodeRef`` is re-exported from ``repopilot_agents.types`` to keep the
Phase 2 tool layer's import surface intact; defining it in one place
removes the drift risk the Phase 2 docstring on that module warned about.
"""

from __future__ import annotations

from datetime import datetime
from operator import add
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from repopilot_agents.types import CodeRef

# ─── Claims & Insights ──────────────────────────────────────────────────────

ClaimStatus = Literal["unverified", "verified", "rejected", "flagged"]


class Claim(BaseModel):
    """A factual assertion produced by an agent. Must carry refs."""

    text: str = Field(min_length=1)
    refs: list[CodeRef] = Field(min_length=1)
    status: ClaimStatus = "unverified"
    verifier_note: str | None = None
    relevance: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("refs")
    @classmethod
    def _refs_non_empty(cls, v: list[CodeRef]) -> list[CodeRef]:
        if not v:
            raise ValueError("Claim must include at least one CodeRef")
        return v


class Insight(BaseModel):
    """Iteration-2 output shape — no stat dumps reach the Teacher."""

    finding: str = Field(min_length=1)
    because: str = Field(min_length=1)
    so_what: str = Field(min_length=1)
    refs: list[CodeRef] = Field(min_length=1)
    goal_link: str = Field(min_length=1)


# ─── Contribute mode ────────────────────────────────────────────────────────

Lane = Literal["A_issue", "B_quality", "C_suspicion", "D_feature"]
Difficulty = Literal["S", "M", "L"]


class RejectedItem(BaseModel):
    """A Lane A candidate shown for transparency after being ranked down."""

    title: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    evidence_refs: list[CodeRef] = Field(default_factory=list)


class Opportunity(BaseModel):
    """One unified shape across all scanner lanes."""

    lane: Lane
    title: str = Field(min_length=1)
    evidence_refs: list[CodeRef] = Field(min_length=1)
    why_this_matters: str = Field(min_length=1)
    blast_radius: str
    difficulty: Difficulty
    suggested_first_step: str = Field(min_length=1)
    files_to_touch: list[str] = Field(default_factory=list)
    nearest_tests: list[str] = Field(default_factory=list)
    confirm_before_pr: str | None = None
    mergeability: float = Field(default=0.5, ge=0.0, le=1.0)
    approachability: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_strength: float = Field(default=0.5, ge=0.0, le=1.0)
    intent_match: str | None = None
    considered_and_rejected: list[RejectedItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def _lane_c_requires_confirm(self) -> Opportunity:
        if self.lane == "C_suspicion" and not self.confirm_before_pr:
            raise ValueError(
                "Lane C suspicions must set confirm_before_pr — guarded language is required"
            )
        return self


# ─── Tour structure ─────────────────────────────────────────────────────────


class TourSection(BaseModel):
    title: str = Field(min_length=1)
    order: int = Field(ge=0)
    claims: list[Claim] = Field(default_factory=list)
    mermaid: str | None = None


# ─── Verifier ───────────────────────────────────────────────────────────────


class ArchaeologistError(BaseModel):
    """Every fail-edge in the graph emits one of these."""

    code: Literal[
        "NO_PYTHON_CONTENT",
        "PYTHON2_SYNTAX_WARNING",
        "PERSIST_FAILED",
        "VERIFIER_UNAVAILABLE",
        "EMBEDDINGS_UNAVAILABLE",
        "QA_NO_RESULTS",
        "REPO_UNAVAILABLE",
        "REPO_TOO_LARGE",
        "CHUNK_CONTENT_MISSING",
        "GRAPH_BUILD_FAILED",
        "QUOTA_EXHAUSTED",
        "INDEX_STALE",
    ]
    message: str
    detail: str | None = None
    stage: str | None = None


class VerifierObjection(BaseModel):
    section_order: int = Field(ge=0)
    claim_text: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    suggested_fix: str | None = None


# ─── Generic intent layer ───────────────────────────────────────────────────

Modality = Literal["understand", "change", "evaluate", "locate", "compare"]
OutputShape = Literal["narrative", "ranked_list", "dossier", "comparison_table", "unspecified"]


class IntentProfile(BaseModel):
    """Free-text intent in, structured tilt out. No fixed purpose enum."""

    raw_text: str = Field(min_length=1)
    modality_weights: dict[Modality, float] = Field(default_factory=dict)
    focus_keywords: list[str] = Field(default_factory=list)
    audience_framing: str | None = None
    output_shape_preference: OutputShape = "unspecified"
    success_criterion: str | None = None

    @field_validator("modality_weights")
    @classmethod
    def _weights_in_unit_interval(cls, v: dict[Modality, float]) -> dict[Modality, float]:
        if any(w < 0 or w > 1 for w in v.values()):
            raise ValueError("modality weights must be in [0, 1]")
        return v


# ─── Capability planning ────────────────────────────────────────────────────

CapabilityName = Literal[
    "cartographer",
    "flow_tracer",
    "lane_a_issue_triage",
    "lane_b_code_health",
    "lane_c_suspicion",
    "decision_archaeology",
    "teacher",
]


class CapabilityPlan(BaseModel):
    """Deterministic Planner output. Verifiable in CI."""

    active: list[CapabilityName] = Field(min_length=1)
    dependencies: dict[CapabilityName, list[CapabilityName]] = Field(default_factory=dict)
    tilts: dict[CapabilityName, dict[str, Any]] = Field(default_factory=dict)
    output_shape: OutputShape
    cartographer_tilt: str | None = None
    flow_tracer_targets: list[str] = Field(default_factory=list)
    lane_b_framing: str | None = None
    ranker_weights: dict[str, float] = Field(default_factory=dict)

    @field_validator("dependencies")
    @classmethod
    def _deps_subset_of_active(
        cls,
        v: dict[CapabilityName, list[CapabilityName]],
        info: ValidationInfo,
    ) -> dict[CapabilityName, list[CapabilityName]]:
        active = set(info.data.get("active", []))
        for cap, deps in v.items():
            if cap not in active:
                raise ValueError(f"dependency declared for inactive capability: {cap}")
            for d in deps:
                if d not in active:
                    raise ValueError(f"{cap} depends on inactive capability {d}")
        return v


# ─── Q&A history ────────────────────────────────────────────────────────────


class QAExchange(BaseModel):
    """One completed Q&A turn. v1 keeps the last 8; the prompt only consumes
    the current ``user_question`` (multi-turn is a v0.2 prompt-shape change)."""

    question: str = Field(min_length=1)
    answer_claims: list[Claim] = Field(default_factory=list)
    asked_at: datetime


# ─── Top-level state ────────────────────────────────────────────────────────


class ArchaeologistState(BaseModel):
    """The single shared LangGraph state. See ``docs/03_ARCHITECTURE.md``."""

    # — identity —
    repo_id: str = Field(min_length=1)
    repo_url: str = Field(min_length=1)

    # — generic intent layer —
    intent_profile: IntentProfile | None = None
    capability_plan: CapabilityPlan | None = None
    user_question: str | None = None
    qa_history: Annotated[list[QAExchange], add] = Field(default_factory=list)

    # — capability outputs (any subset, depending on the plan) —
    system_map: Annotated[list[Insight], add] = Field(default_factory=list)
    traced_flows: Annotated[list[Insight], add] = Field(default_factory=list)
    triaged_issues: Annotated[list[Opportunity], add] = Field(default_factory=list)
    opportunity_list: Annotated[list[Opportunity], add] = Field(default_factory=list)
    ranked_opportunity_list: list[Opportunity] = Field(default_factory=list)
    decision_dossier: Annotated[list[Insight], add] = Field(default_factory=list)

    # — output —
    draft_tour: Annotated[list[TourSection], add] = Field(default_factory=list)

    # — verifier loop —
    verifier_objections: Annotated[list[VerifierObjection], add] = Field(default_factory=list)
    retry_count: dict[int, int] = Field(default_factory=dict)

    # — observability —
    tokens_used: dict[str, int] = Field(default_factory=dict)
    errors: Annotated[list[str], add] = Field(default_factory=list)


__all__ = [
    "ArchaeologistError",
    "ArchaeologistState",
    "CapabilityName",
    "CapabilityPlan",
    "Claim",
    "ClaimStatus",
    "CodeRef",
    "Difficulty",
    "Insight",
    "IntentProfile",
    "Lane",
    "Modality",
    "Opportunity",
    "OutputShape",
    "QAExchange",
    "RejectedItem",
    "TourSection",
    "VerifierObjection",
]
