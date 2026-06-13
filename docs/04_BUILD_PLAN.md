# 04 — Build Plan

Seven phases (0–6). Each phase ends in a **working demo plus a hard quality gate with measurable numbers**. No phase ships if its gate fails. The plan is sized for a solo developer working 3–7 days per phase; expect Phase 1 (ingestion) and Phase 3 (orchestration) to anchor the long end of that range.

The structure of each phase below:

- **Goal** — what working code exists at the end.
- **Task checklist** — what to build, in order.
- **Production-grade specifics** — non-negotiable details the implementer must not paper over.
- **Quality gate** — measurable, binary numbers. Either pass and ship, or fail and iterate.

The `Per-PR Definition of Done` (at the end of this file) applies to every PR within every phase, not just the gate-passing PR.

---

## Phase 0 — Foundation

**Goal.** A monorepo that builds, tests, and lints cleanly. `LLMProvider` works against Groq with cache, backoff, and Ollama fallback. CI is green.

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
- [ ] `docker-compose.yml` for: Postgres 16 with `pgvector`, Redis 7, Ollama. Pulls `qwen2.5-coder:7b` and `nomic-embed-text` on first up.
- [ ] `packages/core/llm/provider.py` — `LLMProvider` class:
  - Async interface: `async def generate(model: ModelId, messages: list[Message], **kwargs) -> Response`
  - Backed by Groq SDK
  - SQLite cache keyed on `sha256(model + canonical_json(messages) + kwargs)`
  - Exponential backoff w/ jitter on 429 (max 5 attempts)
  - Provider fallback chain: Groq → Cerebras → Ollama (configurable per call)
  - Tracks `tokens_used` per model in a shared counter
- [ ] `packages/core/llm/models.py` — `ModelId` enum mapping logical names ("intent_router", "cartographer", "verifier") to physical model strings. Agents only ever reference the logical name.
- [ ] Unit tests for `LLMProvider`:
  - Cache hit avoids the API call
  - 429 retries the right number of times
  - **Forced 429 storm falls back to Ollama and returns a response** (no test mocks the fallback away)
  - Token counter increments correctly

**Production-grade specifics**

- `mypy --strict` from day one. No `Any` outside narrow boundary functions, each of which is annotated `# type: ignore[no-any-return]  # boundary: external SDK` with the reason.
- Logging via `structlog` only. No `print()`. JSON renderer in production, dev renderer in tests.
- Settings via `pydantic-settings`. `.env.example` checked in; `.env` git-ignored. `gitleaks` runs in pre-commit.
- Docker Compose uses **named volumes** for postgres and ollama so pulls survive container restarts.
- The Ollama service in compose preloads `qwen2.5-coder:7b` and `nomic-embed-text` via an `entrypoint` script — not lazily on first call (Phase 1 will need them ready).

**Quality gate**

- [ ] `make ci` passes locally and in GitHub Actions.
- [ ] Coverage ≥ 80% on `packages/core`.
- [ ] **Forced-429 test**: with Groq mocked to return 429 indefinitely, `LLMProvider.generate(...)` returns a real response from Ollama within 30s.
- [ ] `docker compose up -d` brings the full stack up clean on a fresh checkout in ≤ 90 s.

---

## Phase 1 — Ingestion

**Goal.** Given a public GitHub URL, an arq worker clones, parses, chunks structurally, builds a NetworkX dependency graph, embeds chunks via Ollama nomic-embed-text, and persists everything to Postgres + pgvector. Idempotent on HEAD SHA.

**Task checklist**

- [ ] `packages/ingestion/clone.py` — clone via GitPython into a tempdir; record HEAD SHA.
- [ ] `packages/ingestion/parse.py` — tree-sitter + tree-sitter-python; produce a typed `ParsedFile` per file with function/class spans.
- [ ] `packages/ingestion/chunk.py` — structural chunker: one chunk per function and per class (with method index). Class chunks include the class signature + docstring + method *names* but not method bodies; method chunks are independent. Line spans preserved exactly.
- [ ] `packages/ingestion/graph.py` — NetworkX builder. Edges:
  - `calls`: function A calls function B (resolved via scope-aware AST walk)
  - `imports`: file X imports symbol Y
  - `inherits`: class C extends class D
