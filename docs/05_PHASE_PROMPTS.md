# 05 — Phase Prompts (paste-ready)

One ready-to-paste prompt per phase. Paste the relevant prompt at the start of a fresh Claude Code session **after** you have read `docs/00_CLAUDE_BUILD_GUIDE.md`, `docs/03_ARCHITECTURE.md`, and `docs/04_BUILD_PLAN.md` (the prompts instruct you to do this anyway).

Each prompt is self-contained. They restate the exact quality gate as the Definition of Done, and they all end with the same stop-and-report instruction so you can review one phase at a time without auto-rolling into the next.

---

## Phase 0 prompt — Foundation

```
Read CLAUDE.md (project-wide conventions), docs/00_CLAUDE_BUILD_GUIDE.md (standing build context), docs/03_ARCHITECTURE.md (design keystone), and docs/04_BUILD_PLAN.md (phase gates) before writing code. The four layer in that order — CLAUDE.md governs the whole project; docs/00 carries phase-agnostic build rules; docs/03 is the architectural source of truth; docs/04 has the phase-specific quality gates. The prompt body below is the phase-specific overlay.

You are starting Phase 0 of Codebase Archaeologist. The goal of this phase is a monorepo that builds, tests, and lints cleanly, with a working LLMProvider (cache + backoff + Ollama fallback), CI green, and `docker compose up` bringing the stack up clean.

Deliverables
- Monorepo:
    apps/api/         (FastAPI scaffold; no endpoints yet)
    apps/web/         (Next.js 15 scaffold; default page only)
    packages/core/    (shared types, config, LLMProvider)
    packages/ingestion/ (empty package skeleton with __init__ and tests dir)
    packages/agents/  (empty package skeleton)
    packages/evals/   (empty package skeleton)
- Root `pyproject.toml` orchestrating the workspace via `uv` or `pdm`. One Python venv for all packages.
- `ruff`, `mypy --strict`, `pytest` + `pytest-asyncio` + `pytest-cov` configured per package.
- `.pre-commit-config.yaml` with: ruff, mypy (touched files), gitleaks, end-of-file-fixer, trailing-whitespace.
- `.github/workflows/ci.yml`: install → lint → typecheck → test → coverage gate (80%) → eval-runner stub job (no-op).
- `docker-compose.yml` for Postgres 16 with pgvector, Redis 7, Ollama. Named volumes. The Ollama service preloads `qwen2.5-coder:7b` and `nomic-embed-text` via an entrypoint script.
- `packages/core/llm/`:
    - `models.py`: `ModelId` enum mapping logical names ("intent_router", "cartographer", "flow_tracer", "teacher", "qa_primary", "qa_fallback", "code_health", "verifier", "embeddings") to physical models per docs/02_TECH_STACK.md.
    - `provider.py`: `LLMProvider` async class with `generate(model: ModelId, messages, **kwargs)`, SQLite cache keyed on sha256(model + canonical_json(messages) + kwargs), exponential backoff w/ jitter on 429 (max 5 attempts), provider fallback chain Groq → Cerebras → Ollama, per-model `tokens_used` counter.
    - The class is the only place agents talk to LLMs. Re-exports go through `packages/core/llm/__init__.py`.
- `packages/core/logging.py`: structlog setup, JSON renderer in prod, dev renderer in tests.
- `packages/core/settings.py`: pydantic-settings; `.env.example` checked in.

Tests to write FIRST (TDD)
1. `test_llm_cache_hit_avoids_api_call` — second identical call hits cache; the underlying client is called exactly once.
2. `test_llm_429_backoff_retries` — with the client raising 429 for N attempts and succeeding on attempt N+1, generate returns the response and the backoff sleeps are bounded.
3. `test_llm_forced_429_storm_falls_back_to_ollama` — Groq mocked to return 429 indefinitely; generate returns a real (mocked-Ollama) response within 30s. THIS TEST IS THE GATE — do not mock the fallback away.
4. `test_llm_token_counter_increments` — `tokens_used[model]` increases by the response's token count after each call.
5. `test_settings_loads_from_env_example` — `.env.example` is a valid settings source.

Implementation order
- Layout + tooling + pre-commit + CI first.
- Then `core/logging.py`, `core/settings.py`.
- Then `core/llm/models.py`, `core/llm/provider.py` strictly test-first.
- Last: docker-compose + Ollama entrypoint preload script.

Quality gate (Definition of Done — restate exactly)
- `make ci` passes locally and in GitHub Actions.
- Coverage ≥ 80% on `packages/core`.
- Forced-429 test: with Groq mocked to 429 indefinitely, `LLMProvider.generate(...)` returns a real response from Ollama within 30s.
- `docker compose up -d` brings the full stack up clean on a fresh checkout in ≤ 90 s.

Per-PR Definition of Done from docs/00 applies to every PR.

Do not start the next phase. Stop and report what was built, the test results (with the forced-429 test output included verbatim), the `docker compose up` timing, and any deviations from the spec.
```

---

## Phase 1 prompt — Ingestion

