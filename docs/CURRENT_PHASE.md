# Current Build Phase

> **Active phase:** **Phase 3 — Orchestration + Learn** (not started; blocked on the Phase 3 entry checklist below)
> **Last verified gate:** Phase 2 — `make ci` green on commit `6065ccf`; 58 fast-lane tests pass, coverage 85.75%, ruff + ruff format + mypy `--strict` all clean.
> **Last updated:** 2026-06-15

This document is the **always-correct pointer** at where the build is. Anyone (human or agent) starting a session reads this first to find the active phase and what's left on its gate. The Phase N as-built records live in [`docs/05_PHASE_PROMPTS.md`](05_PHASE_PROMPTS.md); this file is the index.

## Phase ladder

| Phase | Status | Last commit | Spec | Gate state |
|---|---|---|---|---|
| 0 — Foundation | 🟢 **done** | `0f170fa` (CI fixes) | [docs/04 §Phase 0](04_BUILD_PLAN.md) · [docs/05 §Phase 0](05_PHASE_PROMPTS.md) | ✅ `make ci` green · ✅ forced-429 → Ollama < 30s · ✅ CI green on GitHub Actions |
| 1 — Ingestion | 🟢 **done** (slow-lane gate ⚠️ unrun) | `c4747e6` | [docs/04 §Phase 1](04_BUILD_PLAN.md) · [docs/05 §Phase 1](05_PHASE_PROMPTS.md) | ✅ fast-lane CI green · ⚠️ **90 s httpx gate never run** (needs Docker + Ollama + Groq locally) · ✅ `revisit_status` returns `stale` |
| 2 — Hybrid Retrieval + Q&A (the spine) | 🟢 **done** (eval gates deferred) | `6065ccf` | [docs/04 §Phase 2](04_BUILD_PLAN.md) · [docs/05 §Phase 2](05_PHASE_PROMPTS.md) | ✅ tools + verifier + Q&A loop ship; 58 tests pass · ⚠️ grounding ≥90% / multi-hop / hallucination gates **unmeasured** — eval datasets deferred · ⚠️ LangSmith deferred |
| 3 — Orchestration + Learn | 🟡 **active** (blocked on entry checklist) | — | [docs/04 §Phase 3](04_BUILD_PLAN.md) · [docs/05 §Phase 3](05_PHASE_PROMPTS.md) | Profiler ≥90%/field · Planner F1 ≥90% · two-intent divergence ≥50% on flask · CI grep "no purpose enum" |
| 4 — Experience | ⚪ pending | — | [docs/04 §Phase 4](04_BUILD_PLAN.md) · [docs/05 §Phase 4](05_PHASE_PROMPTS.md) | Cold-start demo · time-to-first-output ≤12s · Lighthouse a11y ≥90 |
| 5 — Contribute (Iteration 1) | ⚪ pending | — | [docs/04 §Phase 5](04_BUILD_PLAN.md) · [docs/05 §Phase 5](05_PHASE_PROMPTS.md) | Top-3 approachability ≥70% · file-mapping ≥80% · suspicion legitimacy ≥75% · banned-vocab regex |
| 6 — Harden and ship | ⚪ pending | — | [docs/04 §Phase 6](04_BUILD_PLAN.md) · [docs/05 §Phase 6](05_PHASE_PROMPTS.md) | Full eval matrix green · gitleaks + audits clean · clean-VM quickstart ≤5min · `v0.1.0` tagged |

Legend: 🟢 done · 🟡 active · ⚪ pending · 🔴 blocked.

---

## Phase 2 — what landed (most recent)

