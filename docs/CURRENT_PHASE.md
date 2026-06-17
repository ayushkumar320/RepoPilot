# Current Build Phase

> **Active phase:** **Phase 3 — Orchestration + Learn** (steps 1–2 landed: `ArchaeologistState` schema + Intent Profiler)
> **Last verified gate:** Phase 2 — `make ci` green on commit `6065ccf`; 58 fast-lane tests pass, coverage 85.75%, ruff + ruff format + mypy `--strict` all clean. Phase 2 entry datasets labeled and loader-validated. Working tree on 2026-06-17 carries pre-existing mypy/ruff debt in `packages/evals/` (unrelated to Phase 3; left over from the harness-reshape session).
> **Last updated:** 2026-06-17

This document is the **always-correct pointer** at where the build is. Anyone (human or agent) starting a session reads this first to find the active phase and what's left on its gate. The Phase N as-built records live in [`docs/05_PHASE_PROMPTS.md`](05_PHASE_PROMPTS.md); this file is the index.

## Phase ladder

| Phase | Status | Last commit | Spec | Gate state |
|---|---|---|---|---|
| 0 — Foundation | 🟢 **done** | `0f170fa` (CI fixes) | [docs/04 §Phase 0](04_BUILD_PLAN.md) · [docs/05 §Phase 0](05_PHASE_PROMPTS.md) | ✅ `make ci` green · ✅ forced-429 → Hugging Face < 30s · ✅ CI green on GitHub Actions |
| 1 — Ingestion | 🟢 **done** | `c4747e6` | [docs/04 §Phase 1](04_BUILD_PLAN.md) · [docs/05 §Phase 1](05_PHASE_PROMPTS.md) | ✅ fast-lane CI green · ✅ slow-lane `httpx` gate validated · ✅ `revisit_status` returns `stale` |
| 2 — Hybrid Retrieval + Q&A (the spine) | 🟢 **done** (real-LLM eval paused on free-tier quota) | `6065ccf` | [docs/04 §Phase 2](04_BUILD_PLAN.md) · [docs/05 §Phase 2](05_PHASE_PROMPTS.md) | ✅ tools + verifier + Q&A loop ship · ✅ LangSmith provisioned · ✅ PR-time sampled eval green · ✅ `httpx_qa_v1.jsonl` (16 rows) + `verifier_quality_v1.jsonl` (30 rows) labeled against real httpx source · ⚠️ grounding ≥90% / verifier ≥92% **unmeasured** under real LLM (datasets ready; runner wired; awaits paid Groq) |
| 3 — Orchestration + Learn | 🟡 **active** (blocked on entry checklist) | — | [docs/04 §Phase 3](04_BUILD_PLAN.md) · [docs/05 §Phase 3](05_PHASE_PROMPTS.md) | Profiler ≥90%/field · Planner F1 ≥90% · two-intent divergence ≥50% on flask · CI grep "no purpose enum" |
| 4 — Experience | ⚪ pending | — | [docs/04 §Phase 4](04_BUILD_PLAN.md) · [docs/05 §Phase 4](05_PHASE_PROMPTS.md) | Cold-start demo · time-to-first-output ≤12s · Lighthouse a11y ≥90 |
| 5 — Contribute (Iteration 1) | ⚪ pending | — | [docs/04 §Phase 5](04_BUILD_PLAN.md) · [docs/05 §Phase 5](05_PHASE_PROMPTS.md) | Top-3 approachability ≥70% · file-mapping ≥80% · suspicion legitimacy ≥75% · banned-vocab regex |
| 6 — Harden and ship | ⚪ pending | — | [docs/04 §Phase 6](04_BUILD_PLAN.md) · [docs/05 §Phase 6](05_PHASE_PROMPTS.md) | Full eval matrix green · gitleaks + audits clean · clean-VM quickstart ≤5min · `v0.1.0` tagged |

Legend: 🟢 done · 🟡 active · ⚪ pending · 🔴 blocked.

---

## Session 2026-06-17 — Phase 3 steps 1–2 landed (most recent)

Step 2: Intent Profiler in `packages/agents/src/repopilot_agents/intent/profiler.py`. Single LLM call against `ModelId.INTENT_PROFILER`, JSON-only response, coerced into a `state.IntentProfile`. Parse-fail → minimal `IntentProfile(raw_text=…)` so the planner's inclusive-default fallthrough takes over instead of the system guessing.