```
Read CLAUDE.md (project-wide conventions), docs/00_CLAUDE_BUILD_GUIDE.md (standing build context), docs/03_ARCHITECTURE.md (design keystone), and docs/04_BUILD_PLAN.md (phase gates) before writing code. The four layer in that order — CLAUDE.md governs the whole project; docs/00 carries phase-agnostic build rules; docs/03 is the architectural source of truth; docs/04 has the phase-specific quality gates. The prompt body below is the phase-specific overlay.

You are starting Phase 1 of Codebase Archaeologist. The goal: given a public GitHub URL, an arq worker clones the repo, parses with tree-sitter, chunks structurally, builds a NetworkX dependency graph, embeds chunks via Ollama nomic-embed-text, and persists everything to Postgres + pgvector. Idempotent on HEAD SHA. Indexing ≤ 90 s on httpx.

Deliverables
- `packages/ingestion/clone.py` — GitPython clone into tempdir; record HEAD SHA; cleanup on completion or failure.
- `packages/ingestion/parse.py` — tree-sitter + tree-sitter-python; produce typed `ParsedFile` per file with function/class spans (exact line ranges).
- `packages/ingestion/chunk.py` — structural chunker:
    - One chunk per function and per class.
    - Class chunks include signature + docstring + method names but NOT method bodies.
    - Method chunks are independent.
    - No chunk starts or ends mid-statement. Tested.
- `packages/ingestion/graph.py` — NetworkX builder with edge types:
    - `calls` (scope-aware AST walk; handle `self.method()`, aliased imports, `from x import y as z`)
    - `imports`
    - `inherits`
    Unresolved dynamic patterns log warnings; do NOT invent edges.
- `packages/ingestion/summary.py` — `llama-3.1-8b-instant` chunk summaries via the LLMProvider. Cached by `(head_sha, file_path, chunk_id)`. Bounded by asyncio.Semaphore tuned to Groq's per-minute rate.
- `packages/ingestion/embed.py` — Ollama nomic-embed-text, batched, async.
- `packages/ingestion/persist.py` — write to Postgres:
    - `chunks(id, repo_id, file_path, start_line, end_line, symbol, kind, summary, content)`
    - `chunk_embeddings(chunk_id, embedding vector(768))` with `ivfflat (embedding vector_cosine_ops) WITH (lists = 100)`
    - `graph_adjacency(repo_id, adjacency JSONB)`
    - `repos(id, url, head_sha, status, indexed_at)`
- `apps/api/jobs/index_repo.py` — arq job orchestrating clone → parse → chunk → graph → summary → embed → persist.
- Idempotency: if `(repo_url, head_sha)` already indexed, exit with status `already_indexed`.
- Hard cap: reject repos > 200k LOC at the queue boundary.

Tests to write FIRST (TDD)
1. `test_chunks_on_ast_boundaries` — on a chosen Python file, every chunk's start_line is the start of a def/class statement; end_line is the line of the last statement of the block.
2. `test_chunk_content_matches_source` — 20 randomly sampled chunks satisfy `chunk.content == repo_file[start:end]` exactly.
3. `test_graph_known_call_chain_httpx` — after indexing httpx, `nx.has_path(graph, "httpx.Client.send", "httpx._transports.default.HTTPTransport.handle_request")` (or the equivalent symbol IDs you adopt).
4. `test_idempotent_reindex` — running the job twice on the same HEAD SHA: second invocation returns `already_indexed` without doing work.
5. `test_indexing_under_90s` — `httpx` (≈ 50 kLOC) indexes in ≤ 90 s on the developer machine with warm Ollama models. (Tag as slow; opt-in in CI.)

Implementation order
- Postgres migrations first (alembic or hand-rolled), then `persist.py`.
- Parse + chunk next; test boundary correctness on flask's `app.py`.
- Graph builder; test the httpx call chain.
- Summaries + embeddings (these depend on Phase 0's LLMProvider).
- arq job last; wires the pipeline.

Quality gate (Definition of Done — restate exactly)
- Indexing completes in ≤ 90 s on httpx with warm Ollama models.
- Line-span correctness: 20 random chunks pass content-equality.
- A known call chain exists as a graph path (the httpx chain above).
- Idempotent re-run exits immediately with `already_indexed`.

Per-PR Definition of Done from docs/00 applies.

Do not start the next phase. Stop and report what was built, test results, the indexing time on httpx, and any deviations.
```

---

## Phase 2 prompt — Hybrid Retrieval + Grounded Q&A (the spine)

