# 04 — Build Plan

Seven phases (0–6). Each phase ends in a **working demo plus a hard quality gate with measurable numbers**. No phase ships if its gate fails. The plan is sized for a solo developer working **3–14 days per phase, including eval-dataset labeling time** (~30 hours of skilled manual labeling spread across Phase 2, Phase 3, Phase 5 — invisible in code stats but real in calendar). Expect Phase 4 (Experience) to anchor the long end at 10–14 days; Phase 1 (Ingestion) and Phase 3 (Orchestration) at 7–10 days.

The structure of each phase below:

- **Goal** — what working code exists at the end.
- **Task checklist** — what to build, in order.
- **Production-grade specifics** — non-negotiable details the implementer must not paper over.
- **Quality gate** — measurable, binary numbers. Either pass and ship, or fail and iterate.

The `Per-PR Definition of Done` (at the end of this file) applies to every PR within every phase, not just the gate-passing PR.

---

## Phase 0 — Foundation

**Goal.** A monorepo that builds, tests, and lints cleanly. `LLMProvider` works against Groq with cache, backoff, and Hugging Face fallback. CI is green.

**Task checklist**

- [ ] Monorepo layout:
  ```
  apps/
    api/                FastAPI app (Phase 4)
    web/                Next.js app (Phase 4)
  packages/
    core/               shared types, config, LLMProvider
    ingestion/          tree-sitter + NetworkX + indexing
    agents/             LangGraph nodes & state
    evals/              eval harness + datasets
  ```
- [ ] Python project per package, pinned via `uv` or `pdm`. Single root `pyproject.toml` orchestrating workspace.
- [ ] `ruff` + `mypy --strict` + `pytest` + `pytest-asyncio` + `pytest-cov` configured per package.
- [ ] `pre-commit` with hooks: ruff, mypy (touched files), gitleaks, end-of-file fixer, trailing whitespace.
- [ ] GitHub Actions CI workflow: install → lint → typecheck → test → coverage gate (80%) → eval-runner stub.
- [ ] `docker-compose.yml` for: Postgres 16 with `pgvector`, Redis 7, Hugging Face. Pulls `Qwen/Qwen2.5-Coder-7B-Instruct` and `nomic-ai/nomic-embed-text-v1.5` on first up.
- [ ] `packages/core/llm/provider.py` — `LLMProvider` class:
  - Async interface: `async def generate(model: ModelId, messages: list[Message], **kwargs) -> Response`
  - Backed by Groq SDK
  - SQLite cache keyed on `sha256(model + canonical_json(messages) + kwargs)`
  - Exponential backoff w/ jitter on 429 (max 5 attempts)
  - Provider fallback chain: Groq → Cerebras → Hugging Face (configurable per call)
  - Tracks `tokens_used` per model in a shared counter
- [ ] `packages/core/llm/models.py` — `ModelId` enum mapping logical names ("intent_router", "cartographer", "verifier") to physical model strings. Agents only ever reference the logical name.
- [ ] Unit tests for `LLMProvider`:
  - Cache hit avoids the API call
  - 429 retries the right number of times
  - **Forced 429 storm falls back to Hugging Face and returns a response** (no test mocks the fallback away)
  - Token counter increments correctly

**Production-grade specifics**

- `mypy --strict` from day one. No `Any` outside narrow boundary functions, each of which is annotated `# type: ignore[no-any-return]  # boundary: external SDK` with the reason.
- Logging via `structlog` only. No `print()`. JSON renderer in production, dev renderer in tests.
- Settings via `pydantic-settings`. `.env.example` checked in; `.env` git-ignored. `gitleaks` runs in pre-commit. **Required env vars:** `GROQ_API_KEY`, `HUGGINGFACE_API_KEY`, `GITHUB_TOKEN` (read-only `public_repo` scope; used by Lane A for 5,000 req/hr instead of 60), `DATABASE_URL`, `REDIS_URL`, `LANGSMITH_API_KEY` (optional), `VERIFIER_CONCURRENCY` (default 4), `MAX_TOURS_PER_IP_PER_HOUR` (default 5).
- Per-IP rate limit on `POST /tours` via `slowapi` middleware. Default 5 tours/IP/hour. When exceeded, returns 429 with body `{"error": "QUOTA_EXHAUSTED", "retry_after_seconds": N}`.
- Docker Compose uses **named volumes** for postgres so data survives container restarts.
- The Hugging Face service in compose preloads `Qwen/Qwen2.5-Coder-7B-Instruct` and `nomic-ai/nomic-embed-text-v1.5` via an `entrypoint` script — not lazily on first call (Phase 1 will need them ready).

**Quality gate**

- [ ] `make ci` passes locally and in GitHub Actions.
- [ ] Coverage ≥ 80% on `packages/core`.
- [ ] **Forced-429 test**: with Groq mocked to return 429 indefinitely, `LLMProvider.generate(...)` returns a real response from Hugging Face within 30s.
- [ ] `docker compose up -d` brings the full stack up clean on a fresh checkout in ≤ 90 s.

---

## Phase 1 — Ingestion

