# 03 — Architecture

This is the design document. It is detailed by intent: getting the topology, state schema, and verification loop right is the entire architectural keystone. Phases 0–6 are mostly an exercise in faithfully implementing what is specified here.

---

## Agent topology

```
                                    user submits repo URL
                                              │
                                              ▼
                              ┌──────────────────────────────┐
                              │       Intent Router          │   ◄── PRE-CONTEXT
                              │   (llama-3.1-8b-instant)     │       LAYER 1:
                              │   purpose ∈ {learn,           │       capture WHY
                              │              contribute,      │
                              │              question}        │
                              └──────────┬───────────────────┘
                                         │ conditional edge
            ┌────────────────────────────┼─────────────────────────────┐
            │                            │                             │
            ▼                            ▼                             ▼
   ┌────────────────┐         ┌──────────────────┐         ┌────────────────────┐
   │ LEARN subgraph │         │ CONTRIBUTE       │         │  Q&A subgraph      │
   │                │         │   subgraph       │         │                    │
   │ Learn          │         │ Contribute       │         │ Hybrid retrieval   │
   │ Elicitation    │◄PRE-CTX │ Elicitation      │◄PRE-CTX │  loop (≤3 hops):   │
   │ (focus_hint)   │ LAYER 2 │ (intent)         │ LAYER 2 │ vector_search →    │
   │      │         │         │      │           │         │ graph_traverse →   │
   │      ▼         │         │      ▼           │         │ judge sufficiency  │
   │ Cartographer   │         │  ┌─── A ───┐     │         │  (Q&A 70B primary, │
   │   (70B)        │         │  │ Issue   │     │         │   qwen3-32b        │
   │      │         │         │  │ Triage  │     │         │   fallback)        │
   │      ▼         │         │  │ (70B)   │     │         └─────────┬──────────┘
   │ Flow Tracer    │         │  └────┬────┘     │                   │
   │   (qwen3-32b)  │         │  ┌─── B ───┐     │                   │
   │      │         │         │  │ Code    │     │                   │
   │      ▼         │         │  │ Health  │     │                   │
   │ Teacher        │         │  │ (8B)    │     │                   │
   │   (70B)        │         │  └────┬────┘     │                   │
   │      │         │         │  ┌─── C ───┐     │                   │
   │      │         │         │  │Suspicion│     │                   │
   │      │         │         │  │(qwen3)  │     │                   │
   │      │         │         │  └────┬────┘     │                   │
   │      │         │         │       │          │                   │
   │      │         │         │       ▼          │                   │
   │      │         │         │  Opportunity     │                   │
   │      │         │         │  Ranker (det.)   │                   │
   │      │         │         │       │          │                   │
   │      │         │         │       ▼          │                   │
   │      │         │         │  Teacher         │                   │
   │      │         │         │  briefing (70B)  │                   │
   └──────┬─────────┘         └───────┬──────────┘                   │
          │                           │                                │
          └───────────┬───────────────┼────────────────────────────────┘
                      │               │
                      ▼               ▼
            ┌─────────────────────────────────────────┐
            │              VERIFIER LOOP              │
            │      qwen2.5-coder:7b (local Ollama)    │
            │                                         │
            │  Per-claim grounding check              │
            │   against read_chunks                   │
            │  + Iteration-2 actionability rubric     │
            │                                         │
            │   pass? ─► stream to client             │
            │   fail? ─► append to verifier_objections│
            │              │                          │
            │              ▼                          │
            │     source node retries ≤ 2             │
            │              │                          │
            │   still failing? ─► render as "flagged" │
            │                       (never as fact)   │
            └─────────────────────────────────────────┘
                              │
                              ▼
                  SSE stream to browser
                  (section_start / token / claim /
                   diagram / section_end / done)
```

A few topology notes that the diagram alone doesn't show:

- **Pre-context capture is two-layered and runs before any analysis.** Layer 1 is the Intent Router (purpose). Layer 2 is the per-branch elicitation node (Learn Elicitation or Contribute Elicitation). Together they populate `purpose`, `focus_hint`, and `contribution_intent` in state. **Every generation node downstream reads these and injects them into its prompt** — the pre-context is the goal anchor that the Iteration-2 contract enforces against.
- **Learn Elicitation is a real LangGraph node, not an optional inference step.** It runs unconditionally on the `learn` branch and asks: "Are you here for the overall structure, a specific feature, or the data model?" The user's answer is the `focus_hint` that determines which hubs Cartographer privileges and which flow Flow Tracer picks.
- **The Verifier is not a node downstream of generation. It is a sub-graph that wraps every generating node**, with a conditional retry edge back to the source. This is why it appears as a single block at the bottom even though it fires repeatedly across the tour.
- **Subgraphs share the same `ArchaeologistState`.** Subgraphs are organizational; there is one state object for the whole run.
- **Contribute Lane A/B/C are parallel.** LangGraph runs them concurrently and the Ranker waits on all three. None of them ever blocks on another.
- **The Q&A subgraph is reachable from any tour state**, not only from the initial router. It is the "ask me anything" escape hatch the user always has. Q&A answers are still framed by the captured pre-context — an OSS-contributor user asking "what does this function do?" gets the answer plus a hint about its blast radius; a learner asking the same question gets the answer plus where it sits in the system map.