```
Read CLAUDE.md (project-wide conventions), docs/00_CLAUDE_BUILD_GUIDE.md (standing build context), docs/03_ARCHITECTURE.md (design keystone), and docs/04_BUILD_PLAN.md (phase gates) before writing code. The four layer in that order — CLAUDE.md governs the whole project; docs/00 carries phase-agnostic build rules; docs/03 is the architectural source of truth; docs/04 has the phase-specific quality gates. The prompt body below is the phase-specific overlay.

You are starting Phase 2 of Codebase Archaeologist. THIS IS THE SPINE OF THE PRODUCT. The goal: working hybrid retrieval (vector → graph) with a sufficiency judge and a Verifier grounding loop. LangSmith tracing on every run. Eval harness v1 in CI. Grounding accuracy ≥ 90% on httpx.

Deliverables
- Tools (deterministic, typed, LLM-free) in `packages/agents/tools/`:
    - `vector_search.py` — pgvector k-NN with cosine distance; returns `list[ChunkHit]` (chunk + file:line span + distance).
    - `graph_traverse.py` — BFS over the JSONB adjacency; returns `list[Path]` where each path is `list[CodeRef]`. Configurable edge_types and max_depth.
    - `graph_query.py` — `kind ∈ {entry_points, hubs, layers, callers, callees}` over NetworkX (rebuilt from adjacency JSONB at query time, cached per-repo).
    - `graph_metrics.py` — per-symbol pack: fan-in, fan-out, cyclomatic complexity (radon), churn (GitPython), has_tests bit.
    - `read_chunks.py` — read content by CodeRef. THE ONLY tool that returns source text.
    - `github_issues.py` — PyGithub with response caching.
- Q&A LangGraph mini-graph in `packages/agents/qa/graph.py`:
    - Nodes: `vector_search → graph_traverse → judge_sufficiency → (expand | answer) → verifier`.
    - Hop budget hard-counter: max 3 iterations of (search ↔ traverse ↔ judge) before forced answer.
    - The sufficiency judge is the SAME Q&A model (70B), called with its accumulated context.
- Verifier in `packages/agents/verifier/grounding.py`:
    - For each Claim, call `read_chunks(claim.refs)`, prompt `qwen2.5-coder:7b` with the structured rubric: "Is this claim FULLY supported by these chunks? JSON: {decision: 'supported'|'rejected', reason: string}".
    - Failure to parse the JSON = treat as rejection.
    - Rejection → append `VerifierObjection` to state.
- LangSmith integration: `@traceable` on every node and tool. Project name from env. Run names include `repo_id` and question.
- `packages/evals/datasets/httpx_qa_v1.jsonl` — 15 hand-written Q&A pairs, each with `question`, `expected_refs[]`, `expected_answer_keywords[]`. Include 3 multi-hop questions that REQUIRE graph traversal beyond vector hits, and 3 not-in-repo questions for the hallucination test.
- `packages/evals/runners/grounding.py` — runs Q&A over a dataset; computes grounding accuracy, retrieval recall@k, hallucination rate. Emits a JSON report.
- `.github/workflows/eval.yml` — runs the eval harness on retrieval-touching PRs; comments numbers on the PR.

Tests to write FIRST (TDD)
1. `test_vector_search_returns_chunks_with_spans` — basic recall check on a tiny fixture corpus.
2. `test_graph_traverse_bfs_correctness` — known graph, known paths.
3. `test_qa_hop_budget_enforced` — when the sufficiency judge keeps returning "insufficient", the loop terminates after 3 hops with a forced answer.
4. `test_verifier_rejects_unsupported_claim` — synthesize a claim whose refs don't actually contain the asserted fact; verifier rejects.
5. `test_forced_hallucination_returns_not_found` — a question about a non-existent module returns an honest "I couldn't find that" answer, no invention.
6. Eval runner integration test — runs `httpx_qa_v1` end-to-end and asserts ≥ 90% grounding accuracy.

Implementation order
- Tools first, each with its own unit tests (deterministic — easy to test).
- Verifier next; it depends only on tools.
- Q&A graph last; it composes everything.
- Eval harness in parallel once the Q&A graph runs end-to-end on one question.

Quality gate (Definition of Done — restate exactly)
- Grounding accuracy ≥ 90% on `httpx_qa_v1`.
- Multi-hop chain test: 3 multi-hop questions; answers reference chunks reached via `graph_traverse`, not vector hits alone.
- Forced-hallucination test: 3 not-in-repo questions produce honest "not found" answers.
- Zero quota exhaustion during a full eval run.
- LangSmith traces for every eval entry are visible with the full tool-call sequence.

Per-PR Definition of Done from docs/00 applies, including: "retrieval-touching PRs run the eval harness and post numbers in the PR description (before/after)."

Do not start the next phase. Stop and report what was built, test results, the full eval report JSON, and the LangSmith project URL.
```

---

## Phase 3 prompt — Orchestration + Learn subgraph