**Goal.** Given a public GitHub URL, an arq worker clones, parses, chunks structurally, builds a NetworkX dependency graph, embeds chunks via Hugging Face nomic-ai/nomic-embed-text-v1.5, and persists everything to Postgres + pgvector. Idempotent on HEAD SHA.

**Task checklist**

- [ ] `packages/ingestion/clone.py` — clone via GitPython into a tempdir; record HEAD SHA.
- [ ] `packages/ingestion/parse.py` — tree-sitter + tree-sitter-python; produce a typed `ParsedFile` per file with function/class spans.
- [ ] `packages/ingestion/chunk.py` — structural chunker: one chunk per function and per class (with method index). Class chunks include the class signature + docstring + method *names* but not method bodies; method chunks are independent. Line spans preserved exactly.
- [ ] `packages/ingestion/graph.py` — NetworkX builder. Edges:
  - `calls`: function A calls function B (resolved via scope-aware AST walk)
  - `imports`: file X imports symbol Y
  - `inherits`: class C extends class D
- [ ] `packages/ingestion/summary.py` — `llama-3.1-8b-instant` chunk summaries via `LLMProvider`. Cached by `(SHA, file_path, chunk_id)`.
- [ ] `packages/ingestion/embed.py` — Hugging Face `nomic-ai/nomic-embed-text-v1.5` embedder. Batched.
- [ ] `packages/ingestion/persist.py` — write to Postgres:
  - `chunks` table: `id, repo_id, file_path, start_line, end_line, symbol, kind, summary, content`
  - `chunk_embeddings`: pgvector column, ivfflat index, **`embedding_model_name TEXT NOT NULL`** + **`embedding_model_version TEXT NOT NULL`** so future model bumps don't silently corrupt retrieval
  - `graph_adjacency`: JSONB sidecar (`{node: {calls: [], called_by: [], imports: [], ...}}`)
  - `repos`: `id, url, head_sha, status, indexed_at, embedding_model_name, embedding_model_version, unresolved_dynamic_count, python2_syntax BOOL, indexing_stages JSONB`
- [ ] `apps/api/jobs/index_repo.py` — arq job that runs the pipeline end-to-end.
- [ ] Idempotency: if `(repo_url, head_sha)` already indexed, no-op.
- [ ] **Revisit staleness check.** When a known `repo_url` is re-submitted, the API does a lightweight `git ls-remote <repo_url>` (no clone) to read the current default-branch HEAD before deciding what to do. If it matches `repos.head_sha`, the cached index is served immediately. If it differs, the API returns `{ status: "stale", indexed_sha, remote_sha, commits_behind_estimate }` and the frontend renders a banner ("This repo has new commits since we last indexed it (~N commits). Re-index? (~90s)"). Re-indexing is opt-in; the user can also choose to stream a first-impression and tour off the cached index while deciding. Test: `test_revisit_with_advanced_remote_returns_stale_status`.
- [ ] **Concurrent-indexing lock.** Before any work, the arq job acquires a Postgres advisory lock keyed on `hashtext(repo_url || head_sha)`. A second concurrent job for the same key short-circuits to "wait for existing indexing", polls `repos.status`, and returns the cached `repo_id` once the first completes. Test: `test_concurrent_indexing_same_repo_does_not_duplicate`.
- [ ] **Embedding model versioning.** Indexing job records the embedding model name + version it used. Q&A always embeds the query with the model that matches the stored vectors. When the configured model differs from stored, the repo is automatically marked for re-index. Test: `test_query_embedded_with_stored_model`.
- [ ] **Typed errors.** Every fail-edge in the indexing pipeline emits an `ArchaeologistError` (codes defined in docs/03). Tests: `test_repo_without_python_files_rejected_with_useful_message`, `test_invalid_repo_url_returns_typed_error`, `test_partial_indexing_failure_records_stage`.

**Production-grade specifics**

- **Indexing skip-list** (configurable, defaults): directories `vendor/`, `third_party/`, `_vendor/`, `node_modules/`, `__pycache__/`; files matching `*.ipynb` (deferred to v0.2, surfaced in scope fence); files with `# Generated by` header. `.pyi` stub files are indexed but tagged separately so Cartographer can distinguish them from runtime modules. Python 2 syntax detected (presence of `print` statement, `except X, e:`) and tagged with `python2_syntax=true`; tours surface a soft warning when this flag is set.
- Chunking on **AST boundaries** is non-negotiable. A test asserts that no chunk starts or ends mid-statement on a chosen file.
- The graph builder resolves calls scope-aware (handle `self.method()`, aliased imports, `from x import y as z`). It is OK to be incomplete for dynamic patterns (decorators that rewrite signatures, `getattr`) — log unresolved calls as warnings, don't invent edges.
- `graph_adjacency` stored as JSONB so traversal queries don't need a graph DB.
- pgvector index: `ivfflat (embedding vector_cosine_ops) WITH (lists = 100)` — adjust if recall < 95% on the eval set.
- Concurrency in summary/embedding pipelines bounded by `asyncio.Semaphore` tuned to Groq's per-minute rate.
- Hard cap: any repo with > 200k LOC is rejected at the queue boundary in v1.

