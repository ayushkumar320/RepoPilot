# Current Build Phase

> **Active phase:** **Phase 4 — Experience** (FastAPI + Next.js + synchronized code viewer; the gate is a working demo on flask reached via locally-run API + web app talking to Neon Postgres + Upstash/local Redis via connection strings — **Docker is deferred to Phase 6**, see the note below the ladder).
> **Last verified gate:** Phase 3 — agents fast lane **104 passed**, `ruff` + `ruff format` + `mypy --strict` all clean across 42 source files; CI grep "no purpose enum" enforced. Real-LLM accuracy gates (Profiler ≥90%/field, Planner F1 ≥90%, two-intent divergence ≥50% on flask, actionability ≥80%) carry the same documented relaxation Phase 2's grounding/verifier numbers did — code is unblocked, only labeled datasets + paid Groq run between us and a measured ✅.
> **Last updated:** 2026-06-17

This document is the **always-correct pointer** at where the build is. Anyone (human or agent) starting a session reads this first to find the active phase and what's left on its gate. The Phase N as-built records live in [`docs/05_PHASE_PROMPTS.md`](05_PHASE_PROMPTS.md); this file is the index.

## Phase ladder

| Phase | Status | Last commit | Spec | Gate state |
|---|---|---|---|---|
| 0 — Foundation | 🟢 **done** | `0f170fa` (CI fixes) | [docs/04 §Phase 0](04_BUILD_PLAN.md) · [docs/05 §Phase 0](05_PHASE_PROMPTS.md) | ✅ `make ci` green · ✅ forced-429 → Hugging Face < 30s · ✅ CI green on GitHub Actions |
| 1 — Ingestion | 🟢 **done** | `c4747e6` | [docs/04 §Phase 1](04_BUILD_PLAN.md) · [docs/05 §Phase 1](05_PHASE_PROMPTS.md) | ✅ fast-lane CI green · ✅ slow-lane `httpx` gate validated · ✅ `revisit_status` returns `stale` |
| 2 — Hybrid Retrieval + Q&A (the spine) | 🟢 **done** (real-LLM eval paused on free-tier quota) | `6065ccf` | [docs/04 §Phase 2](04_BUILD_PLAN.md) · [docs/05 §Phase 2](05_PHASE_PROMPTS.md) | ✅ tools + verifier + Q&A loop ship · ✅ LangSmith provisioned · ✅ PR-time sampled eval green · ✅ `httpx_qa_v1.jsonl` (16 rows) + `verifier_quality_v1.jsonl` (30 rows) labeled against real httpx source · ⚠️ grounding ≥90% / verifier ≥92% **unmeasured** under real LLM (datasets ready; runner wired; awaits paid Groq) |
| 3 — Orchestration + Learn | 🟢 **done** (real-LLM accuracy gates paused on free-tier quota — same relaxation as Phase 2) | — *(working tree on `65a0a80`; commit pending)* | [docs/04 §Phase 3](04_BUILD_PLAN.md) · [docs/05 §Phase 3](05_PHASE_PROMPTS.md) | ✅ ArchaeologistState schema · ✅ Intent Profiler · ✅ Capability Planner · ✅ goal-anchor helper · ✅ verifier loop (actionability + retry → flagged) · ✅ Cartographer / Flow Tracer / Teacher · ✅ full StateGraph with `recursion_limit=15` · ✅ CI grep "no purpose enum" · ⚠️ Profiler ≥90%/field, Planner F1 ≥90%, two-intent divergence ≥50% on flask, actionability ≥80% **unmeasured** under real LLM (harness wired; datasets need labeling and paid Groq) |
| 4 — Experience | 🟡 **active** (entry from a clean slate — no code yet) | — | [docs/04 §Phase 4](04_BUILD_PLAN.md) · [docs/05 §Phase 4](05_PHASE_PROMPTS.md) | Demo on flask reachable from a locally-run API + web app (Postgres/Redis via connection strings — Docker deferred to Phase 6) · time-to-first-useful-output ≤ 12s (Playwright) · click-to-highlight on 10 random claims · verified-badge on ≥ 90% of demo-tour claims · retrieval-path chip on every claim/Q&A · Q&A drives the code viewer · Lighthouse a11y ≥ 90 · SSE survives 5 min idle |
| 5 — Contribute (Iteration 1) | ⚪ pending | — | [docs/04 §Phase 5](04_BUILD_PLAN.md) · [docs/05 §Phase 5](05_PHASE_PROMPTS.md) | Top-3 approachability ≥70% · file-mapping ≥80% · suspicion legitimacy ≥75% · banned-vocab regex |
| 6 — Harden and ship | ⚪ pending | — | [docs/04 §Phase 6](04_BUILD_PLAN.md) · [docs/05 §Phase 6](05_PHASE_PROMPTS.md) | Full eval matrix green · gitleaks + audits clean · clean-VM quickstart ≤5min · `v0.1.0` tagged |

