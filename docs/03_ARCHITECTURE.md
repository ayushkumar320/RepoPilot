# 03 — Architecture

This is the design document. It is detailed by intent: getting the topology, state schema, and verification loop right is the entire architectural keystone. Phases 0–6 are mostly an exercise in faithfully implementing what is specified here.

---

## Agent topology

```
                              user submits repo URL + free-text intent
                                              │
                                              ▼
   ┌──────────────────────────────────────────────────────────────────────────┐
   │   GENERIC INTENT LAYER (universal — runs for every user, every time)     │
   │                                                                          │
   │   ┌─────────────────────────────┐    ┌────────────────────────────────┐  │
   │   │     Intent Profiler         │    │     Capability Planner          │  │
   │   │  (llama-3.1-8b-instant)     │───►│      (deterministic)            │  │
   │   │                             │    │                                 │  │
   │   │ free-text  ──► IntentProfile│    │ IntentProfile ─► plan: which    │  │
   │   │  intent          {modality, │    │   capabilities run, with what   │  │
   │   │                   focus_kw, │    │   tilts. Deterministic; no LLM. │  │
   │   │                   audience, │    │                                 │  │
   │   │                   shape,    │    │                                 │  │
   │   │                   raw_text} │    │                                 │  │
   │   └──────────────┬──────────────┘    └────────────────┬────────────────┘  │
   │                  │ (user confirms via chip strip)     │                   │
   └──────────────────┼─────────────────────────────────────┼───────────────────┘
                      │                                     │
                      │                                     ▼
                      │                  ┌──────────────────────────────────┐
                      │                  │  DYNAMIC PLAN over the           │
                      │                  │  CAPABILITY LIBRARY              │
                      │                  │                                  │
                      │                  │  Any subset of, in any tilt:     │
                      │                  │   · Cartographer (70B)           │
                      │                  │   · Flow Tracer (qwen3-32b)      │
                      │                  │   · Lane A Issue Triage (70B)    │
                      │                  │   · Lane B Code Health (8B)      │
                      │                  │   · Lane C Suspicion (qwen3-32b) │
                      │                  │   · Decision Archaeology (70B)   │
                      │                  │   · Teacher (70B) [terminal]     │
                      │                  └────────────────┬─────────────────┘
                      │                                   │
                      ▼                                   ▼
   ┌─────────────────────────────────────────────────────────────────────────┐
   │              VERIFIER LOOP (universal — wraps every capability)         │
   │             qwen2.5-coder:7b (local Ollama)                             │
   │                                                                         │
   │   Per-claim grounding check against read_chunks                         │
   │   + Iteration-2 actionability rubric                                    │
   │                                                                         │
   │   pass → stream to client                                               │
   │   fail → append to verifier_objections → source retries ≤ 2 →           │
   │          render as "flagged" if still failing                           │
   └─────────────────────────────────────────────────────────────────────────┘
                      │
                      ▼
              SSE stream to browser
              (section_start / token / claim /
               diagram / section_end / done)
                      ▲
                      │ (always-on, cross-cutting)
   ┌─────────────────────────────────────────────────────────────────────────┐
   │     Q&A SUBGRAPH (universal — available throughout, for every user)     │
   │     Hybrid retrieval (≤3 hops):                                         │
   │       vector_search → graph_traverse → judge sufficiency                │
   │     Reads the same IntentProfile; answers are framed accordingly.       │
   │     Drives the synchronized code viewer just like tour claims do.       │
   └─────────────────────────────────────────────────────────────────────────┘
```

A few topology notes the diagram alone doesn't show:

- **There are three universal layers and one dynamic layer.** The Generic Intent Layer (top), the Verifier Loop (wraps everything), and the Q&A Subgraph (always-on cross-cutting concern) run for *every* user every time, regardless of what they stated. The Dynamic Plan over the Capability Library is the *only* layer that varies per intent. This separation is the architectural property that makes the system purpose-elastic without a tangle of per-persona code paths.
- **No fixed purpose enum, no fixed lens enum.** The Intent Profiler takes free text and emits a structured `IntentProfile`. Anything a user can articulate is supported. Adding a new kind of stated intent never requires schema changes — only (possibly) a new planner heuristic, and only if existing heuristics don't already produce a good plan.
- **The Capability Planner is deterministic.** It is not an LLM. It maps `IntentProfile → plan` via testable rules. This is deliberate: planning correctness is verifiable in CI, and the planner does not consume Groq quota.
- **The capability library is independently invocable.** Each block (Cartographer, Flow Tracer, Lane A/B/C, Decision Archaeology, Teacher, Q&A) takes the `IntentProfile` as input and runs standalone. The library has no internal "this only makes sense if X also ran" assumptions. This is what lets the planner compose freely.
- **Q&A is universal, not branched.** It is a cross-cutting concern available throughout the lifecycle — before the tour, during the tour, after the tour. It reads the same `IntentProfile` as every other capability, so answers are always goal-anchored. It drives the synchronized code viewer the same way tour claims do.
- **The Verifier wraps every generating capability**, with a conditional retry edge back to the source. It is a sub-graph that fires repeatedly across the run, not a single terminal node.
- **One shared `ArchaeologistState`.** No subgraph owns its own state; the graph applies typed diffs from each capability's returns.
- **Capabilities the planner activates in parallel run in parallel.** LangGraph concurrency handles this — e.g., Lane A/B/C in the contribute-shaped plans, or Cartographer + Decision Archaeology in the build-shaped plans.