**Quality gate** — measured on `httpx` (≈ 50 kLOC):

- [ ] Indexing completes in ≤ 90 s on a developer laptop with warm Hugging Face models.
- [ ] **Line-span correctness**: on 20 randomly sampled chunks, `chunk.content == repo_file[start:end]` exactly (no off-by-one). Automated test.
- [ ] **A known call chain exists as a graph path** — pick `httpx.Client.send → httpx.Client._send_single_request → httpx._transports.default.HTTPTransport.handle_request` and assert `nx.has_path(graph, ...)`.
- [ ] Idempotent: re-running the job on the same HEAD SHA exits immediately with status `already_indexed`.

---

## Phase 2 — Hybrid Retrieval + Grounded Q&A (THE SPINE)

**Goal.** End-to-end Q&A over an indexed repo with hybrid retrieval (vector → graph), a sufficiency judge, and a Verifier grounding loop. LangSmith traces every run. Eval harness v1 lives in CI.

**Task checklist**

- [ ] `packages/agents/tools/vector_search.py` — pgvector k-NN with cosine distance.
- [ ] `packages/agents/tools/graph_traverse.py` — BFS over `graph_adjacency`. Typed return: `list[Path]` where each path is `list[CodeRef]`.
- [ ] `packages/agents/tools/graph_query.py` — entry_points (in-degree 0), hubs (top-N fan-in), layers (Louvain), callers, callees.
- [ ] `packages/agents/tools/graph_metrics.py` — per-symbol pack.
- [ ] `packages/agents/tools/read_chunks.py` — read by `CodeRef`.
- [ ] `packages/agents/tools/github_issues.py` — PyGithub with caching.
- [ ] `packages/agents/qa/graph.py` — Q&A LangGraph mini-graph: `vector_search → graph_traverse → judge_sufficiency → (expand | answer) → verifier`.
- [ ] `packages/agents/verifier/grounding.py` — for each `Claim`, fetch `read_chunks(claim.refs)`, ask Qwen/Qwen2.5-Coder-7B-Instruct: "Is this claim *fully supported by* these chunks? Yes/No + reason." Reject → objection appended.
- [ ] LangSmith setup: `LANGCHAIN_TRACING_V2=true`, project name from env.
- [ ] **Eval-labeling time: ~1.5 days.** Two datasets:
- [ ] `packages/evals/datasets/httpx_qa_v1.jsonl` — 15 Q&A pairs over httpx. Each has `question`, `expected_refs[]`, `expected_answer_keywords[]`. Hand-labeled by reading the actual `httpx` source.
- [ ] `packages/evals/datasets/verifier_quality_v1.jsonl` — **30 hand-labeled `(claim, chunk, expected_verdict)` triples**. Verifies the Verifier itself. Without this, "grounding accuracy ≥ 90%" is a number we can't trust. Gate: Verifier accuracy ≥ 92% on this set.
- [ ] `packages/evals/runners/grounding.py` — runs Q&A over a dataset, computes:
  - grounding accuracy (Verifier-pass rate)
  - retrieval recall@k vs `expected_refs`
  - hallucination rate (forced-question test: 3 questions whose answers are NOT in the repo; system must say so)
- [ ] CI runs the eval harness on PR; numbers in PR description.

**Production-grade specifics**

- Hop budget: vector_search ↔ graph_traverse ↔ judge can iterate at most **3 times** before forcing an answer. Hard counter.
- The sufficiency judge is the **same** Q&A model (70B), not a separate one — it has the context already.
- `read_chunks` is the **only** tool that returns source text. Vector search returns chunks-with-metadata; the agent still calls `read_chunks` to see content for the answer. This is a deliberate choke point so the Verifier can reuse the same input.
- Forced-hallucination test: questions like "What is the unicorn module in httpx?" must return "I couldn't find that in the repo" — not invent a module.

**Quality gate**

- [ ] **Verifier accuracy ≥ 92%** on `verifier_quality_v1`. Gate this *before* trusting `grounding accuracy`.
- [ ] **Grounding accuracy ≥ 90%** on `httpx_qa_v1` (only meaningful if Verifier accuracy gate passed).
- [ ] **Multi-hop chain test**: pick 3 questions that require ≥ 2 hops; assert the answer references chunks reached via `graph_traverse`, not vector hits alone.
- [ ] **Forced-hallucination test**: 3 not-in-repo questions; all 3 produce an honest "not found" answer.
- [ ] **Zero quota exhaustion** during a full eval run.
- [ ] LangSmith traces visible for every eval entry, with the full tool-call sequence inspectable.

---

## Phase 3 — Orchestration + Learn subgraph

**Goal.** Full `ArchaeologistState`. Generic intent layer (Intent Profiler → Capability Planner) runs reliably. Capability library (Cartographer, Flow Tracer, Teacher, etc.) is composable per the planner's output. Verifier loop integrated, including the Iteration-2 actionability rubric. Postgres checkpoints survive kill/resume.

**Task checklist**

