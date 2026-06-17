# RepoPilot — Documentation Set Overview

This folder is the **complete design spec.** Phases 0, 1, and 2 of `docs/04_BUILD_PLAN.md` are now implemented and on `main`; the rest of the build plan is what the docs still drive against. This file summarises every doc and how they relate, so a new reader (human or AI) can orient in one page.

> Prefer the [Graphify knowledge graph](../graphify-out/) over reading these raw — `graphify query "<question>"`. See [`CLAUDE.md`](../CLAUDE.md) for the project rules. This overview is the human-readable map; `CLAUDE.md` is the authoritative rule set.

## Build progress at a glance

| Phase | Status | Commit | Notes |
|---|---|---|---|
| **Phase 0 — Foundation** | ✅ shipped, CI green | `a684bd7` (code), `0f170fa` (CI fixes) | Monorepo, `LLMProvider` (Groq → Cerebras → Hugging Face + cache + 429 backoff), `Settings`, Docker Compose, ruff/mypy/pytest/CI. |
| **Phase 1 — Ingestion** | ✅ shipped, CI green | `c4747e6` | clone → parse → chunk → graph → embed → persist. Alembic migration, `LLMProvider.embed()`, idempotent on `(repo_url, head_sha)`. The 90 s `httpx` gate has been validated. |
| **Phase 2 — Hybrid Retrieval + Q&A spine** | ✅ shipped, CI green; eval measurement still pending | `6065ccf` | Six tools (`read_chunks`, `vector_search`, `graph_traverse`, `graph_query`, `graph_metrics`, `github_issues` stub), Verifier (D4 + M1 + S4), Q&A loop (hop budget 3). The only remaining Phase 3 entry blockers are running the labeled grounding and verifier evals. |
| Phase 3 — Orchestration + Learn | not started | — | Full `ArchaeologistState`, Intent Profiler, Capability Planner, Cartographer/Flow Tracer/Teacher. **Blocked** on the Phase 3 entry checklist in `docs/05`. |
| Phase 4 — Experience | not started | — | FastAPI SSE + Next.js synchronised code viewer. |
| Phase 5 — Contribute mode | not started | — | Lane A/B/C scanners, Opportunity Ranker. |
| Phase 6 — Harden and ship | not started | — | Full eval matrix in CI, README, `v0.1.0`. |

---

## How the doc set fits together

The docs form a layered chain, from "why" to "exactly what to type into Claude Code":

```
01 PROBLEM_AND_SOLUTION   →  WHY this exists + the vision (the thesis)
00 CLAUDE_BUILD_GUIDE     →  standing context pasted at every build session (the contract)
02 TECH_STACK             →  WHAT it's built with + why each choice (the toolbox)
03 ARCHITECTURE           →  HOW it's wired: agents, state, tools, verifier (the blueprint)
04 BUILD_PLAN             →  WHEN/in what order to build it: 7 phases + gates (the schedule)
05 PHASE_PROMPTS          →  paste-ready prompts to execute each phase (the script)
```

**Reading order for a build session:** `CLAUDE.md` → `docs/00` → `docs/03` → `docs/04` → the matching `docs/05` phase block.

> The pre-build doc-review punch list (`06_FUTURE_IMPROVEMENTS.md`) was applied in full and removed before Phase 0 — all of its M/S/W items are now folded into the docs above. Git history retains the original review for context.

---

## Per-doc summaries

### 01 — Problem and Solution *(the thesis / "why")*