Legend: 🟢 done · 🟡 active · ⚪ pending · 🔴 blocked.

---

## Session 2026-06-17 — Phase 3 steps 3–7 + CI grep landed (most recent)

The remaining Phase 3 kickoff outline now ships. Same session as steps 1–2 below; everything sits unstaged on top of `65a0a80`.

- ✅ **Step 3 — Capability Planner** at `packages/agents/src/repopilot_agents/intent/planner.py`. Pure Python `plan(IntentProfile) → CapabilityPlan` per docs/03 § "The Capability Planner". Rules read continuous `modality_weights` + `raw_text` signals; inclusive default fires on the minimal profile so the planner never returns empty. 11 unit tests pin divergent profiles → divergent plans, dependency-DAG correctness, and shape inference.
- ✅ **Step 4 — Goal-anchor helper** at `packages/agents/src/repopilot_agents/prompts/goal_anchor.py`. Single source of truth for the prompt header every generation node prepends — renders `intent_profile.raw_text` + planner-derived tilts + the Three Laws contract. **Snapshot test pins the exact rendered string** so any drift fails CI loudly. 8 tests.
- ✅ **Step 5 — Verifier loop** at `packages/agents/src/repopilot_agents/verifier/loop.py`. Wraps Phase 2 grounding with the Iteration-2 actionability rubric (binary, goal-relevance against `intent_profile`). `verify_section_with_retries` retries the source node up to `MAX_SOURCE_RETRIES=2`; persistent failures are **flagged**, never silently dropped. 14 tests cover JSON parsing, section aggregation, retry recovery, and the flagged-not-dropped rule.
- ✅ **Step 6 — Capability nodes** at `packages/agents/src/repopilot_agents/capabilities/`. Cartographer, Flow Tracer, Teacher. Each reads the deterministic tools, renders the goal anchor, asks for STRICT JSON, coerces into typed state objects. Iteration-2 contract enforced by the Pydantic validators in state.py (empty `so_what` → drop). 15 tests.
- ✅ **Step 7 — LangGraph wiring** at `packages/agents/src/repopilot_agents/graph.py`. Full `StateGraph[ArchaeologistState]` with conditional edges on `capability_plan.active`. `RECURSION_LIMIT=15`. Q&A re-exported alongside (universal side channel — not wired into the main graph per docs/03). MemorySaver checkpointer plumbed for tests; AsyncPostgresSaver swap is a Phase 6 hardening pass. 6 wiring tests cover cold-start, confirmed-profile, conditional skip, and checkpointer plumbing.
- ✅ **Step 8 — CI grep for "no purpose enum"** at `packages/agents/tests/test_no_purpose_enum.py`. Hard test fails when any source file matches `state.purpose`, `purpose_enum`, or `Purpose = Literal[`. Lifts the elasticity guarantee into CI per docs/03 § "State rules" #7.
- ✅ **Agents fast lane: 104 passed, ruff + ruff format + mypy `--strict` all clean** across the 42 source files in `packages/agents/`. Total source-line coverage in the agents package crossed 65%.