---

## Agent table

| Agent | Model | Job | Tools | Reads from state | Writes to state |
|---|---|---|---|---|---|
| **Intent Profiler** | `llama-3.1-8b-instant` | **Generic intent layer, step 1.** Reads the user's free-text intent statement. Emits a structured `IntentProfile` (modality_weights, focus_keywords, audience_framing, output_shape_preference, raw_text). Runs on every user, every time. Always the first node. | (none) | `repo_url`, user's free-text intent | `intent_profile` (draft) |
| **Capability Planner** | (deterministic, no LLM) | **Generic intent layer, step 2.** Reads the confirmed `IntentProfile` and emits a `CapabilityPlan`: which capabilities to activate, in what order, and with what tilt parameters. Deterministic rules — verifiable in CI, consumes no LLM quota. | (none) | `intent_profile` | `capability_plan` |
| **Cartographer** | `llama-3.3-70b-versatile` | (Optional, planner-activated.) Build the system map: entry points (in-degree 0), hubs (top fan-in), layers (community detection). **Tilt parameters from `capability_plan.cartographer_tilt`** select hub-selection bias (import-graph hubs / data-shaped hubs / hot-path hubs / decision-shaped hubs) and subsystem narrowing via `intent_profile.focus_keywords`. Emit `Insight` objects — never raw metrics. | `graph_query`, `graph_metrics`, `read_chunks` | `repo_id`, `intent_profile`, `capability_plan` | `system_map[]` |
| **Flow Tracer** | `qwen3-32b` | (Optional, planner-activated.) Pick one or more end-to-end flows aligned with `capability_plan.flow_tracer_targets`. Walk each via graph traversal. Emit Insight objects per step. The Insight's `goal_link` cites the active part of the profile. | `graph_traverse`, `read_chunks` | `system_map`, `intent_profile`, `capability_plan` | `traced_flows[]` |
| **Teacher** | `llama-3.3-70b-versatile` | (Terminal capability, almost always activated.) Sequences whichever capabilities ran into a coherent output. Output shape (`narrative` / `ranked_list` / `dossier` / `comparison_table`) and audience framing come from `intent_profile`. Every section ends in motion. Emits mermaid when shape is `narrative`. Lead paragraph echoes the user's `raw_text` intent. | `read_chunks` | `intent_profile`, plus any of `system_map`, `traced_flows`, `opportunity_list`, `decision_dossier` | `draft_tour[]` |
| **Lane A — Issue Triage** | `llama-3.3-70b-versatile` | (Optional, planner-activated.) Score open issues by **graph-backed approachability** (blast radius, callers, isolation). Filter by `intent_profile.focus_keywords`. | `github_issues`, `graph_metrics`, `read_chunks` | `repo_url`, `intent_profile` | `triaged_issues[]`, contributes to `opportunity_list[]` |
| **Lane B — Code Health** | `llama-3.1-8b-instant` | (Optional, planner-activated.) Rank deterministic quality signals (hot-untested, missing docstrings, AST dup, dead code, churn × complexity, TODO archaeology). Teacher framing — cleanup-opportunities vs. tradeoffs-visible-in-code — comes from `capability_plan.lane_b_framing`. | `graph_metrics`, `read_chunks` | `repo_id`, `intent_profile` | contributes to `opportunity_list[]` |
| **Lane C — Suspicion** | `qwen3-32b` | (Optional, planner-activated.) Explain pre-filtered structural anomalies with guarded language. Every suspicion includes a `to_confirm:` step. Detector subset filterable by `focus_keywords` (security-shaped, async-shaped, IO-shaped). | `graph_metrics`, `read_chunks` | `repo_id`, `intent_profile` | contributes to `opportunity_list[]` |
| **Decision Archaeology** | `llama-3.3-70b-versatile` | (Optional, planner-activated.) Reads `git log`, README, commit messages, and the import graph to extract architectural decisions + rationale. Activated when `modality_weights.evaluate` is high or `audience_framing` is build-vs-buy / paper / competitive. | `graph_query`, `graph_metrics`, `read_chunks`, GitPython | `repo_id`, `intent_profile` | `decision_dossier[]` |
| **Opportunity Ranker** | (deterministic, no LLM) | Combine Lane A/B/C outputs into a single ranked `opportunity_list`. Ranking weights read from `capability_plan.ranker_weights` (planner-derived from `intent_profile.modality_weights`). | (none) | A, B, C outputs, `capability_plan` | `opportunity_list[]` |
| **Q&A** | `llama-3.3-70b-versatile` (qwen3-32b fallback) | **Universal — always-on, available throughout the lifecycle.** Hybrid retrieval loop with sufficiency judge, ≤ 3 hops. Reads `intent_profile` to frame the answer. Drives the synchronized code viewer like any tour claim. | `vector_search`, `graph_traverse`, `read_chunks` | `user_question`, `repo_id`, `intent_profile` | `draft_tour[]` (appended) |
| **Verifier** | `qwen2.5-coder:7b` (Ollama) | **Universal.** Per-claim grounding check against `read_chunks` PLUS Iteration-2 actionability rubric (goal-relevance against `intent_profile`). Wraps every generating capability. | `read_chunks` | `draft_tour[]` (latest section), `intent_profile` | `verifier_objections[]`, mutates `claim.status` |