- [ ] `packages/agents/state.py` — `ArchaeologistState` exactly as specified in `03_ARCHITECTURE.md` (CodeRef, Claim, Insight, Opportunity, TourSection, VerifierObjection).
- [ ] `packages/agents/intent/profiler.py` — **Intent Profiler (generic intent layer, step 1).** 8B model. Takes the user's free-text intent statement and emits an `IntentProfile` (modality_weights, focus_keywords, audience_framing, output_shape_preference, suggested success_criterion, raw_text preserved). Returns a confirmable draft — the user accepts or edits via the chip strip before the graph proceeds.
- [ ] `packages/agents/intent/planner.py` — **Capability Planner (generic intent layer, step 2).** Pure Python function `plan(IntentProfile) -> CapabilityPlan`. Rules over `modality_weights` + `raw_text` keyword signals decide which capabilities are active and how each is tilted. No LLM; verifiable in CI on a labeled set. Falls through to a sensible default plan (`cartographer + teacher`, `output_shape=narrative`) if no rules match.
- [ ] Goal-anchor helper in `packages/agents/prompts/goal_anchor.py`: renders the leading prompt block from `intent_profile.raw_text` + the planner-derived tilts. **Every** generation prompt template starts with this block. A snapshot test pins the rendered output.
- [ ] `packages/agents/learn/cartographer.py` — uses `graph_query` (entry_points, hubs, layers) → emits `Insight[]`. Reads `intent_profile.focus_keywords` and `capability_plan.cartographer_tilt` (`balanced` / `data_hubs` / `decision_hubs` / `hot_path`) and biases hub selection accordingly. Each Insight has `finding/because/so_what/refs/goal_link`. Validators enforce non-empty `so_what` and `goal_link`, and the `goal_link` must cite something in `intent_profile`.
- [ ] `packages/agents/learn/flow_tracer.py` — picks one or more flows aligned to `capability_plan.flow_tracer_targets` (planner-derived from `intent_profile.focus_keywords` + `raw_text` signals). Walks via `graph_traverse`. Emits `Insight[]`.
- [ ] `packages/agents/learn/teacher.py` — sequences map+flow into `TourSection[]`, emits mermaid diagrams, every section ends in motion.
- [ ] `packages/agents/verifier/loop.py` — grounding check + actionability rubric. Source-node retry edge with budget 2.
- [ ] LangGraph wiring: `StateGraph[ArchaeologistState]` with conditional edges; Postgres checkpointer.
- [ ] **Eval-labeling time: ~2 days.** Three datasets, each requires careful manual labeling:
- [ ] `packages/evals/datasets/intent_profiling_v1.jsonl` — 50 free-text intent statements (paraphrasing the 12 planner-mapping examples in `docs/01` + 38 originals) labeled with the expected `IntentProfile` fields per row.
- [ ] `packages/evals/datasets/planner_correctness_v1.jsonl` — same 50 entries, additionally labeled with the expected `CapabilityPlan.active` subset and key tilts.
- [ ] `packages/evals/datasets/actionability_v1.jsonl` — 20 tour sections labeled `actionable` / `not_actionable` with rubric reasons.
- [ ] `packages/evals/runners/checkpoint_resume.py` — start a tour, kill the process mid-flight, resume from checkpoint, assert the same final state (modulo timestamps).

**Production-grade specifics**

- **Each agent's prompt fits in ≤ 2000 input tokens.** Enforced by a test that loads each prompt template and asserts `tiktoken` count.
- The Insight model validators do real work. A test asserts that constructing `Insight(finding="x", because="y", so_what="", refs=[...], goal_link="z")` raises.
- The Iteration-2 prompt contracts include ❌/✅ contrastive examples. A test snapshots the rendered prompts so a refactor that weakens them is caught in code review.
- The Verifier returns structured JSON (Pydantic schema), not free text. Failing to parse = treat as rejection.
- `recursion_limit=15` set on the compiled graph.

**Quality gate**

- [ ] **Intent Profiler per-field accuracy ≥ 90%** on `intent_profiling_v1` (each of modality_weights, focus_keywords, audience_framing, output_shape_preference evaluated independently).
- [ ] **Capability Planner F1 ≥ 90%** on `planner_correctness_v1` (precision + recall on the activated-capability subset).
- [ ] **Capability library dependencies satisfied** — for every active capability in a plan, every declared dependency is also active; a topological sort exists; and capabilities run in dependency order under LangGraph compilation. Test name: `test_capability_library_dependencies_satisfied`.
- [ ] **Intent shapes the output** — running two materially different `IntentProfile`s (e.g., "explain how request lifecycle works" vs "audit auth surface for fragility") on flask produces `draft_tour`s that differ structurally by ≥ 50% on a sectional-overlap metric.
- [ ] **No purpose-enum branches in code** — a CI grep asserts `if state.purpose ==` does not appear anywhere under `packages/agents/`.
- [ ] **Verifier concurrency works**: `test_verifier_per_section_concurrent` passes — 30 synthetic claims through Verifier with concurrency=8 complete in ≤ 1.5× a single-claim baseline.
- [ ] **Verifier cache works**: identical (claim, chunks) pair returns from SQLite cache with zero LLM call.
- [ ] **Streaming verification works**: claims stream to client as `unverified` and upgrade to `✓ grounded` (or `flagged`) when verdict lands.
- [ ] **Full Learn-shaped tour on `flask` repo in < 4 minutes** wall clock, with every factual claim ref-linked (no `flagged` claims in the demo run).
- [ ] **Checkpoint resume passes** on the runner test (kill at any point in the graph; resume produces identical final state).
- [ ] **Actionability ≥ 80%** on `actionability_v1`.
- [ ] **No node prompt exceeds 2000 input tokens.**
- [ ] LangSmith trace for the demo run reviewed and linked in the PR.