- [ ] `packages/ingestion/summary.py` — `llama-3.1-8b-instant` chunk summaries via `LLMProvider`. Cached by `(SHA, file_path, chunk_id)`.
- [ ] `packages/ingestion/embed.py` — Ollama `nomic-embed-text` embedder. Batched.
- [ ] `packages/ingestion/persist.py` — write to Postgres:
  - `chunks` table: `id, repo_id, file_path, start_line, end_line, symbol, kind, summary, content`
  - `chunk_embeddings`: pgvector column, ivfflat index
  - `graph_adjacency`: JSONB sidecar (`{node: {calls: [], called_by: [], imports: [], ...}}`)
  - `repos`: `id, url, head_sha, status, indexed_at`
- [ ] `apps/api/jobs/index_repo.py` — arq job that runs the pipeline end-to-end.
- [ ] Idempotency: if `(repo_url, head_sha)` already indexed, no-op.

**Production-grade specifics**

- Chunking on **AST boundaries** is non-negotiable. A test asserts that no chunk starts or ends mid-statement on a chosen file.
- The graph builder resolves calls scope-aware (handle `self.method()`, aliased imports, `from x import y as z`). It is OK to be incomplete for dynamic patterns (decorators that rewrite signatures, `getattr`) — log unresolved calls as warnings, don't invent edges.
- `graph_adjacency` stored as JSONB so traversal queries don't need a graph DB.
- pgvector index: `ivfflat (embedding vector_cosine_ops) WITH (lists = 100)` — adjust if recall < 95% on the eval set.
- Concurrency in summary/embedding pipelines bounded by `asyncio.Semaphore` tuned to Groq's per-minute rate.
- Hard cap: any repo with > 200k LOC is rejected at the queue boundary in v1.

**Quality gate** — measured on `httpx` (≈ 50 kLOC):

- [ ] Indexing completes in ≤ 90 s on a developer laptop with warm Ollama models.
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
- [ ] `packages/agents/verifier/grounding.py` — for each `Claim`, fetch `read_chunks(claim.refs)`, ask qwen2.5-coder:7b: "Is this claim *fully supported by* these chunks? Yes/No + reason." Reject → objection appended.
- [ ] LangSmith setup: `LANGCHAIN_TRACING_V2=true`, project name from env.
- [ ] `packages/evals/datasets/httpx_qa_v1.jsonl` — 15 Q&A pairs over httpx. Each has `question`, `expected_refs[]`, `expected_answer_keywords[]`.
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

- [ ] **Grounding accuracy ≥ 90%** on `httpx_qa_v1`.
- [ ] **Multi-hop chain test**: pick 3 questions that require ≥ 2 hops; assert the answer references chunks reached via `graph_traverse`, not vector hits alone.
- [ ] **Forced-hallucination test**: 3 not-in-repo questions; all 3 produce an honest "not found" answer.
- [ ] **Zero quota exhaustion** during a full eval run.
- [ ] LangSmith traces visible for every eval entry, with the full tool-call sequence inspectable.

---

## Phase 3 — Orchestration + Learn subgraph

**Goal.** Full `ArchaeologistState`. Intent Router branches reliably. LEARN subgraph (Cartographer → Flow Tracer → Teacher) produces a tour. Verifier loop integrated, including the Iteration-2 actionability rubric. Postgres checkpoints survive kill/resume.

**Task checklist**