---

## State schema (Pydantic v2)

This is the contract between agents. Every architectural decision flows from it.

```python
from __future__ import annotations
from typing import Annotated, Literal
from pydantic import BaseModel, Field, field_validator
from operator import add  # reducer for append-only lists


# ─── References ─────────────────────────────────────────────────────────────

class CodeRef(BaseModel):
    """A pointer into the repo. Every factual claim must carry at least one."""
    file_path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    symbol: str | None = None  # e.g. "MyClass.my_method"

    @field_validator("end_line")
    @classmethod
    def _end_after_start(cls, v: int, info) -> int:
        if v < info.data["start_line"]:
            raise ValueError("end_line must be >= start_line")
        return v


# ─── Claims & Insights ──────────────────────────────────────────────────────

ClaimStatus = Literal["unverified", "verified", "rejected", "flagged"]


class Claim(BaseModel):
    """A factual assertion produced by an agent. Must carry refs."""
    text: str
    refs: list[CodeRef] = Field(min_length=1)
    status: ClaimStatus = "unverified"
    verifier_note: str | None = None
    relevance: float = 1.0  # how relevant to user's goal, 0..1

    @field_validator("refs")
    @classmethod
    def _refs_non_empty(cls, v: list[CodeRef]) -> list[CodeRef]:
        if not v:
            raise ValueError("Claim must include at least one CodeRef")
        return v


class Insight(BaseModel):
    """
    The shape required for Iteration-2 (no stat dumps).
    Raw metrics never reach the Teacher — they are transformed into Insights first.
    """
    finding: str                # what we observed
    because: str                # the structural/AST/graph reason
    so_what: str = Field(min_length=1)   # consequence for the user's goal
    refs: list[CodeRef] = Field(min_length=1)
    goal_link: str = Field(min_length=1) # how this maps to intent_profile (raw_text / focus_keywords / audience_framing)

    # Empty so_what or goal_link fails validation. This is intentional.


# ─── Contribute mode ────────────────────────────────────────────────────────

Lane = Literal["A_issue", "B_quality", "C_suspicion", "D_feature"]
Difficulty = Literal["S", "M", "L"]


class Opportunity(BaseModel):
    """One unified shape across all scanner lanes."""
    lane: Lane
    title: str
    evidence_refs: list[CodeRef] = Field(min_length=1)
    why_this_matters: str
    blast_radius: str            # e.g. "isolated", "module-scoped", "hub"
    difficulty: Difficulty
    suggested_first_step: str
    files_to_touch: list[str]
    nearest_tests: list[str]
    confirm_before_pr: str | None = None  # Lane C suspicions REQUIRE this


# ─── Tour structure ─────────────────────────────────────────────────────────

class TourSection(BaseModel):
    title: str
    order: int
    claims: list[Claim]
    mermaid: str | None = None       # optional diagram for this section


# ─── Verifier ───────────────────────────────────────────────────────────────

class VerifierObjection(BaseModel):
    section_order: int
    claim_text: str
    reason: str                       # "ungrounded" | "no next action" | "off-goal" | ...
    suggested_fix: str | None = None


# ─── Generic intent layer ───────────────────────────────────────────────────

# Modality is continuous, not categorical. Any combination is valid. Open-ended literal set
# (we constrain to five well-understood axes; nothing about the architecture forbids extending it).
Modality = Literal["understand", "change", "evaluate", "locate", "compare"]

# Output shape can be unspecified — the Teacher picks based on the profile when so.
OutputShape = Literal["narrative", "ranked_list", "dossier", "comparison_table", "unspecified"]


class IntentProfile(BaseModel):
    """
    The product of the Intent Profiler. Free-text intent in, structured tilt out.
    There is NO fixed enum of "purposes". Anything a user can articulate is supported.
    """
    raw_text: str = Field(min_length=1)          # the user's exact sentence — preserved verbatim
    modality_weights: dict[Modality, float] = Field(default_factory=dict)
    focus_keywords: list[str] = Field(default_factory=list)
    audience_framing: str | None = None          # "for a PR" | "for internal docs" | "for a security report" | …
    output_shape_preference: OutputShape = "unspecified"
    success_criterion: str | None = None         # profiler-suggested measurable success condition; user-editable

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
    # NOTE: q_and_a is universal/always-on, not planner-activated; not listed here.
    # NOTE: the verifier is universal too; it wraps every active capability.
]


class CapabilityPlan(BaseModel):
    """
    The product of the Capability Planner. Deterministic, derivable from IntentProfile.
    No LLM. Verifiable in CI.
    """
    active: list[CapabilityName] = Field(min_length=1)
    tilts: dict[CapabilityName, dict] = Field(default_factory=dict)
    output_shape: OutputShape
    # Typed knobs for the most common tilts (still expressible via `tilts` for novelty):
    cartographer_tilt: str | None = None      # "balanced" | "data_hubs" | "decision_hubs" | "hot_path" | …
    flow_tracer_targets: list[str] = Field(default_factory=list)
    lane_b_framing: str | None = None         # "cleanup_opportunities" | "tradeoffs_visible_in_code"
    ranker_weights: dict[str, float] = Field(default_factory=dict)  # e.g. {"A": 0.6, "B": 0.3, "C": 0.1}


# ─── Top-level state ────────────────────────────────────────────────────────

class ArchaeologistState(BaseModel):
    # — identity —
    repo_id: str
    repo_url: str

    # — generic intent layer (set in this order, before any capability runs) —
    intent_profile: IntentProfile | None = None       # Intent Profiler output, user-confirmed
    capability_plan: CapabilityPlan | None = None     # Capability Planner output
    user_question: str | None = None                  # Q&A inputs land here (Q&A is universal)

    # — Capability outputs (any subset may exist depending on the plan) —
    system_map: Annotated[list[Insight], add] = Field(default_factory=list)
    traced_flows: Annotated[list[Insight], add] = Field(default_factory=list)
    triaged_issues: Annotated[list[Opportunity], add] = Field(default_factory=list)
    opportunity_list: Annotated[list[Opportunity], add] = Field(default_factory=list)
    decision_dossier: Annotated[list[Insight], add] = Field(default_factory=list)

    # — Output —
    draft_tour: Annotated[list[TourSection], add] = Field(default_factory=list)

    # — Verifier loop —
    verifier_objections: Annotated[list[VerifierObjection], add] = Field(default_factory=list)
    retry_count: dict[int, int] = Field(default_factory=dict)

    # — Observability —
    tokens_used: dict[str, int] = Field(default_factory=dict)
    errors: Annotated[list[str], add] = Field(default_factory=list)
```