Commit `6065ccf` shipped the hybrid-retrieval spine. Full as-built record is in [`docs/05` § Phase 2 — as built](05_PHASE_PROMPTS.md#phase-2--as-built-post-merge-addendum). Headline:

- ✅ Six deterministic tools: `read_chunks` · `vector_search` · `graph_traverse` · `graph_query` · `graph_metrics` · `github_issues` (stub)
- ✅ Verifier with D4 (parse-fail = reject), M1 (asyncio.gather + hash cache), S4 (`<source>` prompt-injection wrapper)
- ✅ Q&A loop in `qa/graph.py` — hybrid retrieval with hop budget hard-capped at 3, hallucination short-circuit returns `NOT_FOUND_SENTINEL`
- ✅ All five locked code-side decisions shipped: D1 (read from `chunks.content`), D2 (async + Pydantic), D3 (shared judge model), D4, D5 (per-repo NetworkX cache)
- ⚠️ D6 (LangSmith) + D7 (eval labeling) **deferred** to the Phase 3 entry checklist
- ✅ Fast-lane CI green: 58 passed, coverage 85.75%, mypy `--strict` clean on 60 files

## Phase 1 — what landed

Commit `c4747e6`. Full record at [`docs/05` § Phase 1 — as built](05_PHASE_PROMPTS.md#phase-1--as-built-post-merge-addendum). Headline:

- ✅ Pipeline: clone → parse (tree-sitter) → chunk (AST-boundary) → graph (NetworkX) → embed (Ollama nomic-embed-text) → persist (Postgres + pgvector)
- ✅ Alembic migration (`0001_ingestion_schema`) with `chunks`, `chunk_embeddings (vector(768) + ivfflat)`, `repos`, `graph_adjacency (JSONB)`
- ✅ `LLMProvider.embed()` added (Phase 0 extension)
- ✅ Idempotent on `(repo_url, head_sha)`; `revisit_status()` uses cheap `git ls-remote`
- ⚠️ **90 s httpx gate never run** — needs `make docker-up && make db-migrate && make test-slow` on a host with Docker + Ollama + a Groq key

## Phase 0 — what landed

Commit `a684bd7` (code) + `0f170fa` (3 latent CI bugs fixed). Full record at [`docs/05` § Phase 1 — as built ("Three latent CI bugs")](05_PHASE_PROMPTS.md#phase-1--as-built-post-merge-addendum). Headline:

- ✅ Monorepo (`apps/`, `packages/`, `uv` workspace), ruff, mypy `--strict`, pytest, pre-commit, gitleaks, GitHub Actions
- ✅ `LLMProvider` with cache + 429 backoff + Groq → Cerebras → Ollama fallback
- ✅ Docker Compose: Postgres + pgvector, Redis, Ollama (with model preload)
- ✅ All 5 TDD tests pass; forced-429 storm falls back to Ollama in < 30 s
- ✅ Phase 1 fold-in landed `make lint` running `ruff format --check` so CI-vs-local drift can't recur

---

## Phase 3 — entry checklist (the active block)

Phase 3 work cannot start until these are checked. Restated from [`docs/05`](05_PHASE_PROMPTS.md#phase-2--explicit-deferrals-must-clear-before-phase-3-starts) for emphasis:

- [ ] **Phase 1 slow-lane gate validated.** Run `make docker-up && make db-migrate && make test-slow`. The 90 s `httpx` index gate is the floor that every downstream phase assumes.
- [ ] **`httpx_qa_v1.jsonl`** has 15 labeled Q&A rows (10 standard + 3 multi-hop + 3 not-in-repo). Without it the Phase 2 grounding gate (≥ 90%) is **unmeasured**, not unmet.
- [ ] **`verifier_quality_v1.jsonl`** has 30 hand-labeled `(claim, chunks, expected_verdict)` triples; verifier accuracy ≥ 92% measured. Per `docs/06` S5 — without this the grounding number is a function of two unknown error rates.
- [ ] **`LANGSMITH_API_KEY`** provisioned in `.env`; a sample trace visible at the project URL. Needed for Phase 3's checkpoint-resume eval matrix anyway.
- [ ] **PR-time sampled eval** runs in ≤ 5 min on `main` (per `docs/06` S6).

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