---

## Agent table

| Agent | Model | Job | Tools | Reads from state | Writes to state |
|---|---|---|---|---|---|
| **Intent Router** | `llama-3.1-8b-instant` | **Pre-context layer 1.** Classify the user's first turn into `learn` / `contribute` / `question`. Always the first node. | (none) | `repo_url`, user message | `purpose` |
| **Learn Elicitation** | `llama-3.1-8b-instant` | **Pre-context layer 2 (Learn branch).** Ask: "Are you here for overall structure, a specific feature, or the data model?" Capture as `focus_hint`. Runs before Cartographer — no analysis happens until this answers. | (none) | `purpose` | `focus_hint` |
| **Cartographer** | `llama-3.3-70b-versatile` | Build the system map: entry points (in-degree 0), hubs (top fan-in), layers (community detection). **Tailors the map to `focus_hint`** (e.g., `data_model` → privileges schema-shaped hubs, dataclass clusters, ORM models; `specific_feature` → narrows to relevant layer; `overall_structure` → balanced). Emit `Insight` objects — never raw metrics. | `graph_query`, `graph_metrics`, `read_chunks` | `repo_id`, `purpose`, `focus_hint` | `system_map[]` |
| **Flow Tracer** | `qwen3-32b` | Pick ONE end-to-end flow that aligns with `focus_hint`. Walk it via graph traversal. Emit Insight objects per step. The Insight's `goal_link` field explicitly cites the captured pre-context. | `graph_traverse`, `read_chunks` | `system_map`, `focus_hint` | `traced_flows[]` |
| **Teacher (Learn)** | `llama-3.3-70b-versatile` | Sequence the system map and traced flow into a narrative. Emit mermaid diagrams. Every section ends with a next action. Lead paragraph references the user's stated focus ("You said you're here for the data model — here is what that looks like in this codebase…"). | `read_chunks` | `system_map`, `traced_flows`, `purpose`, `focus_hint` | `draft_tour[]` |
| **Contribute Elicitation** | `llama-3.1-8b-instant` | **Pre-context layer 2 (Contribute branch).** Ask the 4-way intent question. Capture as `contribution_intent`. Runs before any scanner — no lane starts until this answers. | (none) | `purpose` | `contribution_intent` |
| **Issue Triage (Lane A)** | `llama-3.3-70b-versatile` | Score open issues by **graph-backed approachability** (blast radius, callers, isolation). | `github_issues`, `graph_metrics`, `read_chunks` | `repo_url`, `contribution_intent` | `triaged_issues[]`, contributes to `opportunity_list[]` |
| **Code Health (Lane B)** | `llama-3.1-8b-instant` | Rank deterministic quality signals (hot-untested, missing docstrings on public API, AST dup, dead code, churn × complexity, TODO archaeology) by **mergeability**. | `graph_metrics`, `read_chunks` | `repo_id` | contributes to `opportunity_list[]` |
| **Suspicion (Lane C)** | `qwen3-32b` | Explain pre-filtered structural anomalies with guarded language. Every suspicion includes a `to_confirm:` step. | `graph_metrics`, `read_chunks` | `repo_id` | contributes to `opportunity_list[]` |
| **Opportunity Ranker** | (deterministic, no LLM) | Combine Lane A/B/C outputs into a single ranked `opportunity_list`. | (none) | A, B, C outputs | `opportunity_list[]` |
| **Teacher (Contribute briefing)** | `llama-3.3-70b-versatile` | Take top-N opportunities, brief the user, end each with files to touch + suggested first step. | `read_chunks` | `opportunity_list`, `contribution_intent` | `draft_tour[]` |
| **Q&A** | `llama-3.3-70b-versatile` (qwen3-32b fallback) | Hybrid retrieval loop with sufficiency judge, ≤ 3 hops. | `vector_search`, `graph_traverse`, `read_chunks` | `user_question`, `repo_id` | `draft_tour[]` (appended) |
| **Verifier** | `qwen2.5-coder:7b` (Ollama) | Per-claim grounding check against `read_chunks` PLUS Iteration-2 actionability rubric. | `read_chunks` | `draft_tour[]` (latest section) | `verifier_objections[]`, mutates `claim.status` |

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
    goal_link: str = Field(min_length=1) # how this maps to purpose+focus_hint

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


# ─── Top-level state ────────────────────────────────────────────────────────

Purpose = Literal["learn", "contribute", "question"]
FocusHint = Literal["overall_structure", "specific_feature", "data_model"]
ContributionIntent = Literal["fix_issue", "improve_quality", "hunt_problems", "show_all"]