**State rules (enforced in code review, not in comments):**

1. **No agent writes another agent's field.** Use Python's typed return values. The reducer composes the diff.
2. **Mutations only via node returns.** Never `state.foo.append(...)`. Always `return {"foo": [new_item]}`.
3. **Reducer on append-only collections.** Verifier objections, errors, system_map, traced_flows, opportunity_list, decision_dossier, draft_tour all use `Annotated[..., add]`.
4. **`recursion_limit=15`.** Anything beyond is a loop bug. Found cheaper here than in production.
5. **Validators do real work.** `Insight.so_what` empty → validation error → the bug is at the source node, not in the Teacher.
6. **The generic intent layer must complete before any capability runs.** A capability node guard raises if `state.intent_profile is None` or `state.capability_plan is None`. The Q&A subgraph is exempt from this guard *only* in the case where the user asks a question before any tour starts — then the Q&A node creates a minimal `IntentProfile` from the question itself (which the Intent Profiler can do in one pass).
7. **No capability code path depends on a "purpose" enum.** If you find yourself writing `if state.purpose == "learn":` you've reintroduced the bucketed model and broken the elasticity property. Capability behavior is parameterized by `intent_profile` + the capability's tilt entry in `capability_plan` — nothing else.

---

## Deterministic tools

The tools layer is the truthfulness floor. **The LLMs never compute these. They only ask.**

