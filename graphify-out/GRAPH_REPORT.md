# Graph Report - RepoPilot  (2026-07-10)

## Corpus Check
- 195 files · ~114,006 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2016 nodes · 4989 edges · 116 communities (97 shown, 19 thin omitted)
- Extraction: 64% EXTRACTED · 36% INFERRED · 0% AMBIGUOUS · INFERRED: 1799 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `70868e3d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 79|Community 79]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]
- [[_COMMUNITY_Community 113|Community 113]]
- [[_COMMUNITY_Community 114|Community 114]]
- [[_COMMUNITY_Community 115|Community 115]]

## God Nodes (most connected - your core abstractions)
1. `IntentProfile` - 163 edges
2. `LLMProvider` - 150 edges
3. `Settings` - 116 edges
4. `Claim` - 82 edges
5. `Claim` - 80 edges
6. `Message` - 79 edges
7. `CapabilityPlan` - 66 edges
8. `CodeRef` - 60 edges
9. `BaseTourEvent` - 51 edges
10. `Insight` - 45 edges

## Surprising Connections (you probably didn't know these)
- `RedisSettings` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `Any` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `WorkerSettings` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `Any` --uses--> `IntentProfile`  [INFERRED]
  apps/api/src/repopilot_api/models.py → packages/agents/src/repopilot_agents/state.py
- `RepoRecord` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/services.py → packages/core/src/repopilot_core/llm/provider.py

## Import Cycles
- 1-file cycle: `apps/api/src/repopilot_api/app.py -> apps/api/src/repopilot_api/app.py`

## Communities (116 total, 19 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (118): AppServices, Any, TourEventType, AsyncEngine, BaseTourEvent, ChunkPayload, CodeRef, IntentProfile (+110 more)

### Community 1 - "Community 1"
Cohesion: 0.07
Nodes (34): AST, AsyncFunctionDef, Call, ClassDef, FunctionDef, Import, ImportFrom, Module (+26 more)

### Community 2 - "Community 2"
Cohesion: 0.21
Nodes (13): CrossEncoderReranker, ChunkContent, ChunkHit, _hit_and_content(), RAG Phase 4: cross-encoder wrapper + rerank pipeline (stubbed encoder).  The rea, Scores by keyword overlap with the query; counts calls., reranker(), _StubEncoder (+5 more)

### Community 3 - "Community 3"
Cohesion: 0.17
Nodes (31): RateLimitError, HTTP 429 from a provider — triggers retry/fallback inside the provider.      ``r, ProviderName, Message, FakeClient, make_provider(), make_response(), Build an LLMProvider that uses the supplied fakes for every provider. (+23 more)

### Community 4 - "Community 4"
Cohesion: 0.13
Nodes (11): _BaseClient, _OpenAICompatibleClient, Common interface for provider HTTP shims., Speaks the OpenAI chat-completions shape. Used for Groq and Cerebras., In-process embedder using sentence-transformers (Hugging Face weights).      No, Default wiring used by the app. Tests pass `clients` for full control., _SentenceTransformersEmbedder, AsyncClient (+3 more)

### Community 5 - "Community 5"
Cohesion: 0.10
Nodes (45): _build_fact_bundle_for_test(), _fact_bundle(), Cartographer — produces ``system_map`` Insights from the call graph.  The Cartog, Run the Cartographer once.      Returns the state diff for the LangGraph reducer, Render the fact bundle as a compact text block.      We deliberately avoid prose, Resolve each symbol's CodeRef from graph_metrics's underlying lookup.      The m, _refs_for_symbols(), _resolve_refs() (+37 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (42): ChunkHit, AsyncEngine, ChunkHit, AsyncEngine, ChunkHit, LLMProvider, Any, ChunkHit (+34 more)

### Community 7 - "Community 7"
Cohesion: 0.15
Nodes (19): coerce_claim(), coerce_insight(), _coerce_ref(), coerce_refs(), extract_json_list(), Shared LLM-output coercion helpers for capability nodes.  Every node asks the LL, Pull the first JSON array out of ``raw`` and return it as a list of     dicts. R, Validate a ref. If the LLM names a symbol, prefer the known CodeRef     for that (+11 more)

### Community 8 - "Community 8"
Cohesion: 0.07
Nodes (36): api, ChunkPayload, ClaimEvent, ClaimStatus, CodeRef, CreateRepoResponse, CreateTourResponse, DiagramEvent (+28 more)

### Community 9 - "Community 9"
Cohesion: 0.26
Nodes (18): MonkeyPatch, _insight(), patched_carto_tools(), patched_traverse(), _plan(), _profile(), Unit tests for the Cartographer / Flow Tracer / Teacher nodes.  These tests pin, Stub the deterministic tools the Cartographer calls.      The fact bundle is sma (+10 more)

### Community 10 - "Community 10"
Cohesion: 0.07
Nodes (46): AsyncEngine, DiGraph, AsyncEngine, SymbolMetrics, AsyncEngine, DiGraph, GraphQueryResult, AsyncEngine (+38 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (28): Path, AsyncEngine, ChunkHit, LLMProvider, Any, RAG Phase 1: ``vector_search`` pool widening + metadata filters.  The pgvector S, _RecordingConn, _RecordingEngine (+20 more)

### Community 12 - "Community 12"
Cohesion: 0.07
Nodes (30): Any, EventDict, index_repo(), arq worker function for the Phase 1 ingestion pipeline.  The actual pipeline log, Build arq RedisSettings from Settings.redis_url.      Without this, arq falls ba, arq job: index a GitHub repo end-to-end. Returns a JSON-able status dict., arq discovery target. Run with: ``arq repopilot_api.jobs.index_repo.WorkerSettin, _redis_settings_from_url() (+22 more)

### Community 13 - "Community 13"
Cohesion: 0.14
Nodes (26): _coerce_keywords(), _coerce_modality_weights(), _coerce_optional_str(), _coerce_output_shape(), _fallback_profile(), _parse_json(), profile_intent(), Intent Profiler — free-text intent → structured ``IntentProfile``.  The Profiler (+18 more)

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (31): _derive_ranker_weights(), _infer_flow_targets(), _infer_shape(), _pick_hub_bias(), plan(), Capability Planner — deterministic ``IntentProfile`` → ``CapabilityPlan``.  The, Deterministic planner. See ``docs/03_ARCHITECTURE.md`` § "The     Capability Pla, Pick a hub-bias tilt for the Cartographer.      Data-heavy intents → "data_hubs" (+23 more)

### Community 15 - "Community 15"
Cohesion: 0.11
Nodes (20): ChunkHit, CodeRef, CodeRef, _apply_rerank(), mrr(), ndcg_at_k(), Pure-retrieval metrics: recall@k, NDCG@k, MRR over a labeled QA dataset.  Runs t, Rerank the pool head; keep the tail in original order so recall@k holds. (+12 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (21): ChunkContent, LLMProvider, Any, ChunkContent, _clip_ranges(), compress_chunk(), compress_chunks(), _compression_user_prompt() (+13 more)

### Community 17 - "Community 17"
Cohesion: 0.11
Nodes (34): Node, Path, Path, _class_base_names(), _class_method_names(), _extract_imports(), _extract_symbols(), _first_docstring() (+26 more)

### Community 18 - "Community 18"
Cohesion: 0.11
Nodes (28): AsyncEngine, IntentProfile, Any, CodeRef, MonkeyPatch, TourSection, build_graph(), Build + compile the full ``ArchaeologistState`` LangGraph.      Pass a Postgres (+20 more)

### Community 19 - "Community 19"
Cohesion: 0.20
Nodes (22): ArchaeologistState, Any, LLMProvider, _capability_planner_node(), _cartographer_node(), _flow_tracer_node(), _intent_profiler_node(), _lane_a_node() (+14 more)

### Community 20 - "Community 20"
Cohesion: 0.08
Nodes (25): 03 — Architecture, Agent table, Agent topology, Capability dependencies, Deterministic tools, Eval harness vs. product runtime — a hard line, Failure modes and cost design, How the intent profile flows through the system (+17 more)

### Community 21 - "Community 21"
Cohesion: 0.16
Nodes (22): AsyncEngine, ChunkContent, Claim, LLMProvider, answer_question(), _Context, _estimate_tokens(), _extend_context() (+14 more)

### Community 22 - "Community 22"
Cohesion: 0.18
Nodes (16): MonkeyPatch, Path, GroundingEvalRow, _async_return(), _dataset_path(), _DummyContext, _DummyEngine, _DummyProvider (+8 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (25): dependencies, next, react, react-dom, devDependencies, lighthouse, @playwright/test, @types/node (+17 more)

### Community 24 - "Community 24"
Cohesion: 0.20
Nodes (5): Any, EmbeddingResponse, Shared fixtures for the core package's tests., FakeEmbedder, Test double for the sentence-transformers in-process embedder.      Returns dete

### Community 25 - "Community 25"
Cohesion: 0.13
Nodes (14): GroundingEvalRow, CodeRef, QAResult, Settings, _contains_all_keywords(), GroundingEvalCaseResult, GroundingEvalMetrics, _has_expected_refs() (+6 more)

### Community 26 - "Community 26"
Cohesion: 0.08
Nodes (23): 1. Clone and install, 2. Create `.env`, 3. Start data services, 4. Run the API, 5. Run the web app, 6. Run checks, Agent Graph, API Surface (+15 more)

### Community 27 - "Community 27"
Cohesion: 0.19
Nodes (16): EvalSpec, GroundingEvalMetrics, Namespace, Path, _cmd_list(), _grounding_markdown(), main(), _print_grounding() (+8 more)

### Community 28 - "Community 28"
Cohesion: 0.15
Nodes (21): IntentProfileEvalRow, Path, PlannerEvalRow, dataset_path(), FileMappingEvalRow, IntentProfileEvalRow, load_file_mapping_dataset(), load_grounding_dataset() (+13 more)

### Community 29 - "Community 29"
Cohesion: 0.05
Nodes (72): build_opportunity_briefing(), ranker_rationale(), Teacher-facing briefing helpers for Phase 5 opportunity cards., Attach the UI-visible Phase 5 briefing surfaces without reranking., Plain-English explanation of planner-derived ranker weights., approachability_score(), Lane A — issue triage backed by graph approachability., Score issue approachability from graph facts, not GitHub labels. (+64 more)

### Community 30 - "Community 30"
Cohesion: 0.18
Nodes (20): CapabilityPlan, IntentProfile, IntentProfile, _format_active(), _format_keywords(), _format_tilt_line(), _format_weights(), Goal-anchor prompt block — shared across every generation node.  Every generatio (+12 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (13): Any, ChunkContent, CodeRef, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, FakeChunk, FakeEngine, FakeProvider, make_content() (+5 more)

### Community 32 - "Community 32"
Cohesion: 0.33
Nodes (11): Path, aggregate(), bench_repo(), main(), Top-level RAG-phase bench runner.  Usage::      uv run python -m repopilot_evals, Compare ``_after`` to ``_before`` per repo; fail on guardrail breaches.      Gua, Gate sanity check: baseline vs itself must be 'not significant'., results_dir() (+3 more)

### Community 33 - "Community 33"
Cohesion: 0.10
Nodes (20): LangGraph nodes + capability library.  Phase 2 surface: the six deterministic to, ChunkContent, ChunkHit, CodeRef, GraphQueryResult, Path, Shared Pydantic types used across tools, verifier, and Q&A.  These are the typed, Pointer into the repo. Every factual claim must carry at least one. (+12 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (20): 01 — Problem and Solution, Fine-grained mapping: example stated intents → what the Capability Planner picks, Four concrete walkthroughs (out of infinitely many possible), Hard scope fence — what v1 will NOT do, How the flow handles "hard-to-context-map" responses, Key features (at a glance), Success criteria, The core bet (+12 more)

### Community 35 - "Community 35"
Cohesion: 0.22
Nodes (16): CloneResult, ModuleSource, Chunk, LLMProvider, Path, Settings, CloneResult, Canonical primary key used across the schema: ``owner/name@sha``. (+8 more)

### Community 36 - "Community 36"
Cohesion: 0.11
Nodes (17): Path, clone_to_tempdir(), parse_github_url(), GitHub clone + HEAD-SHA helpers for Phase 1 ingestion.  Two entry points:  * :fu, Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c, remote_head_sha() (+9 more)

### Community 37 - "Community 37"
Cohesion: 0.13
Nodes (24): CodeRef, CapabilityPlan, QAExchange, Deterministic Planner output. Verifiable in CI., One completed Q&A turn. v1 keeps the last 8; the prompt only consumes     the cu, Validator tests for ``ArchaeologistState`` and its sub-models.  These tests pin, _ref(), test_claim_defaults_unverified() (+16 more)

### Community 38 - "Community 38"
Cohesion: 0.10
Nodes (20): compilerOptions, allowImportingTsExtensions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib (+12 more)

### Community 39 - "Community 39"
Cohesion: 0.15
Nodes (15): ChunkContent, CodeRef, ChunkContent, MonkeyPatch, attribute_refs(), Claim → ref attribution via the Phase 4 cross-encoder.  The verifier judges each, Return the refs of the ``k`` chunks most relevant to ``claim_text``.      Best-f, _chunk() (+7 more)

### Community 40 - "Community 40"
Cohesion: 0.14
Nodes (22): AsyncEngine, ChunkContent, LLMProvider, _apply(), _Cache, _objection_if_rejected(), Per-claim grounding check against ``read_chunks``.  The Verifier is the single l, Test helper — clear the verifier verdict cache. (+14 more)

### Community 41 - "Community 41"
Cohesion: 0.18
Nodes (10): Connection, EmbeddingResponse, Provider-agnostic embedding shape., Thread-safe SQLite cache keyed on the canonical request hash., Embed ``text`` via the in-process sentence-transformers embedder.          No HT, _SQLiteCache, Path, Path (+2 more)

### Community 42 - "Community 42"
Cohesion: 0.16
Nodes (14): Any, ChunkContent, CodeRef, MonkeyPatch, _chunk(), _patch_tools(), End-to-end Q&A tests against fully stubbed dependencies.  We monkey-patch the th, Returns canned text responses in queue order. (+6 more)

### Community 43 - "Community 43"
Cohesion: 0.14
Nodes (13): ChunkContent, ChunkContent, ChunkHit, Cross-encoder reranker over (query, chunk) pairs via ``fastembed``.  Unlike the, The text the cross-encoder sees for one chunk (symbol-prefixed)., Process-wide reranker so the ONNX model loads once., rerank_text(), shared_reranker() (+5 more)

### Community 44 - "Community 44"
Cohesion: 0.12
Nodes (16): Current Build Phase, Design decisions & deviations from spec, How it landed — the λ × pool sweep, How to advance the phase, LLM guardrails through the reranked path (closed 2026-07-10), Pending (does not block the land), Phase 0 facts that feed later phases, Phase 1 — how it landed (httpx) (+8 more)

### Community 45 - "Community 45"
Cohesion: 0.14
Nodes (7): Alembic environment — uses Settings.postgres_dsn so dev + CI agree., SQLAlchemy schema for Phase 1 ingestion.  Tables:     repos              one row, Minimal pgvector type so alembic can emit `vector(N)` without importing     the, Vector, Batched async embedder over chunks via the central ``LLMProvider``.  The provide, Return a deterministic normalized vector when the local embedder rejects a chunk, _stable_fallback_vector()

### Community 46 - "Community 46"
Cohesion: 0.15
Nodes (22): Any, MonkeyPatch, Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)., The semaphore must cap in-flight verifier calls at max_concurrency., _StubEngine, _StubProvider, test_parse_verdict_accepts_clean_json(), test_parse_verdict_extracts_json_from_prose() (+14 more)

### Community 47 - "Community 47"
Cohesion: 0.31
Nodes (10): Settings, VerifierEvalRow, Eval runners for the phase gates., _patched_read_chunks(), Verifier-quality eval runner for the Phase 2 gate., run_verifier_eval(), run_verifier_eval_rows(), VerifierEvalCaseResult (+2 more)

### Community 48 - "Community 48"
Cohesion: 0.12
Nodes (15): D1.1 — Close Phase 0 (30 min), D1.2 — Phase 1: Recall Lift (~3 h) — **must ship**, D1.3 — Phase 2: Query Understanding (timebox **2 h**, cut line 18:00) — polish, D1.4 — Phase 3: BM25 Hybrid (start today, finish by D2 morning) — **must ship**, D2.1 — Phase 3 finish (~2 h) — **must ship**, D2.2 — Phase 4: Reranking (~3 h) — **must ship**, D2.3 — Phase 5: Context Compression (timebox **90 min**) — polish, D2.4 — Phase 6: Ingestion Enrichment (timebox **90 min**, incl. re-index wait) — polish (+7 more)

### Community 49 - "Community 49"
Cohesion: 0.14
Nodes (13): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, After Phase 6 (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.21
Nodes (13): jaccard(), mmr_select(), Maximal Marginal Relevance — diversity-aware top-k selection (pure).  ``MMR(c) =, Return indices of up to ``k`` items, MMR-ordered (pure function).      ``relevan, _tokens(), RAG Phase 4: MMR diversity selection (pure function)., test_constant_relevance_normalises_safely(), test_empty_and_zero_k() (+5 more)

### Community 51 - "Community 51"
Cohesion: 0.15
Nodes (12): 02 — Tech Stack, ASCII full-stack diagram, Backend layer, Code intelligence layer (deterministic, NO LLM), Frontend layer, Groq free-tier survival strategy, LLM layer, Orchestration layer (+4 more)

### Community 52 - "Community 52"
Cohesion: 0.25
Nodes (4): paired_bootstrap(), Paired bootstrap significance test between two metric arrays.  Used by every pha, SignificanceResult, TestSignificance

### Community 53 - "Community 53"
Cohesion: 0.15
Nodes (12): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, Honest notes (+4 more)

### Community 54 - "Community 54"
Cohesion: 0.15
Nodes (12): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, Honest notes (+4 more)

### Community 55 - "Community 55"
Cohesion: 0.15
Nodes (12): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, Critical safety rule (+4 more)

### Community 56 - "Community 56"
Cohesion: 0.15
Nodes (12): Priority order for acting on this doc, R1 — The eval foundation is too thin for the effects being measured (ROOT RISK), R2 — Per-phase latency budgets are mathematically inconsistent with the global gate, R3 — "Significant on at least one of three datasets" inflates false positives, R4 — The verifier is load-bearing but unvalidated, R5 — Phases optimize around a fixed, non-code-specialized embedding model, R6 — Phases are measured pairwise, but the effects interact, R7 — Synthetic-content safety rests on a single test (+4 more)

### Community 57 - "Community 57"
Cohesion: 0.17
Nodes (11): Definition of Done (for the whole plan), Eval datasets we will use, For contributors, Metrics, in priority order, Per-phase doc template (what every `docs/rag/<n>_*.md` looks like), RAG Quality Plan — RepoPilot Retrieval Upgrade, Sequencing rationale (why this order), The 7 phases at a glance (+3 more)

### Community 58 - "Community 58"
Cohesion: 0.17
Nodes (11): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, Honest notes (+3 more)

### Community 59 - "Community 59"
Cohesion: 0.28
Nodes (5): Any, MonkeyPatch, CrossEncoderReranker, Lazy-loading, score-caching wrapper around ``fastembed.TextCrossEncoder``., Relevance score per text (higher = more relevant). Cached per pair.

### Community 60 - "Community 60"
Cohesion: 0.31
Nodes (10): _coerce_section(), _collect_refs(), _format_source_bundle(), Teacher — weaves Insights into goal-anchored ``TourSection``s.  The Teacher is t, Run the Teacher once.      Returns ``{"draft_tour": [TourSection, …]}``. Empty l, Index every CodeRef from upstream insights by symbol so the Teacher     can only, run_teacher(), CodeRef (+2 more)

### Community 61 - "Community 61"
Cohesion: 0.18
Nodes (8): AsyncEngine, Settings, take_rows(), resolve_repo_id(), RetrievalEvalMetrics, run_retrieval_eval(), SearchMode, T

### Community 62 - "Community 62"
Cohesion: 0.20
Nodes (5): Animal, Dog, Fixture file the chunker tests assert against. Real Python so AST is exact., A base class with one method., A subclass overriding speak().

### Community 63 - "Community 63"
Cohesion: 0.26
Nodes (11): Any, Path, _cmd_status(), _coerce(), _ensure_reports_dir(), find_latest_report(), _now_stamp(), Persisted eval reports.  Each eval run writes a timestamped JSON + Markdown pair (+3 more)

### Community 64 - "Community 64"
Cohesion: 0.31
Nodes (9): MonkeyPatch, Decide whether ``repo_url`` is already-current, stale, or unknown.      Cheap —, revisit_status(), Idempotency + staleness — exercised against a stubbed DB and stubbed clone.  The, When the remote HEAD has moved past the indexed SHA → status=stale., _StubEngine, test_revisit_unknown_repo_returns_stale(), test_revisit_with_advanced_remote_returns_stale_status() (+1 more)

### Community 65 - "Community 65"
Cohesion: 0.18
Nodes (10): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, As-built record (Phase 0 closed 2026-07-04), Honest notes for future-me (+2 more)

### Community 66 - "Community 66"
Cohesion: 0.18
Nodes (10): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, Honest notes (+2 more)

### Community 67 - "Community 67"
Cohesion: 0.21
Nodes (7): Settings, LatencyEvalMetrics, percentile(), Latency runner: p50/p95 wall-clock timings around ``answer_question``., Nearest-rank percentile over a pre-sorted list., run_latency_eval(), TestPercentile

### Community 68 - "Community 68"
Cohesion: 0.20
Nodes (9): 1. What this project is, 2. How project knowledge is organized, 3. Knowledge Graph first (Graphify), 4. Graph maintenance (mandatory), 5. Codex harness (`.Codex/`), 6. Engineering conventions, 7. Definition of Done, 8. For contributors (human or AI) (+1 more)

### Community 69 - "Community 69"
Cohesion: 0.20
Nodes (9): 1. What this project is, 2. How project knowledge is organized, 3. Knowledge Graph first (Graphify), 4. Graph maintenance (mandatory), 5. Claude Code harness (`.claude/`), 6. Engineering conventions, 7. Definition of Done, 8. For contributors (human or AI) (+1 more)

### Community 70 - "Community 70"
Cohesion: 0.22
Nodes (10): _cache_key(), LLMResponse, Generate a completion. Hits cache first; otherwise walks the fallback chain., Per-binding 429 retry loop with exponential backoff + jitter., Provider-agnostic response shape., LLMResponse, ModelId, Any (+2 more)

### Community 71 - "Community 71"
Cohesion: 0.15
Nodes (15): Settings, AsyncEngine, Settings, known_head_sha(), make_engine(), persist_index(), PersistResult, Persist Phase 1 pipeline output to Postgres + pgvector.  The functions here are (+7 more)

### Community 72 - "Community 72"
Cohesion: 0.42
Nodes (8): Path, accept_row(), load(), main(), Terminal review loop for candidate eval labels (Phase 0, Option A).  Walks every, review(), save(), show_row()

### Community 73 - "Community 73"
Cohesion: 0.29
Nodes (7): ModelBinding, ModelId, ProviderName, Logical model identifiers and their physical-model resolution per provider.  Age, Logical, agent-facing model identifiers., The concrete model name to send to a given provider for one `ModelId`., StrEnum

### Community 74 - "Community 74"
Cohesion: 0.19
Nodes (15): Path, ParsedFile, ParsedSymbol, chunk_file(), _class_header_content(), _class_header_end_line(), _module_residue_lines(), _module_symbol_from_path() (+7 more)

### Community 75 - "Community 75"
Cohesion: 0.13
Nodes (29): BaseSettings, EmbeddedChunk, ProviderError, All providers in the fallback chain failed., CodeRef, Chunk, LLMProvider, Settings (+21 more)

### Community 76 - "Community 76"
Cohesion: 0.29
Nodes (6): AsyncEngine, ChunkContent, CodeRef, ``read_chunks`` — the ONLY tool that returns source text.  Per Phase 2 decision, Fetch the content of every chunk whose ``(file_path, start_line, end_line)``, read_chunks()

### Community 77 - "Community 77"
Cohesion: 0.29
Nodes (6): Authoring, Engineering conventions, Graph maintenance (mandatory), Knowledge graph first, RepoPilot — Project Rules (portable), What this project is

### Community 78 - "Community 78"
Cohesion: 0.08
Nodes (60): ClaimStatus, AsyncEngine, Claim, IntentProfile, LLMProvider, TourSection, Any, CodeRef (+52 more)

### Community 79 - "Community 79"
Cohesion: 0.33
Nodes (5): Build Prompt — Ship Closeout (Definition of Done), Build the regression gate, Final protocol, Verify (report each with the actual number, no hedging), Write the ship report

### Community 80 - "Community 80"
Cohesion: 0.14
Nodes (13): _backoff_delay(), _extract_openai_compatible_text(), _parse_retry_after(), The single LLMProvider every agent goes through.  Responsibilities (Phase 0 deli, Exponential backoff with full jitter. attempt=0 is the first retry., Parse a ``Retry-After`` header (delta-seconds or HTTP-date) into seconds.      P, Extract assistant text from OpenAI-compatible payload variants.      Some provid, test_backoff_delay_is_bounded() (+5 more)

### Community 81 - "Community 81"
Cohesion: 0.40
Nodes (4): Layout, Read in order (cold pickup), RepoPilot — Docs, The one-paragraph story

### Community 82 - "Community 82"
Cohesion: 0.50
Nodes (4): Path, _iter_source_files(), Hard CI rule: nothing in the source tree may branch on a ``purpose`` enum.  Phas, test_no_purpose_enum_in_source_tree()

### Community 83 - "Community 83"
Cohesion: 0.40
Nodes (4): Bench commands (referee, unchanged since Phase 0), Iron rules (baked into every spec), Order of execution, RAG Phase Ladder — README

### Community 84 - "Community 84"
Cohesion: 0.50
Nodes (3): Constraints, Mandatory order of operations, What to return

### Community 113 - "Community 113"
Cohesion: 0.26
Nodes (8): Any, EmbeddingResponse, ModelBinding, FakeEmbedder, Tests for ``LLMProvider.embed()`` — cache hit, fresh embed, dim contract., Test double — bypasses the sentence-transformers model load and     returns cann, test_embed_cache_hit_skips_provider(), test_embed_returns_vector()

### Community 114 - "Community 114"
Cohesion: 0.50
Nodes (7): ChunkContent, answer_user_prompt(), _chunk_view(), Q&A prompt templates.  Three prompts, all under the 2000-token budget from ``doc, _render_chunks(), _render_numbered_chunk(), sufficiency_user_prompt()

## Knowledge Gaps
- **316 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `type` (+311 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMProvider` connect `Community 5` to `Community 0`, `Community 3`, `Community 4`, `Community 6`, `Community 9`, `Community 11`, `Community 12`, `Community 13`, `Community 16`, `Community 18`, `Community 19`, `Community 21`, `Community 24`, `Community 35`, `Community 40`, `Community 41`, `Community 60`, `Community 61`, `Community 70`, `Community 71`, `Community 75`, `Community 78`, `Community 80`, `Community 115`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 75` to `Community 0`, `Community 35`, `Community 4`, `Community 5`, `Community 70`, `Community 3`, `Community 71`, `Community 41`, `Community 67`, `Community 12`, `Community 15`, `Community 47`, `Community 24`, `Community 25`, `Community 61`?**
  _High betweenness centrality (0.086) - this node is a cross-community bridge._
- **Why does `IntentProfile` connect `Community 0` to `Community 5`, `Community 37`, `Community 9`, `Community 13`, `Community 78`, `Community 14`, `Community 18`, `Community 19`, `Community 115`, `Community 60`, `Community 29`, `Community 30`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Are the 147 inferred relationships involving `IntentProfile` (e.g. with `Any` and `TourEventType`) actually correct?**
  _`IntentProfile` has 147 INFERRED edges - model-reasoned connections that need verification._
- **Are the 142 inferred relationships involving `LLMProvider` (e.g. with `Any` and `AsyncEngine`) actually correct?**
  _`LLMProvider` has 142 INFERRED edges - model-reasoned connections that need verification._
- **Are the 109 inferred relationships involving `Settings` (e.g. with `AsyncEngine` and `BaseTourEvent`) actually correct?**
  _`Settings` has 109 INFERRED edges - model-reasoned connections that need verification._
- **Are the 70 inferred relationships involving `Claim` (e.g. with `AsyncEngine` and `BaseTourEvent`) actually correct?**
  _`Claim` has 70 INFERRED edges - model-reasoned connections that need verification._