The richest, most persuasive doc. Establishes:
- **The problem:** opening an unfamiliar 50k-line Python repo, a junior dev or first-time OSS contributor has one unanswered question — *"where do I look first, and why?"* READMEs are marketing, file trees show shape not flow, issue labels lie, and general LLM chat is fluent but hallucinates structure.
- **Why every existing tool fails this user** (comparison table: GitHub search, Sourcegraph/Cody, ChatGPT/Claude, Cursor/Copilot, CodeSee/Sourcetrail, CONTRIBUTING.md).
- **Who it's for:** anyone who can finish *"I'm here because…"* on a public Python repo. Purpose-driven, **not** role-driven.
- **The solution + 14 key features:** free-text intent capture, Intent Profiler, Capability Planner, shared capability library, parallel-with-indexing flow, verified grounding badges, hybrid retrieval, guarded suspicion language, actionability contract, synchronized code viewer, intent-aware Q&A, trust surfaces, CTA-ended briefings, free-tier survivability.
- **Four full walkthroughs** (Learner/Django, Contributor/httpx, Builder/FastAPI, Security researcher/Flask) proving the same architecture produces radically different output per intent — and that it's *not* a hidden 3-bucket system.
- **The core bet:** capture intent as free text *before* analysis, profile it, plan capabilities over it. **No per-persona code paths.**
- **The five principles, success criteria** (merge-blocker bars like grounding ≥90%), and a **hard scope fence** (Python only, public repos, no IDE plugin, no team mode, no code execution, no paid APIs).

### 00 — Claude Build Guide (Standing Context) *(the contract)*