| Tool | Signature | What it returns |
|---|---|---|
| `vector_search(query: str, k: int=8) -> list[ChunkHit]` | Embed query, k-NN over pgvector. | Top-k chunks with file:line spans + cosine distance. |
| `graph_traverse(start: str, edge_types: list[str], max_depth: int=3) -> list[Path]` | BFS from a symbol along call/import/inheritance edges. | All paths up to depth, each as a list of `CodeRef`. |
| `graph_query(kind: Literal["entry_points","hubs","layers","callers","callees"], symbol: str | None = None) -> list[GraphResult]` | Structural queries against the NetworkX graph. | Entry points = in-degree 0. Hubs = top-N fan-in. Layers = Louvain communities. |
| `graph_metrics(symbol: str) -> SymbolMetrics` | One-symbol metric pack: fan-in, fan-out, cyclomatic complexity, churn, has-tests bit. | Used by Lane A/B/C and Cartographer. |
| `read_chunks(refs: list[CodeRef]) -> list[ChunkContent]` | Read exact chunks by file:line. | The only way an agent sees source text. Verifier uses this too. |
| `github_issues(repo_url: str, state: str="open") -> list[Issue]` | PyGithub fetch with caching. | Raw issues for Lane A. Lane A then scores via `graph_metrics`. |

**Why these and not more.** Every additional tool is a surface where an agent might invent. Six tools is enough. Any new tool needs a justification that begins with "the model cannot do this from existing tools because…".

---

## Hybrid retrieval pattern (the Q&A spine)

```
user_question
     │
     ▼
┌────────────────────────────┐
│  vector_search(question)   │   ◄── FINDS plausibly relevant chunks
│   top-k = 8                 │
└──────────┬─────────────────┘
           ▼
┌────────────────────────────┐
│ graph_traverse from         │   ◄── COMPLETES the context (callers,
│ each hit's symbol           │       callees, definitions)
│ edge_types depends on Q     │
└──────────┬─────────────────┘
           ▼
┌────────────────────────────┐
│ Q&A judge: "is this enough  │   ◄── BOUND by hop budget (≤3)
│  to answer?"                │
└──────────┬─────────────────┘
           │ no → expand (re-search or traverse further)
           │ yes ↓
┌────────────────────────────┐
│ generate answer w/ refs     │
└──────────┬─────────────────┘
           ▼
       Verifier
```

**Key property:** vector_search alone is insufficient — it finds the function but not its callers; the user needs the caller chain to understand what to change. graph_traverse alone is insufficient — without a vector seed it has no idea where to start. The two operations compose; neither replaces the other.

---

## The Capability Planner

The Planner is the deterministic heart of elasticity. It is a Python function: `plan(IntentProfile) -> CapabilityPlan`. No LLM. No state mutation. Pure transformation. Verifiable in CI on a labeled set of `(IntentProfile, expected CapabilityPlan)` pairs.

The Planner's job is to encode "which subset of the capability library serves this intent, and how to tilt each member of the subset." A starter rule sketch (this is the v1 implementation; the file evolves):

```python
def plan(p: IntentProfile) -> CapabilityPlan:
    active: list[CapabilityName] = []
    tilts: dict[CapabilityName, dict] = {}

    understand = p.modality_weights.get("understand", 0)
    change     = p.modality_weights.get("change", 0)
    evaluate   = p.modality_weights.get("evaluate", 0)
    locate     = p.modality_weights.get("locate", 0)
    compare    = p.modality_weights.get("compare", 0)

    # Cartographer: needed whenever we're producing structural understanding
    # or whenever narrowing by focus_keywords is requested.
    if understand >= 0.2 or evaluate >= 0.2 or locate >= 0.3 or p.focus_keywords:
        active.append("cartographer")
        tilts["cartographer"] = {
            "hub_bias": _pick_hub_bias(p),     # data / decision / hot_path / balanced
            "narrow_to": p.focus_keywords,
        }

    # Flow Tracer: needed when the user wants to understand a path / lifecycle.
    if understand >= 0.4 or "lifecycle" in p.raw_text.lower():
        active.append("flow_tracer")
        tilts["flow_tracer"] = {"targets": _infer_flow_targets(p)}

    # Lane A: needed when the user wants to ship a PR against the issue tracker.
    if change >= 0.4 and ("issue" in p.raw_text.lower() or "PR" in p.raw_text):
        active.append("lane_a_issue_triage")

    # Lane B: needed for quality cleanup work AND for surfacing tradeoffs.
    if change >= 0.3 or evaluate >= 0.4:
        active.append("lane_b_code_health")
        tilts["lane_b_code_health"] = {
            "framing": "tradeoffs_visible_in_code" if evaluate > change else "cleanup_opportunities",
        }

    # Lane C: needed for fragility / problem hunting / security audits.
    fragility_signal = any(k in p.raw_text.lower()
                           for k in ("fragile", "problem", "audit", "security", "vulnerab"))
    if change >= 0.3 and (fragility_signal or "hunt" in p.raw_text.lower()):
        active.append("lane_c_suspicion")
        tilts["lane_c_suspicion"] = {"keyword_filter": p.focus_keywords}

    # Decision Archaeology: needed when the user wants the "why" behind choices.
    if evaluate >= 0.4 or compare >= 0.3 or "decision" in p.raw_text.lower():
        active.append("decision_archaeology")

    # Teacher: terminal capability; almost always activated.
    active.append("teacher")

    shape = p.output_shape_preference if p.output_shape_preference != "unspecified" \
            else _infer_shape(active, p)

    return CapabilityPlan(
        active=active,
        tilts=tilts,
        output_shape=shape,
        cartographer_tilt=tilts.get("cartographer", {}).get("hub_bias"),
        flow_tracer_targets=tilts.get("flow_tracer", {}).get("targets", []),
        lane_b_framing=tilts.get("lane_b_code_health", {}).get("framing"),
        ranker_weights=_derive_ranker_weights(p) if "lane_a_issue_triage" in active else {},
    )
```