class ArchaeologistState(BaseModel):
    # — identity —
    repo_id: str
    repo_url: str

    # — pre-context (captured BEFORE any analysis runs) —
    # purpose: set by Intent Router (layer 1).
    # focus_hint: set by Learn Elicitation (layer 2, learn branch).
    # contribution_intent: set by Contribute Elicitation (layer 2, contribute branch).
    # Downstream generation nodes MUST raise if their required pre-context field is None.
    purpose: Purpose | None = None
    focus_hint: FocusHint | None = None
    contribution_intent: ContributionIntent | None = None
    user_question: str | None = None

    # — Learn artifacts —
    system_map: Annotated[list[Insight], add] = Field(default_factory=list)
    traced_flows: Annotated[list[Insight], add] = Field(default_factory=list)

    # — Contribute artifacts —
    triaged_issues: Annotated[list[Opportunity], add] = Field(default_factory=list)
    opportunity_list: Annotated[list[Opportunity], add] = Field(default_factory=list)

    # — Output —
    draft_tour: Annotated[list[TourSection], add] = Field(default_factory=list)

    # — Verifier loop —
    verifier_objections: Annotated[list[VerifierObjection], add] = Field(default_factory=list)
    retry_count: dict[int, int] = Field(default_factory=dict)  # section_order -> retries

    # — Observability —
    tokens_used: dict[str, int] = Field(default_factory=dict)  # model_name -> tokens
    errors: Annotated[list[str], add] = Field(default_factory=list)
```

**State rules (enforced in code review, not in comments):**

1. **No agent writes another agent's field.** Use Python's typed return values. The reducer composes the diff.
2. **Mutations only via node returns.** Never `state.foo.append(...)`. Always `return {"foo": [new_item]}`.
3. **Reducer on append-only collections.** Verifier objections, errors, system_map, traced_flows, opportunity_list, draft_tour all use `Annotated[..., add]`.
4. **`recursion_limit=15`.** Anything beyond is a loop bug. Found cheaper here than in production.
5. **Validators do real work.** `Insight.so_what` empty → validation error → the bug is at the source node, not in the Teacher.
6. **Pre-context is required before analysis.** No node downstream of an elicitation may run with its required pre-context field unset: Cartographer / Flow Tracer / Teacher (Learn) require `focus_hint`; Lane A/B/C / Ranker / Teacher (Contribute) require `contribution_intent`. Enforced by a guard at the top of each such node that raises if the field is `None`. The graph topology blocks the elicitation edge until the user answers, so this guard catches programmer error, not normal flow.

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

## How pre-context flows through the system

| Step | What gets captured / used |
|---|---|
| **User opens app** | (nothing yet — no analysis runs) |
| **Intent Router fires** | Captures `purpose` ∈ `{learn, contribute, question}` from the first message. |
| **Per-branch Elicitation fires** | Learn → `focus_hint`. Contribute → `contribution_intent`. The graph **blocks** here until the user answers; no scanner, Cartographer, or Q&A runs without pre-context. |
| **Downstream prompts read pre-context** | Every generation prompt template injects `purpose`, `focus_hint`, and `contribution_intent` as the leading "goal anchor" block. The Iteration-2 Verifier rubric uses these same fields to check goal relevance — a section that doesn't tie back to the captured pre-context fails the rubric. |
| **Contribute lane gating** | `contribution_intent` controls which lanes are active and how they're weighted in the Ranker: `fix_issue` → Lane A weighted heaviest; `improve_quality` → Lane B; `hunt_problems` → Lane C; `show_all` → all three balanced. |
| **Q&A escape hatch** | When the user asks a question mid-tour, Q&A still reads `purpose` and `focus_hint` and frames the answer accordingly. |
| **User changes their mind** | "Restart with a different purpose" re-runs from the Intent Router with the existing indexed repo. Indexing is not redone. |

The traceability property: for every paragraph the user sees, they can point at the pre-context fields that produced it. This is what "meet the purpose" looks like in practice.

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
| **1. State design** | `Insight` model has `min_length=1` validators on `so_what` and `goal_link`. Pydantic raises before the Insight enters state. | Cartographer emits a bullet with no actionable consequence. |
| **2. Prompt contracts** | Every generation prompt restates the three laws and includes contrastive ❌/✅ examples. ❌: "23 files import this module." ✅: "This module is a hub — 23 files import it, so a signature change ripples broadly. If you're adding a feature, prefer extending vs. modifying." | Teacher slips into stat-dump mode under load. |
| **3. Verifier 2nd rubric** | After grounding, the Verifier runs a binary actionability rubric: every claim goal-relevant? every section ends in action? Fail → objections appended → source node retries ≤ 2. | Teacher emits an on-topic section that doesn't end with a next step. |
| **4. Eval harness** | Per-PR retrieval/generation runs hit eval datasets. Actionability rate ≥ 80%. Regex denylist test asserts forbidden phrases ("X functions", "Y classes" as standalone) never appear in generated tours. | Slow drift; a refactor weakens the prompt without anyone noticing until the eval fails CI. |

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