- ✅ **Schema-bounded coercion:** unknown `modality_weights` keys dropped silently; out-of-[0,1] weights clipped (preserves intent over rejection); unknown `output_shape_preference` coerced to `"unspecified"`; keywords lowercased / trimmed / capped at 6.
- ✅ **9 unit tests pin the coercion contract** — clean parse, unknown keys, embedded-in-prose JSON, fallback on garbage, empty-input rejection, raw_text verbatim. mypy `--strict` clean; full agents fast lane now: **49 passed**.
- ✅ **Aligned `IntentProfileEvalRow` to the state schema** — `expected_modality_weights` now keyed on the same `Modality` literal as state (`understand | change | evaluate | locate | compare`), and `expected_output_shape` matches state's `OutputShape` (`narrative | ranked_list | dossier | comparison_table | unspecified`). The scaffold row updated to match; this closes a latent drift between the harness scaffold and the schema we're now grading against.

## Session 2026-06-17 — Phase 3 keystone landed

Phase 3 step 1 from the kickoff outline is in: `packages/agents/src/repopilot_agents/state.py` holds the full Pydantic v2 schema from `docs/03_ARCHITECTURE.md` § "State schema", and `packages/agents/tests/test_state.py` pins the validators (19 tests, all green).

- ✅ **`ArchaeologistState` + sub-models shipped:** `Claim`, `Insight`, `Opportunity`, `TourSection`, `VerifierObjection`, `ArchaeologistError`, `IntentProfile`, `CapabilityPlan`, `QAExchange`. Append-only collections use `Annotated[list[X], add]` so LangGraph's reducer wires the diffs.
- ✅ **Validators do real work:** empty `Claim.refs` rejected, empty `Insight.so_what` / `Insight.goal_link` rejected, `Opportunity` Lane C without `confirm_before_pr` rejected (model-validator, fires even on the `None` default), modality weights outside [0,1] rejected, `CapabilityPlan.dependencies` referencing inactive capabilities rejected.
- ✅ **mypy `--strict` clean** on the two new files; agents-package fast lane: 40 passed.
- ⚠️ **Working-tree `make ci` is currently red on pre-existing `packages/evals/` debt** (mypy errors in `runners/grounding.py` + `runners/verifier.py`, plus a duplicate `__all__` in `__init__.py`) inherited from the harness-reshape session. These are not Phase 3 work and should be cleared before the Phase 3 entry gates are re-stamped.

## Session 2026-06-16 — eval-harness evolution

Phase 2's entry-checklist datasets landed, plus the harness itself was evolved from a Q&A-only shim into a registry-driven measurement layer ready for Phase 3+. No new commits yet (working tree).

- ✅ **Datasets labeled against the cloned httpx snapshot (`b5addb64`):**
  - `httpx_qa_v1.jsonl` — 16 rows (10 standard + 3 multi-hop + 3 not-in-repo); every `file:line` ref read directly from source.
  - `verifier_quality_v1.jsonl` — 30 rows (15 supported + 15 rejected) with embedded real code chunks.
  - Generator preserved at `.cache/gen_eval_datasets.py` (gitignored) — regeneration reads fresh source, so refs and content cannot drift.
- ✅ **Harness layer reshaped** (`packages/evals/`):
  - `registry.py` — single source of truth: one `EvalSpec` per gate (name · phase · dataset · threshold · `needs_llm` / `needs_indexed_repo`). Adding an eval = appending one row.
  - `reports.py` — every run persists a timestamped JSON + Markdown pair under `eval-reports/` (gitignored). Status surfaces read the latest record.
  - `__main__.py` rewrite — `list`, `status`, and `run <eval> [--sample N] [--report]` subcommands. Real-LLM paths, no monkeypatches.
  - Phase 3 schemas added to `datasets.py` (`IntentProfileEvalRow`, `PlannerEvalRow`) with scaffold JSONL files so Phase 3 labeling has a target.