```
Read CLAUDE.md (project-wide conventions), docs/00_CLAUDE_BUILD_GUIDE.md (standing build context), docs/03_ARCHITECTURE.md (design keystone), and docs/04_BUILD_PLAN.md (phase gates) before writing code. The four layer in that order — CLAUDE.md governs the whole project; docs/00 carries phase-agnostic build rules; docs/03 is the architectural source of truth; docs/04 has the phase-specific quality gates. The prompt body below is the phase-specific overlay.

You are starting Phase 3 of Codebase Archaeologist. The goal: full `ArchaeologistState` (with `IntentProfile` + `CapabilityPlan`), working **generic intent layer** (Intent Profiler → Capability Planner), composable capability library (Cartographer, Flow Tracer, Teacher), Verifier loop with Iteration-2 actionability rubric integrated, Postgres checkpointing with kill-resume working. **No hardcoded purpose enum anywhere.**

Deliverables
- `packages/agents/state.py` — `ArchaeologistState`, `Claim`, `Insight`, `CodeRef`, `Opportunity`, `TourSection`, `VerifierObjection` EXACTLY as specified in docs/03_ARCHITECTURE.md. Use Pydantic v2. Use `Annotated[..., add]` reducers on every append-only list. Validators must fail on:
    - `Claim.refs` empty
    - `Insight.so_what` empty
    - `Insight.goal_link` empty
- `packages/agents/intent/profiler.py` — **Intent Profiler (generic intent layer, step 1)** using `llama-3.1-8b-instant`. Takes the user's free-text intent. Emits a draft `IntentProfile` (modality_weights ∈ [0,1] sparse over understand/change/evaluate/locate/compare, focus_keywords, audience_framing, output_shape_preference, success_criterion, raw_text preserved verbatim). Returns the draft to the UI for user confirmation; the confirmed profile is what lands in state. Prompt fits ≤ 2000 input tokens.
- `packages/agents/intent/planner.py` — **Capability Planner (generic intent layer, step 2)**. Pure Python function `plan(IntentProfile) -> CapabilityPlan`. Rules over `modality_weights` and `raw_text` keyword signals. Outputs `active` (list of CapabilityName), `tilts` (per-capability), `output_shape`, and typed knobs (cartographer_tilt, flow_tracer_targets, lane_b_framing, ranker_weights). No LLM. Falls through to a sensible default (`["cartographer", "teacher"]`, `output_shape="narrative"`) if no rules match.
- `packages/agents/prompts/goal_anchor.py` — single helper that renders the "goal anchor" block from `intent_profile` + the planner-derived tilts. EVERY downstream generation prompt template begins with this block (Cartographer, Flow Tracer, Teacher, all three scanners, Decision Archaeology, Q&A). Snapshot test pins the rendered output.
- `packages/agents/learn/cartographer.py` — uses `graph_query` (entry_points, hubs, layers) → emits `system_map: list[Insight]`. **Tailors selection to `capability_plan.cartographer_tilt`** (`balanced` / `data_hubs` / `decision_hubs` / `hot_path`) and narrows by `intent_profile.focus_keywords`. Each Insight populates `finding/because/so_what/refs/goal_link`. The `goal_link` field must explicitly reference something in `intent_profile`.
- **Architectural rule**: no node anywhere in `packages/agents/` may write `if state.purpose == "..."`. Capability behavior is parameterized exclusively by `intent_profile` + `capability_plan.tilts[capability_name]`. A CI grep check enforces this.
- `packages/agents/learn/flow_tracer.py` — picks one or more flows aligned to `capability_plan.flow_tracer_targets` (planner-derived from `intent_profile.focus_keywords` + `raw_text` signals). Walks via `graph_traverse`. Emits `traced_flows: list[Insight]`.
- `packages/agents/learn/teacher.py` — sequences map+flow into `draft_tour: list[TourSection]`. Emits mermaid in `TourSection.mermaid`. Every section ends in a next action (file to open, command to run, step to take).
- `packages/agents/verifier/loop.py` — grounding check (from Phase 2) PLUS actionability rubric:
    - For each Claim: goal-relevant? (binary)
    - For each TourSection: ends in motion? (binary)
    - Failure → `VerifierObjection` appended; source node retries ≤ 2; after that, the claim renders as `flagged`.
- LangGraph wiring in `packages/agents/graph.py`:
    - `StateGraph[ArchaeologistState]` with Postgres checkpointer.
    - Conditional edges for verifier pass/fail/retry.
    - `recursion_limit=15`.
- Iteration-2 prompt contracts: every generation prompt restates the three laws (goal-anchored / numbers carry consequences / sections end in motion) with contrastive ❌/✅ examples. Snapshot tests pin the rendered prompts.
- `packages/evals/datasets/intent_profiling_v1.jsonl` — 50 free-text intents, per-row expected `IntentProfile` fields.
- `packages/evals/datasets/planner_correctness_v1.jsonl` — same 50 entries, expected `CapabilityPlan.active` subset and key tilts.
- `packages/evals/datasets/actionability_v1.jsonl` — 20 tour sections labeled `actionable` / `not_actionable` with rubric reasons.
- `packages/evals/runners/checkpoint_resume.py` — starts a tour, kills mid-flight, resumes from checkpoint, asserts identical final state (modulo timestamps).

Tests to write FIRST (TDD)
1. `test_insight_so_what_required` — `Insight(..., so_what="")` raises ValidationError.
2. `test_claim_refs_required` — `Claim(..., refs=[])` raises ValidationError.
3. `test_intent_profiler_per_field_accuracy` — ≥ 90% per field (modality_weights, focus_keywords, audience_framing, output_shape_preference) on `intent_profiling_v1`.
3a. `test_planner_correctness` — ≥ 90% F1 on capability-subset selection from `planner_correctness_v1`.
3b. `test_cartographer_rejects_missing_intent_profile` — invoking the Cartographer with `intent_profile=None` or `capability_plan=None` raises a ValidationError. The generic intent layer is non-optional.
3c. `test_intent_shapes_output` — run the pipeline on flask with two materially different `IntentProfile`s ("explain request lifecycle" vs "audit auth surface for fragility"); assert resulting `draft_tour`s differ structurally by ≥ 50% on a sectional-overlap metric.
3d. `test_no_purpose_enum_in_code` — CI grep asserts `if state.purpose ==` does not appear under `packages/agents/`. Elasticity guarantee.
3e. `test_capability_library_independence` — each capability invocable standalone with a synthetic `IntentProfile + CapabilityPlan`, without any other capability running.
4. `test_prompt_token_budget` — every node's rendered prompt is ≤ 2000 input tokens (`tiktoken`).
4a. `test_goal_anchor_present_in_every_prompt` — render each generation prompt with sample state; assert the goal-anchor block (referencing `intent_profile.raw_text` + the relevant tilt fields) appears as the leading section in every one.
5. `test_verifier_retries_then_flags` — synthesize a section that fails actionability; verifier objects; source node retries twice; after that claim status == "flagged" (not silently dropped).
6. `test_checkpoint_resume` — start a tour, kill at any step, resume; final state matches a clean-run state.
7. `test_actionability_eval_threshold` — ≥ 80% on `actionability_v1`.
8. Snapshot test on Cartographer / Flow Tracer / Teacher prompts (catch silent prompt drift).

Implementation order
- State models + validators first (these are the keystone; build with TDD).
- Intent Profiler + Capability Planner (the generic intent layer — small, isolated, evaluable on a labeled set).
- Verifier loop with actionability rubric (needs to be in place BEFORE Cartographer/Teacher so you don't build prompts that bypass it).
- Cartographer → Flow Tracer → Teacher.
- LangGraph wiring last; checkpoint test is the integration gate.

Quality gate (Definition of Done — restate exactly)
- Intent Profiler per-field accuracy ≥ 90% on `intent_profiling_v1`.
- Capability Planner F1 ≥ 90% on `planner_correctness_v1`.
- Capability library independence test passes (each capability invocable standalone).
- Intent-shapes-output test passes (≥ 50% structural delta between two materially different `IntentProfile`s on flask).
- No-purpose-enum-in-code grep check passes (CI greps `if state.purpose ==` under `packages/agents/`, must be zero hits).
- Goal-anchor-present test passes on every generation prompt.
- Full tour on flask for an "understand request lifecycle" intent in < 4 minutes wall clock, every claim ref-linked, no `flagged` claims in the demo run.
- Checkpoint resume passes.
- Actionability ≥ 80% on `actionability_v1`.
- No node prompt exceeds 2000 input tokens.

Per-PR Definition of Done from docs/00 applies.

Do not start the next phase. Stop and report what was built, all eval numbers, the flask tour total wall-clock time, and the LangSmith trace URL for the flask demo run.
```