The "paste this at the top of every build session" condensation — the standing context every phase prompt assumes:
- Project one-liner, the pre-context bet, and *why pre-context runs in parallel with indexing* (time-to-first-useful-output is the metric, not time-to-index).
- The four trust surfaces and five principles.
- **Iteration 1** (Contribute = opportunity engine: Lanes A/B/C/D feeding one ranked Opportunity list) and **Iteration 2** (the "no stat dumps" output contract: the *three laws of output* — goal-anchored, numbers-carry-consequences, every-section-ends-in-motion — enforced at four layers: state validation, prompt contracts, verifier rubric, eval harness).
- The free/local tech-stack table and Groq free-tier survival strategy.
- The **agent roster** (Intent Profiler → Capability Planner → Cartographer / Flow Tracer / Teacher / Lanes A-C / Decision Archaeology / Q&A / Verifier).
- **State schema rules** (Pydantic v2; no agent writes another's field; mutations only via node returns; `recursion_limit=15`; *no code may branch on a `purpose` enum*).
- The **Per-PR Definition of Done**.

### 02 — Tech Stack *(the toolbox — every choice + why + what was rejected)*

Hard constraint: **the whole stack runs on a laptop with free-tier services only.**
- **LLMs:** Groq `llama-3.3-70b` (judgment), `qwen3-32b` (tracing + verifier), `llama-3.1-8b-instant` (cheap/high-volume); Hugging Face Inference Providers as the universal final fallback. **Embeddings run in-process via `sentence-transformers` (HF weights `nomic-ai/nomic-embed-text-v1.5`)** — no daemon, no Docker. A custom `LLMProvider` hides all of this behind a Groq→Cerebras→Hugging Face fallback chain with a SQLite cache and 429 backoff. Includes the per-agent model map and Groq per-model quota survival strategy.
- **Orchestration:** LangGraph (typed StateGraph, Postgres checkpointing) + LangSmith.
- **Code intelligence (deterministic, NO LLM):** tree-sitter, NetworkX, GitPython, PyGithub. This is the layer where "truthful" is *purchased* — the AST builds the graph, the LLM never invents it.
- **Storage:** Postgres + pgvector; Redis + arq; SQLite cache.
- **Backend:** FastAPI + sse-starlette. **Frontend:** Next.js 15, TypeScript, Tailwind v4, shiki, mermaid, Zustand.
- **Quality:** ruff, mypy --strict, pytest (80%), pre-commit + gitleaks, GitHub Actions, Docker Compose. Ends with a full ASCII stack diagram.

### 03 — Architecture *(the blueprint — the keystone doc)*

The detailed engineering design:
- **Agent topology** (ASCII): pre-context layer → branch subgraphs → a Verifier loop that *wraps every generating node* with a bounded retry edge → SSE stream. *(This section still reflects the older Intent Router / learn-contribute-question buckets — see the drift note above.)*
- **Agent table:** every agent's model, job, tools, and which state fields it reads/writes.
- **State schema (Pydantic v2)** — the actual code for `CodeRef`, `Claim`, `Insight`, `Opportunity`, `TourSection`, `VerifierObjection`, and the top-level `ArchaeologistState`, plus the six enforced state rules. The `Insight` model's `min_length=1` validators on `so_what`/`goal_link` are how "no stat dumps" is enforced at the type level.
- **The six deterministic tools** (`vector_search`, `graph_traverse`, `graph_query`, `graph_metrics`, `read_chunks`, `github_issues`) and the "six and no more" rule.
- **Hybrid retrieval pattern** (vector finds, graph completes, judge bounds at ≤3 hops), Q&A driving the synchronized code viewer, the four **trust surfaces**, and how pre-context flows through every node.
- Deep detail on **Iteration 1** (Lane A/B/C scanners) and **Iteration 2** (four-layer enforcement), LangSmith setup, and a **failure-modes-and-cost-design** table.

### 04 — Build Plan *(the schedule — 7 phases, each with a hard gate)*

Seven phases, each ending in a **working demo + a binary, measurable quality gate** (no gate pass = no ship):
- **Phase 0 — Foundation:** monorepo, `LLMProvider` with cache/backoff/fallback, CI, Docker Compose. *Gate: forced-429 falls back to Hugging Face in <30s; stack up in ≤90s.*
- **Phase 1 — Ingestion:** clone → tree-sitter parse → structural chunk → NetworkX graph → embed → persist; idempotent on HEAD SHA. *Gate (httpx): index ≤90s, exact line-spans, known call chain exists as a graph path.*
- **Phase 2 — Hybrid Retrieval + Grounded Q&A (THE SPINE):** the 6 tools, Q&A mini-graph, verifier grounding loop, eval harness v1 in CI. *Gate: grounding ≥90%, multi-hop test, forced-hallucination test.*
- **Phase 3 — Orchestration + Learn:** full `ArchaeologistState`, Intent Profiler + Capability Planner, Learn capabilities, verifier+actionability loop, checkpoint resume. *Gate: profiler ≥90%/field, planner F1 ≥90%, two intents on flask differ ≥50%, CI grep asserts no `if state.purpose ==`.*
- **Phase 4 — Experience:** FastAPI + versioned SSE protocol, Next.js streaming UI, the **synchronized shiki code viewer**, verified badges, retrieval-path chips, first-impression panel. **Runs on the metal — Docker deferred to Phase 6.** Postgres + Redis are reached via connection strings. *Gate: cold-start demo on flask via `uv sync` + `pnpm install` + `uvicorn` + `pnpm dev`, time-to-first-output ≤12s, Lighthouse a11y ≥90.*
- **Phase 5 — Contribute (Iteration 1):** planner-activated Lanes A/B/C → deterministic ranker → Teacher briefing, considered-and-rejected trail, per-opportunity CTAs. *Gate: top-3 approachability ≥70%, file-mapping ≥80%, suspicion legitimacy ≥75%, banned-vocab regex passes.*
- **Phase 6 — Harden and ship:** full eval matrix (fastapi/httpx/flask) in CI, security pass, honest README, tag `v0.1.0`.

Ends with the **Per-PR Definition of Done** and an **11-item prioritized post-v0.1 backlog** (incremental indexing, comprehension quiz, TypeScript support, HITL interrupts, README "take the tour" badge, semantic cache, verifier fine-tune, starter-branch scaffolding, etc.).

### 05 — Phase Prompts *(the script — paste-ready)*

One **paste-ready Claude Code prompt per phase (0–6)**, each used on top of doc 00's standing context — turning doc 04's checklist + gate for that phase into an executable instruction. This is the operational bridge: doc 04 says *what* a phase delivers; doc 05 is the literal text you feed the agent to *build* it.

---

## One-paragraph takeaway

RepoPilot's docs describe a **multi-agent, grounding-first codebase-onboarding tool** whose single differentiating bet is capturing the user's *intent* in free text before any analysis and adapting a shared library of specialized agents to it — with truthfulness enforced by a deterministic AST/graph layer and a separate verifier model, and quality enforced by hard, measured phase gates. The spec is unusually disciplined: a strict scope fence, merge-blocker metrics, a documentation-layering rule, and an "everything runs free on a laptop" constraint. The pre-build doc review has been fully applied and the spec is consistent across docs 00–05.