**Gate status.** The remaining 🟡 items are the **LLM-bound accuracy gates** (profiler ≥90%/field, planner F1 ≥90%, two-intent divergence ≥50% on flask, actionability ≥80%). All the harness scaffolding is in place; the labeled datasets need to be backfilled and a real-LLM run executed against paid Groq. Code is unblocked — datasets + paid quota are the only remaining blockers, same as the Phase 2 grounding/verifier numbers.

## Session 2026-06-17 — Phase 3 steps 1–2 landed

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

## Phase 3 — what landed

Phase 3's seven kickoff-outline steps + the elasticity CI grep shipped in one session (records above under "Session 2026-06-17"). Headline:

- ✅ `packages/agents/src/repopilot_agents/state.py` — full Pydantic v2 `ArchaeologistState` schema with append-only reducers and `Insight` / `Claim` / `Opportunity` validators that fail empty `so_what` / `goal_link` / refs.
- ✅ Generic intent layer — Intent Profiler (`intent/profiler.py`, schema-bounded coercion) + deterministic Capability Planner (`intent/planner.py`, pure rules over modality_weights + raw_text).
- ✅ `prompts/goal_anchor.py` — single rendered prompt header every generation node prepends; snapshot-pinned.
- ✅ `verifier/loop.py` — Phase 2 grounding + actionability rubric + `MAX_SOURCE_RETRIES=2` + `flagged`-not-dropped on persistent failure.
- ✅ Capability library — Cartographer, Flow Tracer, Teacher (`capabilities/`); each reads the six deterministic tools, renders the goal anchor, coerces strict-JSON LLM output into typed Insights / Claims.
- ✅ `graph.py` — full `StateGraph[ArchaeologistState]` with conditional edges on `capability_plan.active`, `RECURSION_LIMIT=15`. Q&A re-exported as a side channel per docs/03.
- ✅ Hard CI rule (`test_no_purpose_enum.py`) — grep over the source tree rejects `state.purpose` / `purpose_enum` / `Purpose = Literal[`.
- ✅ Agents fast lane: **104 passed**; `ruff` + `ruff format` + `mypy --strict` clean across 42 source files.

> **Note on the LLM-bound accuracy gates** (Profiler ≥90%/field, Planner F1 ≥90%, two-intent divergence ≥50% on flask, actionability ≥80%). Same documented relaxation as Phase 2's grounding/verifier numbers: code is unblocked, the harness runs end-to-end, only the labeled-dataset rows + paid Groq run are paused. The moment paid credits land, label `intent_profiling_v1.jsonl`, `planner_correctness_v1.jsonl`, and `actionability_v1.jsonl`, then `uv run python -m repopilot_evals run …` for each — they convert to measured ✅ without any code change.

## Phase 4 — entry checklist (the active block)