**Why deterministic.** A planner that uses an LLM creates two problems: (1) every quota hit is a planning failure, not just a generation failure; (2) verifying "the planner does the right thing" becomes verifying an LLM, which is expensive and probabilistic. A rule-based planner is testable on a labeled set in milliseconds.

**Why this is enough flexibility.** Any intent the user can articulate gets a plan: the rules read both structured `modality_weights` and the `raw_text` for keyword signals. New stated intents either fall through existing rules (the common case) or trigger a new rule (rare, and a one-line addition). Adding a new capability (say, a Security Scanner) means: (a) adding the capability to the library, (b) adding a rule like *"if `focus_keywords` includes a security term OR raw text contains `audit|security|vulnerab`, activate `security_scanner`."* No restructuring.

**Why this is not just "if statements over a hidden enum."** The rules read continuous weights and free-text signals. Two users with very different stated intents can produce the same plan (e.g., a learner asking "explain async" and an evaluator asking "how solid is their async story" both get `cartographer + flow_tracer + teacher` — but the *tilts* differ because their `audience_framing` and `modality_weights` differ). And any intent that doesn't match an existing rule falls through to a default plan (`cartographer + teacher + narrative`) instead of erroring — the system is open, not closed.

---

## Q&A drives the synchronized code viewer

The Q&A subgraph is the user's escape hatch, but its answers are not text-only. Every Q&A answer carries the same `Claim[]` structure as tour sections — meaning every Q&A claim has `refs[]`, and **the UI scrolls the synchronized code viewer to the first ref of the first claim automatically** on answer. The user asks "where does the request lifecycle start?" and the viewer opens the file at the function. This is the synchronized code viewer pulled through the entire product, not just the scripted tour.

Implementation note: the SSE stream for Q&A answers emits the same `claim` events as the tour. The frontend's claim → code-viewer reducer is the same handler in both modes.

---

## Trust surfaces — how moats become visible

The architecture's distinguishing properties are only differentiating if the user can see them. Four UI affordances exist specifically to make moats legible:

| Surface | What the user sees | What it proves |
|---|---|---|
| **Verified badge** | `✓ grounded` badge per claim where `status == "verified"`. Hover: the chunk the verifier used + the verifier's one-line confirmation. | A separate model checked this against actual source — not just the generator's confidence. |
| **Retrieval path** | `vector_search → graph_traverse (2 hops)` chip per claim. Hover: the intermediate symbols traversed. | We didn't just do a vector lookup. The graph completed the context. |
| **Intent-match chip** | Every Opportunity carries `matches: hunt problems` (or whichever intent was captured). | The output is goal-anchored, not generic. The user can point at the chain back to their pre-context. |
| **Considered-and-rejected trail (Lane A)** | "We looked at #234 but ranked it lower because it touches a hub of fan-in 47." Top-3 rejected items shown below the top-N accepted. | The triage is graph-backed, not label-driven. Lane A is doing real work, not parroting `good first issue`. |

These surfaces are required deliverables in Phase 4 (verified badge, retrieval path, intent chip) and Phase 5 (considered-and-rejected trail). Without them, the architectural moat does not reach the user.

---

## How the intent profile flows through the system