- [ ] `packages/agents/state.py` — `ArchaeologistState` exactly as specified in `03_ARCHITECTURE.md` (CodeRef, Claim, Insight, Opportunity, TourSection, VerifierObjection).
- [ ] `packages/agents/router/intent.py` — Intent Router node (pre-context layer 1). 8B model. Classify into `learn` / `contribute` / `question` and capture `purpose` only. (Focus_hint is NOT inferred here — the elicitation node captures it explicitly.)
- [ ] `packages/agents/learn/elicitation.py` — **Learn Elicitation node (pre-context layer 2).** 8B model. Asks: "Are you here for the overall structure, a specific feature, or the data model?" Captures `focus_hint` ∈ `{overall_structure, specific_feature, data_model}`. Graph blocks here until answered — no downstream node runs without pre-context.
- [ ] Pre-context injection helper in `packages/agents/prompts/goal_anchor.py`: renders the leading "goal anchor" block from `(purpose, focus_hint, contribution_intent)`. **Every** generation prompt template starts with this block. A snapshot test pins the rendered output.
- [ ] `packages/agents/learn/cartographer.py` — uses `graph_query` (entry_points, hubs, layers) → emits `Insight[]`. Reads `focus_hint` and tailors which hubs are privileged (`data_model` → schema/ORM/dataclass hubs; `specific_feature` → narrow to relevant layer; `overall_structure` → balanced). Each Insight has `finding/because/so_what/refs/goal_link`. Validators enforce non-empty `so_what` and `goal_link`, and the `goal_link` must cite the captured pre-context.
- [ ] `packages/agents/learn/flow_tracer.py` — picks ONE flow aligned to `focus_hint`. Walks via `graph_traverse`. Emits `Insight[]`.
- [ ] `packages/agents/learn/teacher.py` — sequences map+flow into `TourSection[]`, emits mermaid diagrams, every section ends in motion.
- [ ] `packages/agents/verifier/loop.py` — grounding check + actionability rubric. Source-node retry edge with budget 2.
- [ ] LangGraph wiring: `StateGraph[ArchaeologistState]` with conditional edges; Postgres checkpointer.
- [ ] `packages/evals/datasets/intent_routing_v1.jsonl` — 30 labeled utterances (purpose classification only).
- [ ] `packages/evals/datasets/focus_hint_capture_v1.jsonl` — 15 simulated user answers to the Learn elicitation question, labeled with the expected `focus_hint`.
- [ ] `packages/evals/datasets/actionability_v1.jsonl` — 20 tour sections labeled `actionable` / `not_actionable` with rubric reasons.
- [ ] `packages/evals/runners/checkpoint_resume.py` — start a tour, kill the process mid-flight, resume from checkpoint, assert the same final state (modulo timestamps).

**Production-grade specifics**

- **Each agent's prompt fits in ≤ 2000 input tokens.** Enforced by a test that loads each prompt template and asserts `tiktoken` count.
- The Insight model validators do real work. A test asserts that constructing `Insight(finding="x", because="y", so_what="", refs=[...], goal_link="z")` raises.
- The Iteration-2 prompt contracts include ❌/✅ contrastive examples. A test snapshots the rendered prompts so a refactor that weakens them is caught in code review.
- The Verifier returns structured JSON (Pydantic schema), not free text. Failing to parse = treat as rejection.
- `recursion_limit=15` set on the compiled graph.

**Quality gate**

- [ ] **Intent Router ≥ 95%** on `intent_routing_v1`.
- [ ] **Focus-hint capture ≥ 95%** on `focus_hint_capture_v1`.
- [ ] **Pre-context shapes the output** — verify that running the Learn tour with `focus_hint=data_model` vs `focus_hint=overall_structure` on the same repo produces materially different system maps (≥ 50% delta in privileged hubs). Automated test on flask.
- [ ] **Full Learn tour on `flask` repo in < 4 minutes** wall clock, with every factual claim ref-linked (no `flagged` claims in the demo run).
- [ ] **Checkpoint resume passes** on the runner test (kill at any point in the graph; resume produces identical final state).
- [ ] **Actionability ≥ 80%** on `actionability_v1`.
- [ ] **No node prompt exceeds 2000 input tokens.**
- [ ] LangSmith trace for the demo run reviewed and linked in the PR.