---

## Phase 4 prompt — Experience (FastAPI + Next.js + synchronized code viewer)

```
Read CLAUDE.md (project-wide conventions), docs/00_CLAUDE_BUILD_GUIDE.md (standing build context), docs/03_ARCHITECTURE.md (design keystone), and docs/04_BUILD_PLAN.md (phase gates) before writing code. The four layer in that order — CLAUDE.md governs the whole project; docs/00 carries phase-agnostic build rules; docs/03 is the architectural source of truth; docs/04 has the phase-specific quality gates. The prompt body below is the phase-specific overlay.

You are starting Phase 4 of Codebase Archaeologist. The goal: a user pastes a GitHub URL into the browser and watches a tour stream in. The synchronized code viewer is the centerpiece demo moment. Cold-start `docker compose up` to working demo on flask.

Deliverables
- FastAPI endpoints in `apps/api/routes/`:
    - `POST /repos` — body `{repo_url}`; enqueues arq indexing; returns `{repo_id, status}`.
    - `GET /repos/{repo_id}/status` — returns `{status: queued|indexing|ready|error, progress?, error?}`.
    - `POST /tours` — body `{repo_id, intent_profile}` (confirmed profile from the elicitation step); returns `{tour_id}` and a `stream_url`.
    - `GET /tours/{tour_id}/stream` — SSE stream of tour events (sse-starlette).
    - `POST /tours/{tour_id}/ask` — body `{question}`; ask-anything escape hatch; returns answer + refs.
    - `GET /chunks/{chunk_id}` — authenticated chunk fetch for the code viewer (NOT the whole repo).
- SSE event protocol (versioned with `v: 1`):
    - `section_start { order, title }`
    - `token { text }`
    - `claim { id, text, refs, status, verifier_note?, retrieval_path? }` — retrieval_path is a short ordered list like `["vector_search:k=8", "graph_traverse:depth=2"]`; verifier_note is the one-liner shown on hover when status is verified or flagged.
    - `diagram { mermaid }`
    - `section_end { order }`
    - `first_impression { text }` — emitted during indexing once enough chunks exist (≥ 10s in). Powered by 8B, cached per (repo_id, head_sha).
    - `done`
    - `error { code, message }`
    - Heartbeat: SSE comment lines (`:`) every 15 s to keep proxies alive.
- Next.js 15 (App Router, RSC) in `apps/web/`:
    - URL input page → **immediately routes to pre-context capture; indexing runs in parallel in the background**. The user never stares at an indexing progress bar with nothing to do.
    - Pre-context capture (runs in parallel with indexing):
        - Step 1: "Why are you here?" — two large cards: "I want to learn this codebase" / "I want to contribute to it". (No Q&A entry — that's available as the always-on ask box.)
        - Step 2 (conditional on step 1):
            - LEARN → "What part interests you most?" — three options: overall structure / a specific feature / the data model. If "specific feature", free-text input.
            - CONTRIBUTE → "What kind of contribution?" — four options: fix a reported issue / improve code quality / hunt for likely problems / show all, ranked.
        - "First impression" panel below the elicitation: subscribes to `GET /repos/{repo_id}/first-impression` (SSE). At ≥ 10s of indexing, an 8B-generated paragraph streams in (language mix, primary entry point, top hubs, last-commit recency).
        - On submit, POST `/tours` with `{repo_id, intent_profile}` (the confirmed profile) and route to the tour view.
        - Persisted in Zustand; displayed as a compact "You said: LEARN · data model" chip at the top of the tour with a one-click "change" link that re-runs the elicitation (no re-indexing).
    - Tour view: streamed text panel (left) + synchronized shiki code viewer (right). If indexing isn't complete when the user lands here, a slim progress bar shows at the top and tour generation starts as soon as `status == ready`.
    - **Verified-badge UI**: every claim with `status == "verified"` renders with a small `✓ grounded` badge; hover shows `verifier_note` and the chunk content. Claims with `status == "flagged"` render with a distinct warning treatment.
    - **Retrieval-path chip**: every claim and every Q&A answer shows `retrieval_path` (e.g., `vector_search → graph_traverse · 2 hops`) on hover.
    - **Q&A drives the code viewer**: when a Q&A answer arrives, the first ref of its first claim auto-opens in the shiki viewer. Same `claim` event handler as the tour.
    - Clicking a claim → code viewer scrolls to + highlights `claim.refs` (exact line ranges).
    - Mermaid renderer for `diagram` events.
    - "Ask anything" input at the bottom of the tour view.
    - Zustand store: sections, claims by id, selected claim, code viewer file/range.
- Generated TypeScript client from FastAPI's OpenAPI; checked in under `apps/web/lib/api/`.
- Accessibility:
    - Keyboard navigation (Tab cycles claims; Enter selects).
    - ARIA labels on streamed regions (`aria-live="polite"`).
    - Focus management on newly streamed sections.

Tests to write FIRST (TDD)
1. API contract tests for each endpoint (pytest + httpx + ASGI test client).
2. SSE event-shape tests — every event type round-trips through the parser correctly.
3. Frontend unit tests (vitest) for the Zustand store: claim selection → code-viewer state.
4. Playwright e2e test: paste flask URL → wait for `ready` → start tour → click 5 claims → assert code viewer highlights the correct lines for each.
5. SSE 5-minute idle test — connection survives via heartbeats.
6. Lighthouse accessibility audit script in CI; fails on < 90.

Implementation order
- API endpoints + SSE event shape first; they are the contract.
- Generate the TS client; build the static URL-input page against it.
- Indexing progress page.
- Tour view: text stream first, then shiki viewer, then the click-to-highlight link.
- Mermaid renderer and ask-anything last.
- Playwright e2e is the integration gate.

Quality gate (Definition of Done — restate exactly)
- Cold-start demo: `docker compose up` → browser → paste `https://github.com/pallets/flask` → tour streams in. Works on a fresh checkout.
- Time-to-first-useful-output ≤ 12s (Playwright): from URL paste to elicitation rendered + first-impression streaming, or first tour claim.
- Click-to-highlight works for 10 randomly chosen claims in the demo tour (Playwright + manual).
- Verified-badge visible on ≥ 90% of demo-tour claims; verifier hover content present and accurate.
- Retrieval-path chip present on every claim and every Q&A answer; matches the actual traversal path (cross-checked via LangSmith).
- Q&A drives the code viewer: 5 sample questions auto-open the correct file (Playwright).
- Lighthouse accessibility ≥ 90 on the tour page.
- SSE survives a 5-minute tour without disconnects.