---

## Phase 4 — Experience

> **Honest budget: 10–14 days. This is the longest phase.** The synchronized code viewer, the streaming SSE protocol with verified-badge upgrades, and the intent-edit re-plan flow are each their own subproject. If a prior phase was tight, do not borrow from this one.

**Goal.** A user pastes a URL and watches a tour stream in. The synchronized code viewer is the centerpiece. **No Docker in Phase 4** — Postgres + Redis are reached via connection strings (`POSTGRES_DSN` → Neon; `REDIS_URL` → Upstash/local). The Phase 4 cold-start gate is `uv sync` + `pnpm install` + `uvicorn` + `pnpm dev` reaching a working demo. Docker Compose moves to Phase 6's quickstart story.

**Task checklist**

- [ ] FastAPI endpoints:
  - `POST /repos` — enqueue indexing; returns `repo_id`.
  - `GET /repos/{repo_id}/status` — `queued | indexing | ready | error | stale` (`stale` includes `indexed_sha`, `remote_sha`, `commits_behind_estimate`; UI renders the revisit-staleness banner from §Phase 1).
  - `POST /tours` — start a tour given `repo_id`, optional `purpose` hint.
  - `GET /tours/{tour_id}/stream` — SSE stream of tour events.
  - `POST /tours/{tour_id}/ask` — Q&A escape hatch.
- [ ] SSE event protocol (versioned):
  - `section_start { order, title }`
  - `token { text }`
  - `claim { id, text, refs[], status, verifier_note?, provenance }` — `provenance` is a typed source descriptor: `{kind: "vector_then_graph", k, hops}` | `{kind: "graph_only", query}` | `{kind: "deterministic_detector", name}` | `{kind: "structural_pattern", name}`. `verifier_note` is the one-liner shown on hover when status is `verified` or `flagged`.
  - `diagram { mermaid }`
  - `section_end { order }`
  - `first_impression { text }` — emitted during indexing once enough chunks exist (≥ 10s in). Powered by 8B; cached per `(repo_id, head_sha)`.
  - `done`
  - `error { code, message }`
- [ ] Next.js 15 app:
  - URL input → enqueues indexing AND immediately shows the pre-context capture flow (no waiting on indexing).
  - **Intent capture (runs in parallel with indexing)**: a single free-text "What brings you to this repo?" prompt + suggestion chips. The Intent Profiler streams its extracted `IntentProfile` into a confirmation chip strip ("I'll focus on X · Y · Z, framed for W. Edit?"). User accepts, edits chips, or rewrites the raw text. The confirmed profile is persisted to the tour POST payload and surfaced as a compact "You said: <raw_text quote>" chip at the top of the tour with a one-click "change" affordance.
  - **"First impression" panel** below the elicitation: at the 10-second mark of indexing, an 8B-generated paragraph (language mix, top entry point, top hubs, last-commit recency) streams in. Makes the wait productive; demonstrates the system is alive.
  - When the user submits the elicitation, the tour view loads. If indexing is still running, a slim progress bar shows at the top and tour generation starts as soon as `status == ready`.
  - Streamed tour panel (left) using SSE.
  - Synchronized code viewer (right) using shiki — clicking a claim scrolls to and highlights the exact lines.
  - **Verified-badge UI**: every claim with `status == "verified"` renders with a small `✓ grounded` badge. Hover reveals the verifier's one-line confirmation and the chunk it grounded against. Claims with `status == "flagged"` render with a warning treatment.
  - **Provenance chip**: every claim displays its typed provenance (vector_then_graph / graph_only / deterministic_detector(name) / structural_pattern(name)) on hover. The SSE `claim` event carries the provenance; the frontend renders it.
  - **Feedback affordance** at the bottom of each section: a quiet 👍 / 👎 / "explain" inline. Anonymous, opt-in, written to a `feedback` table with `(section_text, claim_ids, intent_profile_id, signal, freeform_text, created_at)`. No accounts. Aggregated counts visible on a maintainer-only debug page in Phase 6. v1 just collects — no clever processing.
  - **Chip-strip natural-language renderer**: a small TS utility converts `IntentProfile` into a plain-English sentence for the chip strip (e.g., *"I'll find quality cleanups in the testing layer and flag what looks fragile, framed for a casual contributor."*). Snapshot tests pin sample renderings.
  - Mermaid renderer for `diagram` events.
  - "Ask anything" input at the bottom of the tour. **Q&A answers drive the code viewer**: the first ref of the first claim in the answer auto-opens in the viewer. Same `claim` event handler as the tour.