| Step | What gets captured / used |
|---|---|
| **User opens app** | Indexing job enqueued in the background. Free-text intent box is the first thing the user sees. |
| **Intent Profiler fires** | Reads the user's free-text intent and emits a draft `IntentProfile` (modality_weights, focus_keywords, audience_framing, output_shape_preference, suggested success_criterion). |
| **User confirms via chip strip** | The draft profile renders as a compact "I'll focus on X · Y · Z, framed for W. Edit?" strip. User accepts, edits a chip, or rewrites the raw text. Confirmed `IntentProfile` is now committed to state. |
| **Capability Planner fires** | Deterministic. Reads `intent_profile`, emits `capability_plan` (which capabilities to activate, in what order, with what tilts). No LLM, no quota. |
| **Active capabilities run (possibly in parallel)** | LangGraph activates only the capability nodes named in `capability_plan.active`. Each reads `intent_profile` and its own entry in `capability_plan.tilts`. Capabilities the planner did not activate do not run — that is the elasticity. |
| **Verifier wraps every generating capability** | Per-claim grounding check + actionability rubric. The rubric checks goal-relevance against `intent_profile`, not against any fixed purpose enum. |
| **Teacher composes the output** | Reads `intent_profile.output_shape_preference` (and `capability_plan.output_shape` if the planner overrode it) to choose narrative / ranked_list / dossier / comparison_table. Audience framing comes from `intent_profile.audience_framing`. Lead paragraph echoes `intent_profile.raw_text` verbatim. |
| **Q&A is reachable throughout** | Universal, cross-cutting. Reads the same `intent_profile`. Drives the synchronized code viewer. Available before, during, and after the planned capabilities have run. |
| **User changes their mind** | The "You said:" chip strip stays editable. Editing the intent re-runs the Profiler + Planner only — no re-indexing. Capabilities that are still relevant under the new plan reuse their cached output; newly-activated capabilities run; deactivated ones don't. |

The traceability property: for every paragraph the user sees, they can point at the entry in `intent_profile` and the capability in `capability_plan` that produced it. This is what "meet the purpose" looks like in practice when the purpose is open-ended.

### What "always-on" means for Q&A specifically

The Q&A subgraph is not a node in the planned pipeline — it is a separate subgraph reachable from any state. Concretely:

- A user can ask a question **before** any planned capability runs. In that case Q&A constructs a minimal `IntentProfile` from the question itself (single-pass profiler call) so the answer still gets framed and so the trust spine still applies.
- A user can ask a question **between** planned capabilities. The Q&A subgraph reads whatever capability outputs exist so far; if it needs context the planned pipeline hasn't produced yet, it falls back to hybrid retrieval over the indexed repo.
- A user can ask a question **after** the planned pipeline completes. Q&A reads the full state and the full `IntentProfile`.

This is what the user means by "Q&A is for everyone" — there is no Q&A-vs-non-Q&A user. Every user has Q&A available the whole time. Every Q&A answer is verified by the same Verifier. Every Q&A answer drives the same synchronized code viewer.

---

## Iteration 1 — Contribute lanes, in detail

### Lane A — Issue Triage

```
PyGithub fetch open issues
        │
        ▼
For each issue:
  Extract referenced files/symbols (regex + NER)
  ─► graph_metrics(symbol)
       fan-in, isolation, has_tests
  Score approachability:
    + small blast radius
    + isolated (low fan-in)
    + has nearby tests
    − touches a hub
    − no tests anywhere near
        │
        ▼
Top-N → LLM (70B) writes
the Opportunity record
```

**Critical:** GitHub labels (`good first issue`, etc.) are an **input signal**, not the ranking. Labels are inconsistent across maintainers. The graph metric is the source of truth.

### Lane B — Quality Scanner

| Signal | Detection | Why mergeable |
|---|---|---|
| **Untested hot code** | fan-in ≥ p90 ∧ no test file references it | Adding a test is a clear, scoped PR a maintainer will accept. |
| **Missing docstrings on public API** | function/class in `__all__` or top-level ∧ no docstring | Docs PRs are nearly always accepted. |
| **Dead code** | symbol in graph with in-degree 0 ∧ not an entry point | Removal PRs are quick wins. |
| **AST duplication** | tree-sitter normalized AST hash collision | Refactor PRs land when the dup is small and obvious. |
| **Churn × complexity** | top decile of `commits_touching × cyclomatic_complexity` | Where bugs hide; reviewers welcome refactors. |
| **TODO archaeology** | `git blame` on TODO/FIXME; age > 1 year | Either resolve or remove — both are good PRs. |

LLM only ranks and explains. The detection is deterministic.

### Lane C — Suspicion Scanner

Pre-filtered structurally before any LLM sees it. Candidates:

- Function with high cyclomatic complexity ∧ no error handling on a call to an IO/network function.
- Mutable default arguments.
- Try/except that swallows the exception with no logging.
- Race-condition-shaped patterns (shared mutable + no lock + threading import).