Per-PR Definition of Done from docs/00 applies.

Do not start the next phase. Stop and report what was built, e2e test output, Lighthouse score, and a screen recording or screenshots of the click-to-highlight working.
```

---

## Phase 5 prompt — Contribute mode (Iteration 1)

```
Read CLAUDE.md (project-wide conventions), docs/00_CLAUDE_BUILD_GUIDE.md (standing build context), docs/03_ARCHITECTURE.md (design keystone), and docs/04_BUILD_PLAN.md (phase gates) before writing code. The four layer in that order — CLAUDE.md governs the whole project; docs/00 carries phase-agnostic build rules; docs/03 is the architectural source of truth; docs/04 has the phase-specific quality gates. The prompt body below is the phase-specific overlay.

You are starting Phase 5 of Codebase Archaeologist. The goal: when the Capability Planner activates Lane A / Lane B / Lane C (based on the user's `IntentProfile` from Phase 3), the system produces a ranked Opportunity List briefed by the Teacher. Lane C uses guarded language and always ends in `confirm_before_pr`. **There is no hardcoded "contribute mode" branch** — lane activation is purely a function of the IntentProfile + the Planner's rules from Phase 3.

Deliverables
- **No new Elicitation node.** When the Planner activates one or more lanes but the IntentProfile underspecifies the contribution shape (e.g., `modality_weights.change` is high but no signal as to fix-issue vs. quality vs. hunt), the Teacher briefing prompt itself injects one targeted question. The answer updates `intent_profile.modality_weights` and triggers a one-shot Planner re-plan. Re-planning is cheap (deterministic, no LLM).
- `packages/agents/contribute/lane_a_triage.py`:
    - Fetch open issues via `github_issues`.
    - Extract referenced files/symbols (regex + light NER).
    - `graph_metrics` on each referenced symbol → approachability score combining fan-in/isolation/has_tests.
    - 70B model writes the Opportunity record. Inputs CAPPED to top-N candidates so the LLM doesn't process the whole issue tracker.
- `packages/agents/contribute/lane_b_quality.py`:
    - Deterministic detectors:
        - Untested hot code (fan-in ≥ p90 ∧ no test reference)
        - Missing docstrings on public API (in `__all__` or module-top-level)
        - Dead code (in-degree 0 ∧ not an entry point)
        - AST duplication (tree-sitter normalized hash collision)
        - Churn × complexity (top decile)
        - TODO/FIXME archaeology (`git blame`, age > 1 year)
    - 8B model RANKS and EXPLAINS only — no detection by LLM.
- `packages/agents/contribute/lane_c_suspicion.py`:
    - Pre-filter structural patterns DETERMINISTICALLY (mutable defaults, swallow-except, race-shaped patterns, complex-no-error-handling, etc.).
    - Cap at top-N before any LLM sees it.
    - qwen3-32b with guarded-language prompt; banned vocabulary { "bug", "broken", "will crash", "obviously wrong" }; required vocabulary includes a `to_confirm:` step.
- `packages/agents/contribute/ranker.py` — fully deterministic combined ranking (no LLM). Weighted combination of mergeability, approachability, evidence-strength. **Lane weights come from `capability_plan.ranker_weights`** — the Planner derived them from `intent_profile.modality_weights` + `raw_text` signals. The Planner's rationale (e.g., "weighted toward problem-hunting because the user said 'show me fragility'") is surfaced as a one-sentence chip in the UI so the "why these" question is always answered.
- All three scanner lanes' prompts MUST start with the shared `goal_anchor.py` block from Phase 3 (which renders `intent_profile.raw_text` + the planner-derived tilts). Snapshot test pins each lane's rendered prompt.
- `packages/agents/contribute/briefing.py` — Teacher (70B) takes ranked top-N → briefing per opportunity → `draft_tour`. Each briefing entry carries an **intent-match tag** derived from `intent_profile` (e.g., quoting the part of `raw_text` that triggered Lane C activation) so the UI can render the chip without re-deriving it. The Opportunity List header surfaces the Planner's `ranker_weights` rationale in one sentence so "why these" is always answered.
- **Lane A considered-and-rejected trail**: Lane A persists the next-3 ranked-down issues with a one-line graph-backed reason ("touches a hub of fan-in 47", "no test files reference the affected module"). Exposed in `Opportunity` payload as `considered_and_rejected: list[RejectedItem]`.
- **Per-opportunity CTAs (frontend)**: each Opportunity card renders two buttons — "Open files on GitHub" (deep links to each `files_to_touch` at the right line) and "Copy first step" (clipboard copy of `suggested_first_step`). No contribute briefing ships ending in prose alone.
- Verifier rubric extensions for Lane C:
    - Regex denylist check on Lane C output (banned vocabulary triggers rejection).
    - `Opportunity.confirm_before_pr` required when `lane == "C_suspicion"`; Pydantic raises if absent.
- Eval datasets:
    - `packages/evals/datasets/opportunity_quality_v1.jsonl` — hand-labeled top-N opportunities per eval repo: `is_approachable`, `is_legit`.
    - `packages/evals/datasets/file_mapping_v1.jsonl` — 20 opportunities with correct `files_to_touch`.
- LangGraph wiring: Lane A/B/C run in parallel via concurrent edges; Ranker is a synchronization point.

Tests to write FIRST (TDD)
1. `test_opportunity_lane_c_requires_confirm` — `Opportunity(lane="C_suspicion", confirm_before_pr=None, ...)` raises.
2. `test_lane_c_banned_vocabulary_rejected` — synthesize a Lane C output containing "bug"; verifier rejects.
3. `test_lane_a_approachability_uses_graph_not_labels` — issue with `good first issue` label but on a hub function ranks LOWER than an unlabeled issue on an isolated function.
4. `test_lane_b_dead_code_excludes_entry_points` — entry point with in-degree 0 not flagged.
5. `test_ranker_deterministic` — identical inputs → identical ordering.
5a. `test_ranker_respects_planner_weights` — same scanner outputs but `capability_plan.ranker_weights = {A:0.7,B:0.2,C:0.1}` vs `{A:0.1,B:0.2,C:0.7}` produces materially different top-N orderings.
5b. `test_planner_activates_correct_lanes` — IntentProfile parsed from "find me a first PR" activates Lane A heavy; IntentProfile from "show me fragility" activates Lane C heavy. No hardcoded purpose enum involved.
5c. `test_goal_anchor_in_lane_prompts` — each lane's rendered prompt starts with the shared goal-anchor block referencing `intent_profile.raw_text` and the relevant tilt.
6. `test_file_mapping_eval_threshold` — ≥ 80% overlap on `file_mapping_v1`.
7. `test_top3_issue_approachability_manual_review` — runs on the 3 eval repos and emits a report; the gate is "honest manual review ≥ 70%" — the test produces the artifact the human reviews.

Implementation order
- Opportunity model validator first (Lane C confirm-required rule).
- Lane B (deterministic detectors) — easiest to test in isolation.
- Lane A (needs PyGithub + graph metrics).
- Lane C (the guarded-language work — write the prompt with ❌/✅ examples, then the verifier denylist check).
- Ranker.
- Briefing Teacher.
- LangGraph parallel wiring last.

Quality gate (Definition of Done — restate exactly)
- Top-3 issue approachability ≥ 70% across 9 items on 3 eval repos (honest manual review of the test-emitted report).
- File-mapping eval ≥ 80% on `file_mapping_v1`.
- Suspicion legitimacy ≥ 75% on `opportunity_quality_v1` Lane C entries.
- Zero unverified claims shipped as fact in generated Contribute briefings on demo repos.
- Banned-vocabulary regex test passes on 20 randomly sampled Lane C generations.
- Intent-match chip visible on every Opportunity card; chip text quotes the relevant fragment of `intent_profile.raw_text` (no enum-shaped labels).
- Considered-and-rejected trail shows 3 entries per repo per demo run; each entry has a graph-backed one-line reason.
- CTA buttons present and functional on every Opportunity card (Playwright: deep-link URL correct; clipboard copy matches `suggested_first_step`).

Per-PR Definition of Done from docs/00 applies.

Do not start the next phase. Stop and report what was built, all eval numbers, and a sample top-5 Opportunity List for each of fastapi / httpx / flask.
```

---

## Phase 6 prompt — Harden and ship

```
Read CLAUDE.md (project-wide conventions), docs/00_CLAUDE_BUILD_GUIDE.md (standing build context), docs/03_ARCHITECTURE.md (design keystone), and docs/04_BUILD_PLAN.md (phase gates) before writing code. The four layer in that order — CLAUDE.md governs the whole project; docs/00 carries phase-agnostic build rules; docs/03 is the architectural source of truth; docs/04 has the phase-specific quality gates. The prompt body below is the phase-specific overlay.

You are starting Phase 6 of Codebase Archaeologist. The goal: full eval matrix in CI, security pass, README with demo GIF + eval table + honest limitations, one-command quickstart verified clean on a fresh VM, tag v0.1.0.

Deliverables
- CI matrix: run the full Phase 2/3/5 eval suites against `fastapi`, `httpx`, `flask`. Numbers persisted as build artifacts and surfaced as a status badge.
- Security:
    - structlog processor that strips chunk content from any log payload. Tested: a log call passing source code does not leak it.
    - `gitleaks` in CI.
    - `pip-audit` + `npm audit` in CI; fail on high-severity.
    - CORS locked to known origins (env-configurable).
    - FastAPI rate limit per `repo_id` (slowapi or middleware).
- README:
    - One-paragraph pitch.
    - Animated GIF of the cold-start flask demo, including click-to-highlight.
    - Quickstart: `docker compose up` + first repo URL to try.
    - Eval table (per repo: grounding accuracy, actionability rate, intent routing accuracy, opportunity quality numbers).
    - HONEST limitations section: Python only; public repos only; 200kLOC cap; known failure modes (dynamic dispatch, decorator-rewritten signatures, `getattr` polymorphism); free-tier quotas mean ~1k full tours/day max.
    - License + contributing notes.
- `make quickstart` script verified on a clean macOS VM and a clean Ubuntu 22.04 VM.
- Tag `v0.1.0` (do NOT push the tag without user approval).

Tests to write FIRST (TDD)
1. `test_logs_do_not_contain_chunk_content` — structlog processor strips a known chunk content marker from a payload.
2. `test_cors_locked_to_env_origins` — request from unlisted origin is rejected.
3. `test_rate_limit_per_repo` — N+1th request within window returns 429.
4. CI dry-run on the full eval matrix; assertions on min-thresholds per repo.
5. `test_quickstart_script_dry_run` — `make quickstart -n` runs without error and references all expected commands.

Implementation order
- Security hardening first (structlog processor, gitleaks, audits, CORS, rate limit).
- CI matrix wiring; produce the eval-numbers artifact.
- README last, using the eval-numbers artifact to populate the table.
- VM quickstart verification with documented commands and timing.
- Tag locally; await user approval before pushing.

Quality gate (Definition of Done — restate exactly)
- Full eval matrix green on all three eval repos with documented per-repo numbers.
- `gitleaks`, `pip-audit`, `npm audit` clean.
- Clean-VM quickstart finishes in ≤ 5 minutes from `git clone` to working browser demo.
- `v0.1.0` tagged locally; not pushed without explicit user approval.

Per-PR Definition of Done from docs/00 applies.

Stop and report what was built, the full eval matrix numbers (markdown table), the VM quickstart timings (macOS + Ubuntu), and ask the user to confirm before pushing the v0.1.0 tag.
```