- [ ] Zustand store: tour sections, claims by id, selected claim, code viewer state.
- [ ] Generated TypeScript client from FastAPI OpenAPI; checked in.
- [ ] Accessibility pass: keyboard navigation between claims and code, ARIA labels, focus management on streamed content.

**Production-grade specifics**

- SSE protocol versioned: events carry a `v` field. Breaking changes bump the version, server supports both during transition.
- The shiki code viewer loads only the highlighted file's content over an authenticated chunk endpoint; the full repo never ships to the client.
- A Phase-4 e2e test (Playwright) drives: paste URL → wait for indexing → start tour → click a claim → assert code viewer highlights the correct lines.
- 5-minute idle SSE connection survives via heartbeat events (`:` comment lines per SSE spec).
- Frontend is server-component-first; only the interactive panels are client components.

**Quality gate**

- [ ] **Cold-start demo (no Docker — deferred to Phase 6)**: on a fresh checkout, `uv sync` + `pnpm install` + `uv run uvicorn apps.api.main:app` (terminal 1) + `pnpm --filter web dev` (terminal 2) → open browser → paste `https://github.com/pallets/flask` → see a tour stream in. Connection strings for Postgres + Redis live in `.env`.
- [ ] **Time-to-first-useful-output ≤ 12s**: from URL paste to either (a) elicitation rendered + first-impression paragraph streaming, or (b) the first tour claim. Measured via Playwright.
- [ ] **Click a claim → exact-line highlight** works for 10 randomly-chosen claims in the demo tour (manual check + Playwright).
- [ ] **Verified-badge visible** on ≥ 90% of demo-tour claims (the rest may legitimately be flagged); verifier hover content present and accurate.
- [ ] **Provenance chip** present on every claim and Q&A answer with correct typed source (vector_then_graph / graph_only / deterministic_detector / structural_pattern); cross-checked against the originating capability.
- [ ] **Q&A drives the code viewer**: 5 sample Q&A questions auto-open the correct file in the viewer (Playwright).
- [ ] **Lighthouse accessibility ≥ 90** on the tour page.
- [ ] **SSE survives a 5-minute tour** without disconnects (load test).
- [ ] **Typed-error UX**: each `ArchaeologistError` code renders a specific actionable UI state. Test: `test_indexing_failure_renders_actionable_error_ux` exercises all 12 codes and asserts the right message + CTA per code.

---

## Phase 5 — Contribute mode (Iteration 1)

**Goal.** Switching purpose to "contribute" produces a ranked Opportunity List from Lane A/B/C, briefed by the Teacher. Every Lane C suspicion uses guarded language and ends in `confirm_before_pr`.

**Task checklist**

- [ ] **No separate "Contribute Elicitation" node.** The Capability Planner from Phase 3 activates Lane A/B/C based on `intent_profile.modality_weights.change` and `raw_text` signals. If the kind-of-contribution is underspecified (e.g., `change` weight high but no signal as to fix-issue vs. quality vs. hunt), the Teacher briefing prompt itself injects one targeted question, the answer is folded back into `intent_profile.modality_weights`, and the Planner re-plans once. No hardcoded contribute branch.
- [ ] `packages/agents/contribute/lane_a_triage.py` — planner-activated. Fetch issues → graph-backed approachability scoring → 70B explanation → `Opportunity[]`. Filter scope by `intent_profile.focus_keywords`.
- [ ] `packages/agents/contribute/lane_b_quality.py` — planner-activated. Deterministic detectors (untested hot code / missing docstrings / dead code / AST dup / churn × complexity / TODO archaeology) → 8B ranking → `Opportunity[]`. Teacher framing comes from `capability_plan.lane_b_framing`.
- [ ] `packages/agents/contribute/lane_c_suspicion.py` — planner-activated. Pre-filter structural patterns → top-N → qwen3-32b with guarded-language prompt → `Opportunity[]`. Detector subset filterable by `intent_profile.focus_keywords` (security-shaped / async-shaped / IO-shaped). Verifier post-checks for banned vocabulary and presence of `to_confirm`.
- [ ] `packages/agents/contribute/ranker.py` — deterministic ranking: weighted combination of mergeability + approachability + evidence-strength. **Lane weights come from `capability_plan.ranker_weights`** (which the Planner derived from `intent_profile.modality_weights` + `raw_text` signals). The derived weights are surfaced to the user inline in the Opportunity List header (e.g., "weighted toward problem-hunting because you said 'show me fragility'") so the "why these" question is always answered.
- [ ] `packages/agents/contribute/briefing.py` — Teacher briefing per opportunity: explain why, files to touch, suggested first step, nearest tests. Every briefing entry carries an **intent-match tag** derived from `intent_profile` so the user always sees, e.g., "matches: 'show me where it's fragile'" on the card.
- [ ] **Lane A considered-and-rejected trail**: Lane A persists not only its top-N accepted opportunities but the next-3 ranked-down items with a one-line reason ("touches a hub of fan-in 47", "no test files reference the affected module"). The Opportunity List UI shows these below the accepted list under a collapsed "considered and rejected" disclosure. This is a deliberate transparency surface — the user sees the triage, not just the verdict.
- [ ] **Per-opportunity CTAs (frontend)**: each Opportunity card renders two buttons — "Open files on GitHub" (deep links to each `files_to_touch` at the right line) and "Copy first step" (clipboard copy of `suggested_first_step`). The contribute briefing never ends in prose alone.
- [ ] **Eval-labeling time: ~2 days** across the two Phase 5 datasets.
- [ ] `packages/evals/datasets/opportunity_quality_v1.jsonl` — hand-labeled top-N opportunities per eval repo: `is_approachable` (bool), `is_legit` (bool, for Lane C), and `rejected_reasons_honest` (bool, for Lane A considered-and-rejected entries — true iff the one-line graph-backed reason is factually defensible against the graph adjacency, not invented post-hoc).
- [ ] `packages/evals/datasets/file_mapping_v1.jsonl` — for 20 opportunities, the correct `files_to_touch` set; eval checks ≥ 80% overlap.
- [ ] LangGraph wiring: Lane A/B/C run in parallel; Ranker waits on all three.