---

## Phase 4 — Experience

**Goal.** A user pastes a URL and watches a tour stream in. The synchronized code viewer is the centerpiece. `docker compose up` on a fresh checkout gets the full demo running.

**Task checklist**

- [ ] FastAPI endpoints:
  - `POST /repos` — enqueue indexing; returns `repo_id`.
  - `GET /repos/{repo_id}/status` — `queued | indexing | ready | error`.
  - `POST /tours` — start a tour given `repo_id`, optional `purpose` hint.
  - `GET /tours/{tour_id}/stream` — SSE stream of tour events.
  - `POST /tours/{tour_id}/ask` — Q&A escape hatch.
- [ ] SSE event protocol (versioned):
  - `section_start { order, title }`
  - `token { text }`
  - `claim { id, text, refs[], status, verifier_note?, retrieval_path? }` — `retrieval_path` is a short list like `["vector_search:k=8", "graph_traverse:depth=2"]`; `verifier_note` is the one-liner shown on hover when status is `verified` or `flagged`.
  - `diagram { mermaid }`
  - `section_end { order }`
  - `first_impression { text }` — emitted during indexing once enough chunks exist (≥ 10s in). Powered by 8B; cached per `(repo_id, head_sha)`.
  - `done`
  - `error { code, message }`
- [ ] Next.js 15 app:
  - URL input → enqueues indexing AND immediately shows the pre-context capture flow (no waiting on indexing).
  - **Pre-context capture (runs in parallel with indexing)**: step 1 — "Why are you here?" (Learn / Contribute). Step 2 — branch-specific follow-up (focus_hint or contribution_intent). The captured values are persisted to the tour POST payload and surfaced as a small "You said:" chip at the top of the tour, with a one-click "change" affordance.
  - **"First impression" panel** below the elicitation: at the 10-second mark of indexing, an 8B-generated paragraph (language mix, top entry point, top hubs, last-commit recency) streams in. Makes the wait productive; demonstrates the system is alive.
  - When the user submits the elicitation, the tour view loads. If indexing is still running, a slim progress bar shows at the top and tour generation starts as soon as `status == ready`.
  - Streamed tour panel (left) using SSE.
  - Synchronized code viewer (right) using shiki — clicking a claim scrolls to and highlights the exact lines.
  - **Verified-badge UI**: every claim with `status == "verified"` renders with a small `✓ grounded` badge. Hover reveals the verifier's one-line confirmation and the chunk it grounded against. Claims with `status == "flagged"` render with a warning treatment.
  - **Retrieval-path chip**: every claim displays its retrieval chain (e.g., `vector_search → graph_traverse · 2 hops`) on hover. The SSE `claim` event carries the path; the frontend renders it.
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

- [ ] **Cold-start demo**: `docker compose up` → open browser → paste `https://github.com/pallets/flask` → see a tour stream in. Full end-to-end on a fresh checkout.
- [ ] **Time-to-first-useful-output ≤ 12s**: from URL paste to either (a) elicitation rendered + first-impression paragraph streaming, or (b) the first tour claim. Measured via Playwright.
- [ ] **Click a claim → exact-line highlight** works for 10 randomly-chosen claims in the demo tour (manual check + Playwright).
- [ ] **Verified-badge visible** on ≥ 90% of demo-tour claims (the rest may legitimately be flagged); verifier hover content present and accurate.
- [ ] **Retrieval-path chip** present on every claim and Q&A answer; content matches what the Q&A subgraph actually traversed (cross-checked via LangSmith trace).
- [ ] **Q&A drives the code viewer**: 5 sample Q&A questions auto-open the correct file in the viewer (Playwright).
- [ ] **Lighthouse accessibility ≥ 90** on the tour page.
- [ ] **SSE survives a 5-minute tour** without disconnects (load test).

---