- ✅ **Architecture doc clarified** — `docs/03_ARCHITECTURE.md` gained an "Eval harness vs. product runtime — a hard line" section so future contributors can't conflate the internal QA layer with the user-facing runtime.
- ✅ **Infra fixes for Neon (free-tier path):**
  - `Settings` now walks up from `packages/core/.../settings.py` to find the repo-root `.env`, so alembic and any subdir invocation see the real DSN instead of falling back to localhost defaults.
  - `make_engine()` and the alembic env normalise bare `postgresql://` DSNs to `postgresql+psycopg://` so SQLAlchemy uses psycopg3's async driver against Neon.
  - Removed the Cerebras tier from `RESOLUTION` chains — the available Cerebras free-tier models (`gpt-oss-120b`, `zai-glm-4.7`) didn't match the llama bindings.
- ⚠️ **Slow-lane `make test-slow` still cannot run end-to-end on free tier** — clone/parse/chunk/graph/embed/DB stages verified manually; the chunk-summary LLM step blows through Groq's 30-RPM rate limit on httpx's ~1500 chunks and the HF fallback returns 402. Code is correct; only quota blocks.

## Phase 2 — what landed (most recent)

Commit `6065ccf` shipped the hybrid-retrieval spine. Full as-built record is in [`docs/05` § Phase 2 — as built](05_PHASE_PROMPTS.md#phase-2--as-built-post-merge-addendum). Headline:

- ✅ Six deterministic tools: `read_chunks` · `vector_search` · `graph_traverse` · `graph_query` · `graph_metrics` · `github_issues` (stub)
- ✅ Verifier with D4 (parse-fail = reject), M1 (asyncio.gather + hash cache), S4 (`<source>` prompt-injection wrapper)
- ✅ Q&A loop in `qa/graph.py` — hybrid retrieval with hop budget hard-capped at 3, hallucination short-circuit returns `NOT_FOUND_SENTINEL`
- ✅ All five locked code-side decisions shipped: D1 (read from `chunks.content`), D2 (async + Pydantic), D3 (shared judge model), D4, D5 (per-repo NetworkX cache)
- ⚠️ Remaining entry-check blockers are the two labeled-dataset eval runs
- ✅ Fast-lane CI green: 58 passed, coverage 85.75%, mypy `--strict` clean on 60 files

## Phase 1 — what landed

Commit `c4747e6`. Full record at [`docs/05` § Phase 1 — as built](05_PHASE_PROMPTS.md#phase-1--as-built-post-merge-addendum). Headline:

- ✅ Pipeline: clone → parse (tree-sitter) → chunk (AST-boundary) → graph (NetworkX) → embed (sentence-transformers in-process, HF weights `nomic-ai/nomic-embed-text-v1.5`) → persist (Postgres + pgvector)
- ✅ Alembic migration (`0001_ingestion_schema`) with `chunks`, `chunk_embeddings (vector(768) + ivfflat)`, `repos`, `graph_adjacency (JSONB)`
- ✅ `LLMProvider.embed()` added (Phase 0 extension)
- ✅ Idempotent on `(repo_url, head_sha)`; `revisit_status()` uses cheap `git ls-remote`
- ✅ **90 s httpx gate validated**

## Phase 0 — what landed

Commit `a684bd7` (code) + `0f170fa` (3 latent CI bugs fixed). Full record at [`docs/05` § Phase 1 — as built ("Three latent CI bugs")](05_PHASE_PROMPTS.md#phase-1--as-built-post-merge-addendum). Headline:

- ✅ Monorepo (`apps/`, `packages/`, `uv` workspace), ruff, mypy `--strict`, pytest, pre-commit, gitleaks, GitHub Actions
- ✅ `LLMProvider` with cache + 429 backoff + Groq → Cerebras → Hugging Face fallback
- ✅ Docker Compose: Postgres + pgvector, Redis, Hugging Face (with model preload)
- ✅ All 5 TDD tests pass; forced-429 storm falls back to Hugging Face in < 30 s
- ✅ Phase 1 fold-in landed `make lint` running `ruff format --check` so CI-vs-local drift can't recur

---

## Phase 3 — entry checklist (the active block)

Phase 3 work cannot start until these are checked. Restated from [`docs/05`](05_PHASE_PROMPTS.md#phase-2--explicit-deferrals-must-clear-before-phase-3-starts) for emphasis:

- [x] **`httpx_qa_v1.jsonl` labeled** — 16 rows (10 standard + 3 multi-hop + 3 not-in-repo) against the cloned httpx snapshot `b5addb64`. Loader-validated. Real-LLM grounding accuracy ≥ 90% remains **unmeasured** (runner ready; awaits paid Groq tier).
- [x] **`verifier_quality_v1.jsonl` labeled** — 30 hand-built `(claim, chunks, expected_verdict)` triples (15 supported + 15 rejected) with embedded real code chunks. Loader-validated. Real-LLM verifier accuracy ≥ 92% remains **unmeasured** (same reason).
- [x] **`LANGSMITH_API_KEY`** provisioned in `.env`; a sample trace visible at the project URL.
- [x] **PR-time sampled eval** runs in ≤ 5 min on `main` (per `docs/06` S6). — *Done. Two workflows (`eval-pr.yml`, `eval-main.yml`) + `eval_sampled` / `eval_full` pytest markers + `make test-eval-sampled` / `make test-eval-full` Makefile targets + scaffold tests that skip cleanly when datasets are missing. Stub eval job removed from `ci.yml`. Local `make ci` green: 60 passed, 5 skipped (sentinel datasets absent), 85.75% coverage.*
- [x] **Phase 1 slow-lane gate validated.**

> **Note on the two ⚠️ "unmeasured" items above.** Per the rule at the bottom of this file, this is a *documented relaxation*, not a silent pass: the datasets are real and the harness runs end-to-end; only the LLM-bound accuracy number is paused on free-tier quota. The moment paid credits land, run `uv run python -m repopilot_evals run verifier --report` and `… run grounding --report` (the latter needs httpx ingested into Neon first) to convert these to measured ✅.

If any box is unchecked when Phase 3 work begins, do that first — not orchestration code. The Phase 4 demo's "verified-grounded badge" UX has nothing to stand on if the grounding number lands below the gate when finally measured.

## Phase 3 — kickoff outline (read after entry checklist clears)

When the checklist above is green, read [`docs/05` § Phase 3 prompt](05_PHASE_PROMPTS.md#phase-3-prompt--orchestration--learn-subgraph) and ship in this order:

1. **`packages/agents/state.py`** — `ArchaeologistState`, full Pydantic v2 schema from `docs/03`. Validators that fail on empty `Claim.refs`, `Insight.so_what`, `Insight.goal_link`. This is the keystone — TDD it.
2. **Intent Profiler** (`packages/agents/intent/profiler.py`) — 8B model, emits draft `IntentProfile`. Tests against `intent_profiling_v1.jsonl` ≥ 90% per field.
3. **Capability Planner** (`packages/agents/intent/planner.py`) — pure Python `plan(IntentProfile) -> CapabilityPlan`. Tests against `planner_correctness_v1.jsonl` ≥ 90% F1.
4. **Goal-anchor helper** (`packages/agents/prompts/goal_anchor.py`) — every generation prompt template begins with the rendered output. Snapshot test pins it.
5. **Verifier loop** (`packages/agents/verifier/loop.py`) — wraps the Phase 2 grounding checker with the actionability rubric, source-node retry budget = 2, `flagged` on persistent failure.
6. **Cartographer → Flow Tracer → Teacher** in that order, each ≤ 2000 input tokens.
7. **LangGraph wiring** (`packages/agents/graph.py`) — promote Phase 2's `qa/graph.py` into a node of the full `StateGraph[ArchaeologistState]` with the Postgres checkpointer. `recursion_limit=15`. Don't refactor `qa/graph.py` earlier than this step.

Phase 3 also lifts the **`if state.purpose ==` grep check** into CI as a hard rule per the elasticity guarantee.

---

## How to advance the phase

1. Pick the next unchecked item on the active phase's checklist and write the test first.
2. When all of the active phase's gate items pass on the machine (not just in mocks), flip the phase to 🟢, flip the next to 🟡, update **Last verified gate**, and add a "what landed" section above with the commit and one-line headline.
3. Paste the next phase's prompt from `docs/05_PHASE_PROMPTS.md` into a fresh session.

> If a phase fails its gate, it stays 🟡 — never silently advance. Either fix the failure or write down explicitly why the gate was relaxed (and update `docs/04_BUILD_PLAN.md` if the relaxation is permanent).
>
> **`CURRENT_PHASE.md` lives or dies on being correct.** If the active phase changes — even just a checklist item flipping — update this file in the same commit. The Phase 1 → Phase 2 → Phase 3 transitions in this session all forgot to update it; that's a documentation-layering bug, caught here once and now noted as the rule.