LLM language constraints (enforced in the prompt **and** post-checked by the Verifier):

| Banned | Allowed |
|---|---|
| "bug" | "worth investigating" |
| "broken" | "looks fragile because…" |
| "will crash" | "may behave unexpectedly when…" |
| "obviously wrong" | "the structural pattern is unusual; to confirm:" |

Every Lane C output **must** end with a `confirm_before_pr` step — the user runs this check before opening a PR. No exceptions.

---

## Iteration 2 — Four-layer enforcement, in detail

| Layer | What it actually does | Failure mode it catches |
|---|---|---|
| **1. State design** | `Insight` model has `min_length=1` validators on `so_what` and `goal_link`. `goal_link` must cite something in `intent_profile` (focus_keyword, modality, audience). Pydantic raises before the Insight enters state. | Cartographer emits a bullet with no actionable consequence, or one not tied to the user's stated intent. |
| **2. Prompt contracts** | Every generation prompt opens with a "goal anchor" block that renders `intent_profile.raw_text` + the planner-derived tilts. The three laws (goal-anchored / numbers carry consequences / sections end in motion) follow, with contrastive ❌/✅ examples. ❌: "23 files import this module." ✅: "This module is a hub — 23 files import it, so a signature change ripples broadly. Since you said you're evaluating extensibility, this is a tradeoff worth flagging." | Teacher slips into stat-dump mode under load, or drifts from the stated intent. |
| **3. Verifier 2nd rubric** | After grounding, the Verifier runs a binary actionability rubric: every claim goal-relevant against `intent_profile`? every section ends in action? Fail → objections appended → source node retries ≤ 2. | Teacher emits an on-topic-for-the-repo section that isn't on-topic for the user's stated intent. |
| **4. Eval harness** | Per-PR retrieval/generation runs hit eval datasets. Actionability rate ≥ 80%. Regex denylist test asserts forbidden phrases ("X functions", "Y classes" as standalone) never appear in generated tours. **Plus**: a `test_pre_context_shapes_output` test that runs two materially different `IntentProfile`s on the same repo and asserts the resulting `draft_tour`s differ structurally by ≥ 50%. | Slow drift; a refactor weakens the prompt without anyone noticing until the eval fails CI. Or worse — the system stops actually tilting on intent and falls back to a generic default. |

The point of four layers is that **no single layer is trusted**. The state validator catches the easy cases; the prompt catches the medium cases; the Verifier catches the hard cases; the eval catches the drift. Removing any layer doubles the bug rate.

---

## LangSmith — tracing and evals

| Use | Setup |
|---|---|
| **Tracing** | Every LangGraph node decorated with `@traceable`. Project = `codebase-archaeologist-{phase}`. Run names include `repo_id` and section title for easy filtering. |
| **Eval datasets** | One dataset per quality dimension: `qa_grounding_v1` (Phase 2), `intent_routing_v1` (Phase 3), `actionability_v1` (Phase 3+), `opportunity_quality_v1` (Phase 5). Each entry is `(input, expected_output, evaluator)`. |
| **Per-PR eval** | A workflow that runs the eval suite on touched packages. Numbers go into the PR description. Drops below gate → CI red. |

LangSmith is the only paid-tier surface we use, and it's free for solo dev.

---

## Failure modes and cost design

| Failure | Detection | Mitigation |
|---|---|---|
| **Groq 429 storm** | provider returns 429 | Exponential backoff with jitter → Cerebras fallback → Ollama fallback. SQLite cache catches retries. |
| **Verifier rejects every claim** | objections > 50% of claims in a section | Source node has 2 retries; after that, claims render as `flagged` and ship. We never silently drop. |
| **Infinite verifier ↔ source loop** | recursion_limit=15 | Hard ceiling. If hit, the run errors with a useful message and the partial tour is preserved via checkpoint. |
| **Indexing too slow on big repos** | arq job exceeds 90s for 50kLOC | Phase 1 quality gate. Profiling task to chunk in parallel batches. |
| **LLM hallucinates a file path** | Verifier `read_chunks` fails because the path doesn't exist | Claim is rejected with reason "ungrounded path". Source retries; if persistent, flagged. |
| **Lane C says "this is broken"** | Verifier regex check on output | Hard-coded denylist in the Verifier rubric. Claim rejected. Source must rephrase. |
| **State leaks across runs** | Postgres checkpoint key collision | `(repo_id, run_id)` composite key. Idempotency on `run_id`. |
| **Free-tier quota exhausted mid-tour** | `tokens_used` near per-day cap | Soft warning at 80%; hard halt at 95% with a "come back tomorrow" UX message — never silently degrade. |