## Phase 5 — Contribute mode (Iteration 1)

**Goal.** Switching purpose to "contribute" produces a ranked Opportunity List from Lane A/B/C, briefed by the Teacher. Every Lane C suspicion uses guarded language and ends in `confirm_before_pr`.

**Task checklist**

- [ ] `packages/agents/contribute/elicitation.py` — asks the four-way intent question; populates `contribution_intent`.
- [ ] `packages/agents/contribute/lane_a_triage.py` — fetch issues → graph-backed approachability scoring → 70B explanation → `Opportunity[]`.
- [ ] `packages/agents/contribute/lane_b_quality.py` — deterministic detectors (untested hot code / missing docstrings / dead code / AST dup / churn × complexity / TODO archaeology) → 8B ranking → `Opportunity[]`.
- [ ] `packages/agents/contribute/lane_c_suspicion.py` — pre-filter structural patterns → top-N → qwen3-32b with guarded-language prompt → `Opportunity[]`. Verifier post-checks for banned vocabulary and presence of `to_confirm`.
- [ ] `packages/agents/contribute/ranker.py` — deterministic ranking: weighted combination of mergeability + approachability + evidence-strength. **Lane weights are gated by `contribution_intent`**: `fix_issue` → Lane A heaviest; `improve_quality` → Lane B; `hunt_problems` → Lane C; `show_all` → balanced. The active intent is shown to the user inline in the Opportunity List header so the "why these" question is always answered.
- [ ] `packages/agents/contribute/briefing.py` — Teacher briefing per opportunity: explain why, files to touch, suggested first step, nearest tests. Every briefing entry carries an **intent-match tag** echoing the captured `contribution_intent` so the user always sees "matches: hunt problems" on the card.
- [ ] **Lane A considered-and-rejected trail**: Lane A persists not only its top-N accepted opportunities but the next-3 ranked-down items with a one-line reason ("touches a hub of fan-in 47", "no test files reference the affected module"). The Opportunity List UI shows these below the accepted list under a collapsed "considered and rejected" disclosure. This is a deliberate transparency surface — the user sees the triage, not just the verdict.
- [ ] **Per-opportunity CTAs (frontend)**: each Opportunity card renders two buttons — "Open files on GitHub" (deep links to each `files_to_touch` at the right line) and "Copy first step" (clipboard copy of `suggested_first_step`). The contribute briefing never ends in prose alone.
- [ ] `packages/evals/datasets/opportunity_quality_v1.jsonl` — hand-labeled top-N opportunities per eval repo: `is_approachable` (bool), `is_legit` (bool, for Lane C).
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
- [ ] **Intent-match chip visible** on every Opportunity card; chip text matches the captured `contribution_intent`.
- [ ] **Considered-and-rejected trail** shows 3 entries per repo on each demo run; each entry has a graph-backed one-line reason.
- [ ] **CTA buttons present and functional** on every Opportunity card (Playwright: click "Open files on GitHub" → correct deep-link URL; click "Copy first step" → clipboard contains `suggested_first_step`).

---

## Phase 6 — Harden and ship

**Goal.** Full eval matrix in CI. Security pass. README with demo GIF, eval table, honest limitations. One-command quickstart verified clean. Tag `v0.1.0`.

**Task checklist**

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

- [ ] `ruff` clean.
- [ ] `mypy --strict` clean on touched packages.
- [ ] Tests written; coverage did not decrease vs. main.
- [ ] No secrets, no `print()`, no `console.log` — `structlog` only.
- [ ] Docstrings on all public functions and classes.
- [ ] State mutations only via typed node returns.
- [ ] Every factual output path runs through the Verifier.
- [ ] LangSmith trace reviewed (link in PR description).
- [ ] **Retrieval-touching PRs run the eval harness and post the numbers in the PR description** — before/after, not just after.

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

The backlog is ordered by leverage, not by ease. We pick from the top after v0.1 ships and the first real users push back on what hurts most.