**Production-grade specifics**

- Lane C's banned-vocabulary check is enforced **in code** by the Verifier rubric, not only in the prompt. A regex test runs against the rendered Lane C output.
- The Opportunity model's `confirm_before_pr` is **required** when `lane == "C_suspicion"`; Pydantic raises if absent.
- The ranker is fully deterministic — no LLM. The Teacher only brief**s** the ranked list; it does not re-rank.
- Lane B's "missing docstrings on public API" detection only flags symbols that appear in `__all__` or at module top-level — not every private helper.

**Quality gate**

- [ ] **Top-3 issue approachability**: on 3 eval repos, the top-3 Lane A opportunities are genuinely approachable on honest manual review (≥ 70% across 9 items).
- [ ] **File-mapping eval ≥ 80%** on `file_mapping_v1`.
- [ ] **Suspicion legitimacy ≥ 75%** on `opportunity_quality_v1` Lane C entries.
- [ ] **Zero unverified claims shipped as fact** in a generated Contribute briefing on the demo repos.
- [ ] **Banned-vocabulary regex test passes** on 20 randomly sampled Lane C generations.
- [ ] **Intent-match chip visible** on every Opportunity card; chip text quotes the relevant fragment of `intent_profile.raw_text` (no fixed-enum labels).
- [ ] **Considered-and-rejected trail** shows 3 entries per repo on each demo run; each entry has a graph-backed one-line reason.
- [ ] **Rejected-reason honesty ≥ 80%** on `opportunity_quality_v1` `rejected_reasons_honest` labels — i.e., when Lane A says "ranked down because X", X is checkable against the graph or issue metadata, not LLM-confabulated.
- [ ] **CTA buttons present and functional** on every Opportunity card (Playwright: click "Open files on GitHub" → correct deep-link URL; click "Copy first step" → clipboard contains `suggested_first_step`).

---

## Phase 6 — Harden and ship

**Goal.** Full eval matrix in CI. Security pass. README with demo GIF, eval table, honest limitations. One-command quickstart verified clean. Tag `v0.1.0`.

**Task checklist**

- [ ] **Two-tier CI eval strategy.** PR-time runs a **sampled** eval (1 eval repo, smaller datasets, target ≤ 5 minutes); the full Phase 2/3/5 matrix against `fastapi`, `httpx`, `flask` runs **only on `main` post-merge** (≤ 30 minutes). Implementation: `.github/workflows/eval-pr.yml` (sampled) + `.github/workflows/eval-main.yml` (full matrix).
- [ ] CI matrix: run the full eval suite (Phase 2/3/5) against `fastapi`, `httpx`, `flask`. Numbers persisted as artifacts.
- [ ] Security:
  - [ ] **No repo content in logs.** Structlog processors strip chunk content from any log message that includes it; tested.
  - [ ] `gitleaks` in CI.
  - [ ] `pip-audit` + `npm audit` in CI; fail on high-severity.
  - [ ] CORS locked to known origins.
  - [ ] FastAPI rate limit per repo_id.
- [ ] README:
  - One-paragraph pitch, demo GIF, quickstart (`docker compose up`).
  - **Eval table** with current scores per repo.
  - **Honest limitations** section: Python-only, public repos only, ingestion cap, known failure modes (dynamic dispatch, decorator-heavy code).
- [ ] `make quickstart` script tested on a clean macOS and Linux VM.
- [ ] **Deployment topology doc** (`docs/DEPLOY.md`) — explicit hosted-demo recipe so reviewers know the stack is hostable, not just local. v0.1 baseline:
  - **Frontend (Next.js)** → Vercel free tier.
  - **API + arq worker** → fly.io or Railway (small VM, ~$5/mo). Note: Hugging Face cannot run on serverless because of the model weights.
  - **Postgres + pgvector** → Neon or Supabase free tier (verify the free tier has pgvector enabled).
  - **Hugging Face (Verifier + embeddings)** → same fly.io VM as the API (needs ≥ 4 GB RAM for `Qwen/Qwen2.5-Coder-7B-Instruct` Q4) or a sibling small VM. The verifier latency budget assumes co-located Hugging Face; cross-region adds ~80–200 ms per claim.
  - **Redis** → Upstash free tier.
  - **Document monthly cost at idle (~$5–15) and the manual scale-down steps** if the free tier limits are hit.