Phase 4 work cannot start until these are checked. Restated from [`docs/05` § Phase 4 prompt](05_PHASE_PROMPTS.md#phase-4-prompt--experience-fastapi--nextjs--synchronized-code-viewer) for emphasis:

- [ ] **`flask` indexed into Neon** at the snapshot the demo will run against. Without a real index, none of the SSE / tour endpoints can be exercised end-to-end and the "time-to-first-useful-output ≤ 12 s" gate is unmeasurable.
- [ ] **`apps/web/` Next.js 15 scaffold** with App Router + RSC compiles cleanly under `pnpm` (or `npm`) on a fresh checkout. Today the scaffold has `package.json` only.
- [ ] **`apps/api/` FastAPI scaffold** with `uv run uvicorn …` running. Today only the placeholder skeleton exists.
- [ ] **`POSTGRES_DSN` (Neon) and `REDIS_URL` reachable from the dev box.** Phase 4 is run "on the metal" — the API + web app start with `uv run uvicorn …` and `pnpm dev`, and read every infra dep from a connection string in `.env`. **Docker is deferred to Phase 6 hardening**; nothing in the Phase 4 gate requires a `docker compose up`.
- [ ] **`LANGSMITH_API_KEY` still provisioned** (carried over from Phase 2). The retrieval-path chip cross-check uses LangSmith traces.

If any box is unchecked when Phase 4 work begins, fix that first — the gates downstream (SSE survives 5 min, Lighthouse a11y ≥ 90, Playwright e2e) can't run otherwise.

> **Phase 4 explicitly skips Docker.** The original Phase 4 spec gated on `docker compose up` reaching a working demo. That requirement is **deferred to Phase 6** ("Harden and ship"), where the Compose file becomes part of the v0.1.0 quickstart story. Phase 4's "cold-start" gate is restated as: **on a fresh checkout, `uv sync` + `pnpm install` + two terminals (`uvicorn`, `pnpm dev`) yield the working flask demo against Neon Postgres + an external Redis** (Upstash, fly.io, or a local install — connection string in `.env`). When the user moves to Docker in Phase 6, the FastAPI / Next.js / arq workers carry over unchanged because they read everything through env vars today.

## Phase 4 — kickoff outline (read after entry checklist clears)

When the checklist above is green, read [`docs/05` § Phase 4 prompt](05_PHASE_PROMPTS.md#phase-4-prompt--experience-fastapi--nextjs--synchronized-code-viewer) and ship in this order (the prompt's "Implementation order" section is authoritative; this is the at-a-glance):

1. **FastAPI endpoints + SSE event shape** (`apps/api/routes/`) — `POST /repos`, `GET /repos/{id}/status`, `POST /tours`, `GET /tours/{id}/stream`, `POST /tours/{id}/ask`, `GET /chunks/{id}`. SSE events carry `v: 1` and the eight event types in the prompt; heartbeats every 15 s. **Contract tests first** (pytest + httpx ASGI client + sse-starlette).
2. **TS client generated from OpenAPI** → `apps/web/lib/api/`. Lets the frontend type-check the contract instead of hand-rolling it.
3. **Static URL-input page** → routes immediately to pre-context capture (LEARN vs CONTRIBUTE chip strip). Indexing runs **in parallel** in the background; the user never stares at a progress bar with nothing to do.
4. **Tour view: streamed text panel (left)**, then **synchronized shiki code viewer (right)**, then the **click-to-highlight link** between them. Zustand store keeps `sections`, `claims by id`, `selected claim`, `code viewer file/range`. Verified-badge UI + retrieval-path chip on every claim.
5. **Mermaid renderer** for `diagram` events.
6. **"Ask anything" input** that auto-opens the first ref of the first claim of the answer in the code viewer (same `claim` event handler as the tour).
7. **Playwright e2e gate** — paste `https://github.com/pallets/flask` → wait for `ready` → start tour → click 5 claims → assert code viewer highlights the correct lines. Plus the 5-minute SSE idle test and the Lighthouse audit script (fails on < 90).

Phase 4 has **no new schema, no new agent code** — it consumes Phase 3's `ArchaeologistState` + `build_graph()`. The risk surface is the frontend ergonomics + SSE plumbing, not the model.

---

## How to advance the phase

1. Pick the next unchecked item on the active phase's checklist and write the test first.
2. When all of the active phase's gate items pass on the machine (not just in mocks), flip the phase to 🟢, flip the next to 🟡, update **Last verified gate**, and add a "what landed" section above with the commit and one-line headline.
3. Paste the next phase's prompt from `docs/05_PHASE_PROMPTS.md` into a fresh session.

> If a phase fails its gate, it stays 🟡 — never silently advance. Either fix the failure or write down explicitly why the gate was relaxed (and update `docs/04_BUILD_PLAN.md` if the relaxation is permanent).
>
> **`CURRENT_PHASE.md` lives or dies on being correct.** If the active phase changes — even just a checklist item flipping — update this file in the same commit. The Phase 1 → Phase 2 → Phase 3 transitions in this session all forgot to update it; that's a documentation-layering bug, caught here once and now noted as the rule.