- [ ] Tag `v0.1.0`.

**Production-grade specifics**

- Logs include `repo_id` and `tour_id` for correlation, **never** chunk content.
- The README is honest. If grounding accuracy is 91% on flask and 87% on fastapi, both numbers go in the table.
- The "limitations" section is non-negotiable. Hand-wavy products lose trust; honest products earn it.

**Quality gate**

- [ ] **Full eval matrix green** on all three eval repos.
- [ ] **`gitleaks` and `pip-audit`/`npm audit` clean.**
- [ ] **Clean-VM quickstart** finishes in ≤ 5 minutes from `git clone`.
- [ ] **`v0.1.0` tagged** and pushed.

---

## Per-PR Definition of Done

Every PR within every phase must satisfy:

- [ ] **Documentation layering respected.** `CLAUDE.md` rules followed; `docs/00`, `docs/03`, and `docs/04` not contradicted. If the PR genuinely needs to change a layer above it (e.g., an architectural decision that invalidates `docs/03`), the PR updates that layer first, in a separate commit, with explicit justification.
- [ ] `ruff` clean.
- [ ] `mypy --strict` clean on touched packages.
- [ ] Tests written; coverage did not decrease vs. main.
- [ ] No secrets, no `print()`, no `console.log` — `structlog` only.
- [ ] Docstrings on all public functions and classes.
- [ ] State mutations only via typed node returns.
- [ ] Every factual output path runs through the Verifier.
- [ ] LangSmith trace reviewed (link in PR description).
- [ ] **Retrieval-touching PRs run the SAMPLED eval harness and post the numbers in the PR description** — before/after, not just after. The full matrix runs on `main` post-merge.

---

## Post-v0.1 backlog (prioritized)

| # | Item | Why it matters | Why deferred |
|---|---|---|---|
| 1 | **Incremental indexing** | Re-indexing on every push is wasteful. SHA-diff-aware partial re-index would unlock daily-driver use. | Requires careful invalidation of graph edges; not on the v0.1 critical path. |
| 2 | **Comprehension quiz** | A 3-question quiz at the end of a Learn tour validates the user actually built the mental model. Big signal-of-success boost. | Quiz quality requires its own eval set; punt to v0.2. |
| 3 | **TypeScript support** | Doubles the addressable repo population. | Hard scope-fence in v1. tree-sitter-typescript + a TS call-graph extractor is a real chunk of work. |
| 4 | **HITL interrupts** | Pause-edit-resume during tour generation lets the user redirect ("skip the data layer, go to the API"). | Needs LangGraph interrupt UX; cleaner to add once the tour shape stabilizes. |
| 5 | **Repo "take the tour" badge** | A README badge maintainers add to invite contributors; viral loop. | Need a stable hosted URL & cached tour storage first. |
| 6 | **Self-host docs** | Lets others run the stack against private repos. | Docs are post-launch work; the code already runs locally. |
| 7 | **Semantic cache** | Cache by intent + question shape, not just exact prompt. Bigger quota savings, faster repeat queries. | Risk of stale results; needs eval guardrails before enabling. |
| 8 | **Verifier fine-tune** | A small specialized verifier (LoRA on qwen2.5-coder) would lift grounding accuracy 3–5 points. | Off-the-shelf works well enough for v0.1; fine-tune is iteration, not foundation. |
| 9 | **Starter-branch scaffolding** | After picking an opportunity, "scaffold a starter branch" runs a tiny Aider/Sweep-style edit producing a draft diff for the user to refine. Big leverage on the contribute promise. | The PR-quality bar is its own product. v0.1 hands off to GitHub at the "files to touch" step instead. |
| 10 | **Stuck-loop re-entry** | When a user picks an opportunity and gets stuck mid-work, a "I'm stuck" button re-enters Q&A with the opportunity preloaded as context. | Requires session continuity beyond a single tour run — clean to add once tours are persisted. |
| 11 | **Common-questions overlay per repo** | After we've toured N users through fastapi, surface "common questions on this repo" as a starting affordance. Compounds with usage. | Needs aggregated session data; meaningless until we have real users. |
| 12 | **Session persistence + shareable tour URLs** | Re-opening the app resumes the last tour; a shareable read-only URL lets a user send a tour to a teammate. Big leverage on the "trust" pitch — others can replay the exact tour. | Requires durable tour storage (Postgres tour table + serialized state), URL signing, and a stable retrieval shape. Clean to add once the tour event schema has stopped moving. |
| 13 | **Q&A multi-turn (`qa_history`)** | Lets users ask building, sequential questions ("how does middleware work?" → "how does my middleware get registered?"). Schema slot reserved in `ArchaeologistState.qa_history` from v1 so adding the UI is a small change later. | Wants a dedicated eval set for follow-up coherence; not blocking v0.1. |

The backlog is ordered by leverage, not by ease. We pick from the top after v0.1 ships and the first real users push back on what hurts most.
