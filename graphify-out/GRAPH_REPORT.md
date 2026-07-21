# Graph Report - RepoPilot  (2026-07-21)

## Corpus Check
- 216 files · ~126,550 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2119 nodes · 5590 edges · 121 communities (101 shown, 20 thin omitted)
- Extraction: 64% EXTRACTED · 36% INFERRED · 0% AMBIGUOUS · INFERRED: 2040 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `72c6132b`
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
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]
- [[_COMMUNITY_Community 107|Community 107]]
- [[_COMMUNITY_Community 113|Community 113]]
- [[_COMMUNITY_Community 114|Community 114]]
- [[_COMMUNITY_Community 116|Community 116]]
- [[_COMMUNITY_Community 119|Community 119]]
- [[_COMMUNITY_Community 120|Community 120]]
- [[_COMMUNITY_Community 121|Community 121]]
- [[_COMMUNITY_Community 127|Community 127]]

## God Nodes (most connected - your core abstractions)
1. `IntentProfile` - 169 edges
2. `LLMProvider` - 168 edges
3. `Settings` - 141 edges
4. `Claim` - 86 edges
5. `Claim` - 86 edges
6. `Message` - 84 edges
7. `CapabilityPlan` - 66 edges
8. `CodeRef` - 60 edges
9. `BaseTourEvent` - 55 edges
10. `TourSectionStartEvent` - 46 edges

## Surprising Connections (you probably didn't know these)
- `RedisSettings` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `Any` --uses--> `IntentProfile`  [INFERRED]
  apps/api/src/repopilot_api/models.py → packages/agents/src/repopilot_agents/state.py
- `AllowanceExceededError` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/access.py → packages/core/src/repopilot_core/llm/provider.py
- `AllowanceExceededError` --uses--> `Settings`  [INFERRED]
  apps/api/src/repopilot_api/access.py → packages/core/src/repopilot_core/settings.py
- `AccountUsage` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/access.py → packages/core/src/repopilot_core/llm/provider.py

## Import Cycles
- 1-file cycle: `apps/api/src/repopilot_api/app.py -> apps/api/src/repopilot_api/app.py`

## Communities (121 total, 20 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.25
Nodes (32): TourEventType, AsyncEngine, BaseTourEvent, ChunkPayload, CodeRef, GraphQueryResult, IntentProfile, LLMProvider (+24 more)

### Community 1 - "Community 1"
Cohesion: 0.14
Nodes (29): Any, CodeRef, MonkeyPatch, TourSection, _claim(), engine(), _patch_read_chunks(), Verifier-loop tests: actionability rubric + retry budget + flagging.  The ground (+21 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (48): AccountUsage, api, ApiError, ChunkPayload, ClaimEvent, ClaimStatus, CodeRef, CreateRepoResponse (+40 more)

### Community 3 - "Community 3"
Cohesion: 0.21
Nodes (23): Node, _class_base_names(), _class_method_names(), _decorators(), _docstring_tokens(), _extract_imports(), _extract_symbols(), _first_docstring() (+15 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (23): Chunk, LLMProvider, Settings, Path, EmbeddingResponse, Path, Parser, embed_chunks() (+15 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (12): LLMProvider, AccessService, AccountUsage, AllowanceExceededError, InMemoryAccessService, ProductAccessService, Anonymous product sessions, free allowances, and session-only BYOK providers., Raised when a session has no free allowance and no user provider key. (+4 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (44): ChunkHit, AsyncEngine, ChunkHit, AsyncEngine, ChunkHit, LLMProvider, Any, ChunkHit (+36 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (38): BaseModel, approachability_score(), Lane A — issue triage backed by graph approachability., Score issue approachability from graph facts, not GitHub labels., Rank issues and keep the next three rejected reasons., _ref_for_issue(), run_lane_a_triage(), triage_issues() (+30 more)

### Community 8 - "Community 8"
Cohesion: 0.21
Nodes (11): Any, EmbeddingResponse, ModelBinding, BatchEmbedder, FakeEmbedder, Tests for ``LLMProvider.embed()`` — cache hit, fresh embed, dim contract., Test double — bypasses the sentence-transformers model load and     returns cann, test_embed_cache_hit_skips_provider() (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.10
Nodes (62): _build_fact_bundle_for_test(), _fact_bundle(), Cartographer — produces ``system_map`` Insights from the call graph.  The Cartog, Run the Cartographer once.      Returns the state diff for the LangGraph reducer, Render the fact bundle as a compact text block.      We deliberately avoid prose, Resolve each symbol's CodeRef from graph_metrics's underlying lookup.      The m, _refs_for_symbols(), _resolve_refs() (+54 more)

### Community 10 - "Community 10"
Cohesion: 0.12
Nodes (25): BaseTourEvent, AsyncClient, QAClaim, A single grounded claim in the Q&A answer., format_sse_comment(), format_sse_event(), Helpers for formatting and parsing the Phase 4 SSE protocol., with_heartbeats() (+17 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (22): AsyncEngine, ChunkHit, LLMProvider, Any, RAG Phase 1: ``vector_search`` pool widening + metadata filters.  The pgvector S, _RecordingConn, _RecordingEngine, _run() (+14 more)

### Community 12 - "Community 12"
Cohesion: 0.08
Nodes (26): Settings, Product-layer tables for sessions, entitlements, usage, and tours., build_claims_for_symbols(), build_mermaid(), build_runtime(), close_live_services(), create_live_services(), decode_chunk_id() (+18 more)

### Community 13 - "Community 13"
Cohesion: 0.14
Nodes (23): ProviderError, All providers in the fallback chain failed., AsyncEngine, ChunkContent, CodeRef, LLMProvider, _apply(), _Cache (+15 more)

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (29): _derive_ranker_weights(), _infer_flow_targets(), _infer_shape(), _pick_hub_bias(), plan(), Capability Planner — deterministic ``IntentProfile`` → ``CapabilityPlan``.  The, Deterministic planner. See ``docs/03_ARCHITECTURE.md`` § "The     Capability Pla, Pick a hub-bias tilt for the Cartographer.      Data-heavy intents → "data_hubs" (+21 more)

### Community 15 - "Community 15"
Cohesion: 0.09
Nodes (23): Any, EventDict, index_repo(), arq worker function for the Phase 1 ingestion pipeline.  The actual pipeline log, Build arq RedisSettings from Settings.redis_url.      Without this, arq falls ba, arq job: index a GitHub repo end-to-end. Returns a JSON-able status dict., arq discovery target. Run with: ``arq repopilot_api.jobs.index_repo.WorkerSettin, _redis_settings_from_url() (+15 more)

### Community 16 - "Community 16"
Cohesion: 0.17
Nodes (31): RateLimitError, HTTP 429 from a provider — triggers retry/fallback inside the provider.      ``r, ProviderName, Message, FakeClient, make_provider(), make_response(), Build an LLMProvider that uses the supplied fakes for every provider. (+23 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (49): ArchaeologistState, lane_c_language_violation(), _matches_focus(), Lane C — guarded structural suspicions., Return the banned phrase when Lane C language is too certain., Build guarded suspicion opportunities from deterministic candidates.      Phase, run_lane_c_suspicion(), _lane_weight() (+41 more)

### Community 18 - "Community 18"
Cohesion: 0.07
Nodes (29): dependencies, geist, next, @phosphor-icons/react, react, react-dom, devDependencies, lighthouse (+21 more)

### Community 19 - "Community 19"
Cohesion: 0.21
Nodes (14): AppServices, Any, FastAPI, FastAPI app for the Phase 4 API contract., FastAPI app entrypoint. Endpoints are added in Phase 4., AccountUsageResponse, AskTourRequest, CreateRepoRequest (+6 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (21): 03 — Architecture, Agent table, Agent topology, Capability dependencies, Deterministic tools, Eval harness vs. product runtime — a hard line, Failure modes and cost design, How the intent profile flows through the system (+13 more)

### Community 21 - "Community 21"
Cohesion: 0.14
Nodes (19): Any, ChunkContent, CodeRef, MonkeyPatch, answer_question(), _estimate_tokens(), Run the hybrid-retrieval Q&A loop for ``question``.      ``recall_k`` / ``exclud, Cheap, stable token estimate for relative Phase 5 prompt-size gating. (+11 more)

### Community 22 - "Community 22"
Cohesion: 0.19
Nodes (17): MonkeyPatch, Path, GroundingEvalRow, VerifierEvalRow, _async_return(), _dataset_path(), _DummyContext, _DummyEngine (+9 more)

### Community 23 - "Community 23"
Cohesion: 0.16
Nodes (23): _coerce_keywords(), _coerce_modality_weights(), _coerce_optional_str(), _fallback_profile(), _parse_json(), profile_intent(), Intent Profiler — free-text intent → structured ``IntentProfile``.  The Profiler, The minimal-but-valid profile used when the LLM fails us.      Matches the "inte (+15 more)

### Community 24 - "Community 24"
Cohesion: 0.17
Nodes (26): ModuleSource, Chunk, CloneResult, LLMProvider, Path, Settings, Chunk, One indexable unit of source. Line numbers are 1-based, inclusive. (+18 more)

### Community 25 - "Community 25"
Cohesion: 0.13
Nodes (15): GroundingEvalRow, CodeRef, QAResult, Settings, _contains_all_keywords(), GroundingEvalCaseResult, GroundingEvalMetrics, _has_expected_refs() (+7 more)

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (16): Agent Graph, API Surface, Architecture At A Glance, Current Build State, Design Principles, Development Workflow, Documentation Map, Graph Connections That Matter (+8 more)

### Community 27 - "Community 27"
Cohesion: 0.18
Nodes (17): EvalSpec, GroundingEvalMetrics, Namespace, Path, _cmd_list(), _grounding_markdown(), main(), _print_grounding() (+9 more)

### Community 28 - "Community 28"
Cohesion: 0.08
Nodes (36): ChunkContent, LLMProvider, ChunkContent, Any, ChunkContent, Any, ChunkContent, _clip_ranges() (+28 more)

### Community 29 - "Community 29"
Cohesion: 0.16
Nodes (28): ClaimStatus, AsyncEngine, Claim, IntentProfile, LLMProvider, TourSection, Phase2Claim, TourSection (+20 more)

### Community 30 - "Community 30"
Cohesion: 0.20
Nodes (20): AsyncEngine, DiGraph, GraphQueryResult, QueryKind, _prime_cache(), Tests for ``graph_query``: entry points, hubs, callers/callees, layers.  Exercis, test_callees_of_a(), test_callers_of_c() (+12 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (13): Any, ChunkContent, CodeRef, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, FakeChunk, FakeEngine, FakeProvider, make_content() (+5 more)

### Community 32 - "Community 32"
Cohesion: 0.10
Nodes (18): LangGraph nodes + capability library.  Phase 2 surface: the six deterministic to, ChunkContent, ChunkHit, GraphQueryResult, Path, Shared Pydantic types used across tools, verifier, and Q&A.  These are the typed, Result of ``read_chunks``: a CodeRef paired with the source text it points at., Result of ``vector_search``: a chunk with retrieval metadata. (+10 more)

### Community 33 - "Community 33"
Cohesion: 0.17
Nodes (20): Chunk, Path, CloneResult, MonkeyPatch, Path, chunk_text_file(), _context_language(), iter_generic_files() (+12 more)

### Community 34 - "Community 34"
Cohesion: 0.15
Nodes (21): IntentProfileEvalRow, Path, PlannerEvalRow, dataset_path(), FileMappingEvalRow, IntentProfileEvalRow, load_file_mapping_dataset(), load_grounding_dataset() (+13 more)

### Community 35 - "Community 35"
Cohesion: 0.17
Nodes (13): _cache_key(), _extract_openai_compatible_text(), LLMResponse, Extract assistant text from OpenAI-compatible payload variants.      Some provid, Generate a completion. Hits cache first; otherwise walks the fallback chain., Per-binding 429 retry loop with exponential backoff + jitter., Provider-agnostic response shape., Any (+5 more)

### Community 36 - "Community 36"
Cohesion: 0.12
Nodes (26): AsyncEngine, IntentProfile, Any, MonkeyPatch, build_graph(), Build + compile the full ``ArchaeologistState`` LangGraph.      Pass a Postgres, ArchaeologistState, The single shared LangGraph state. See ``docs/03_ARCHITECTURE.md``. (+18 more)

### Community 37 - "Community 37"
Cohesion: 0.12
Nodes (25): CodeRef, ArchaeologistError, Claim, QAExchange, ``ArchaeologistState`` and the Pydantic v2 schema it composes.  This is the Phas, Every fail-edge in the graph emits one of these., One completed Q&A turn. v1 keeps the last 8; the prompt only consumes     the cu, A factual assertion produced by an agent. Must carry refs. (+17 more)

### Community 38 - "Community 38"
Cohesion: 0.10
Nodes (20): 01 — Problem and Solution, Fine-grained mapping: example stated intents → what the Capability Planner picks, Four concrete walkthroughs (out of infinitely many possible), Hard scope fence — what v1 will NOT do, How the flow handles "hard-to-context-map" responses, Key features (at a glance), Success criteria, The core bet (+12 more)

### Community 39 - "Community 39"
Cohesion: 0.15
Nodes (15): ChunkContent, CodeRef, ChunkContent, MonkeyPatch, attribute_refs(), Claim → ref attribution via the Phase 4 cross-encoder.  The verifier judges each, Return the refs of the ``k`` chunks most relevant to ``claim_text``.      Best-f, _chunk() (+7 more)

### Community 41 - "Community 41"
Cohesion: 0.10
Nodes (28): EmbeddedChunk, AsyncEngine, Chunk, LLMProvider, Message, Settings, delete_incomplete_index(), known_head_sha() (+20 more)

### Community 42 - "Community 42"
Cohesion: 0.10
Nodes (20): compilerOptions, allowImportingTsExtensions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib (+12 more)

### Community 43 - "Community 43"
Cohesion: 0.25
Nodes (10): Path, AsyncEngine, Settings, build_eval_context(), resolve_repo_id(), _is_noise(), _load_questions(), main() (+2 more)

### Community 44 - "Community 44"
Cohesion: 0.20
Nodes (10): Path, clone_to_tempdir(), parse_github_url(), Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c, Pure-logic tests around URL parsing and the revisit/staleness contract.  The net, test_parse_github_url_accepts_canonical_forms(), test_parse_github_url_rejects_unsupported() (+2 more)

### Community 45 - "Community 45"
Cohesion: 0.14
Nodes (24): AsyncEngine, ChunkContent, ChunkHit, Claim, LLMProvider, QuerySpec, _Context, _extend_context() (+16 more)

### Community 46 - "Community 46"
Cohesion: 0.07
Nodes (34): AST, AsyncFunctionDef, Call, ClassDef, FunctionDef, Import, ImportFrom, Module (+26 more)

### Community 47 - "Community 47"
Cohesion: 0.14
Nodes (18): BaseException, Any, build_query_spec(), fallback_query_spec(), _infer_intent(), _looks_multi_hop(), _merge_fallback_hints(), _normalize_paths() (+10 more)

### Community 48 - "Community 48"
Cohesion: 0.14
Nodes (9): Animal, Dog, Kennel, login(), Fixture file the chunker tests assert against. Real Python so AST is exact., A base class with one method., A subclass overriding speak()., Validate session csrf redirect. (+1 more)

### Community 49 - "Community 49"
Cohesion: 0.23
Nodes (13): Any, MonkeyPatch, CodeRef, Pointer into the repo. Every factual claim must carry at least one., The semaphore must cap in-flight verifier calls at max_concurrency., _StubEngine, _StubProvider, test_verify_claim_parse_fail_rejects() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.15
Nodes (12): Connection, _embedding_cache_key(), EmbeddingResponse, Provider-agnostic embedding shape., Thread-safe SQLite cache keyed on the canonical request hash., Embed ``text`` via the in-process sentence-transformers embedder.          No HT, Embed texts in backend batches while caching each distinct text independently., _SQLiteCache (+4 more)

### Community 51 - "Community 51"
Cohesion: 0.09
Nodes (32): Path, Path, ParsedFile, ParsedSymbol, _build_enriched_text(), chunk_file(), _class_header_content(), _class_header_end_line() (+24 more)

### Community 52 - "Community 52"
Cohesion: 0.21
Nodes (13): CrossEncoderReranker, ChunkContent, ChunkHit, _hit_and_content(), RAG Phase 4: cross-encoder wrapper + rerank pipeline (stubbed encoder).  The rea, Scores by keyword overlap with the query; counts calls., reranker(), _StubEncoder (+5 more)

### Community 53 - "Community 53"
Cohesion: 0.23
Nodes (13): Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)., test_parse_verdict_accepts_clean_json(), test_parse_verdict_extracts_json_from_prose(), test_parse_verdict_ignores_decoy_json_without_decision(), test_parse_verdict_returns_none_on_garbage(), test_parse_verdict_returns_none_on_invalid_decision(), test_parse_verdict_returns_none_when_only_think_block(), test_parse_verdict_strips_closed_think_block() (+5 more)

### Community 54 - "Community 54"
Cohesion: 0.21
Nodes (13): jaccard(), mmr_select(), Maximal Marginal Relevance — diversity-aware top-k selection (pure).  ``MMR(c) =, Return indices of up to ``k`` items, MMR-ordered (pure function).      ``relevan, _tokens(), RAG Phase 4: MMR diversity selection (pure function)., test_constant_relevance_normalises_safely(), test_empty_and_zero_k() (+5 more)

### Community 55 - "Community 55"
Cohesion: 0.31
Nodes (9): Settings, take_rows(), _patched_read_chunks(), Verifier-quality eval runner for the Phase 2 gate., run_verifier_eval(), run_verifier_eval_rows(), VerifierEvalCaseResult, T (+1 more)

### Community 56 - "Community 56"
Cohesion: 0.15
Nodes (12): 02 — Tech Stack, ASCII full-stack diagram, Backend layer, Code intelligence layer (deterministic, NO LLM), Frontend layer, Groq free-tier survival strategy, LLM layer, Orchestration layer (+4 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (13): ChunkContent, ChunkContent, ChunkHit, Cross-encoder reranker over (query, chunk) pairs via ``fastembed``.  Unlike the, The text the cross-encoder sees for one chunk (symbol-prefixed)., Process-wide reranker so the ONNX model loads once., rerank_text(), shared_reranker() (+5 more)

### Community 58 - "Community 58"
Cohesion: 0.24
Nodes (11): MonkeyPatch, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, remote_head_sha(), Decide whether ``repo_url`` is already-current, stale, or unknown.      Cheap —, revisit_status(), Idempotency + staleness — exercised against a stubbed DB and stubbed clone.  The, When the remote HEAD has moved past the indexed SHA → status=stale., _StubEngine (+3 more)

### Community 59 - "Community 59"
Cohesion: 0.28
Nodes (5): Any, MonkeyPatch, CrossEncoderReranker, Lazy-loading, score-caching wrapper around ``fastembed.TextCrossEncoder``., Relevance score per text (higher = more relevant). Cached per pair.

### Community 60 - "Community 60"
Cohesion: 0.15
Nodes (11): ChunkHit, MonkeyPatch, QuerySpec, Settings, QuerySpec, Structured retrieval plan for one user question., Return raw question + deduped rewrites, capped for latency., _hit() (+3 more)

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (8): Any, EmbeddingResponse, Path, Settings, Shared fixtures for the core package's tests., FakeEmbedder, Test double for the sentence-transformers in-process embedder.      Returns dete, tmp_settings()

### Community 62 - "Community 62"
Cohesion: 0.21
Nodes (9): CodeRef, 1/0 per ranked hit; each expected ref credits at most one hit., ref_matches(), relevance_vector(), Unit tests for the pure retrieval-metric math (no DB, no LLM)., _ref(), TestRefMatches, TestRelevanceVector (+1 more)

### Community 63 - "Community 63"
Cohesion: 0.26
Nodes (11): Any, Path, _cmd_status(), _coerce(), _ensure_reports_dir(), find_latest_report(), _now_stamp(), Persisted eval reports.  Each eval run writes a timestamped JSON + Markdown pair (+3 more)

### Community 64 - "Community 64"
Cohesion: 0.33
Nodes (11): Path, aggregate(), bench_repo(), main(), Top-level RAG-phase bench runner.  Usage::      uv run python -m repopilot_evals, Compare ``_after`` to ``_before`` per repo; fail on guardrail breaches.      Gua, Gate sanity check: baseline vs itself must be 'not significant'., results_dir() (+3 more)

### Community 65 - "Community 65"
Cohesion: 0.21
Nodes (7): Settings, LatencyEvalMetrics, percentile(), Latency runner: p50/p95 wall-clock timings around ``answer_question``., Nearest-rank percentile over a pre-sorted list., run_latency_eval(), TestPercentile

### Community 66 - "Community 66"
Cohesion: 0.25
Nodes (4): paired_bootstrap(), Paired bootstrap significance test between two metric arrays.  Used by every pha, SignificanceResult, TestSignificance

### Community 67 - "Community 67"
Cohesion: 0.42
Nodes (8): Path, accept_row(), load(), main(), Terminal review loop for candidate eval labels (Phase 0, Option A).  Walks every, review(), save(), show_row()

### Community 68 - "Community 68"
Cohesion: 0.22
Nodes (9): 1. What this project is, 2. How project knowledge is organized, 3. Knowledge Graph first (Graphify), 4. Graph maintenance (mandatory), 5. Codex harness (`.Codex/`), 6. Engineering conventions, 7. Definition of Done, 8. For contributors (human or AI) (+1 more)

### Community 69 - "Community 69"
Cohesion: 0.22
Nodes (9): 1. What this project is, 2. How project knowledge is organized, 3. Knowledge Graph first (Graphify), 4. Graph maintenance (mandatory), 5. Claude Code harness (`.claude/`), 6. Engineering conventions, 7. Definition of Done, 8. For contributors (human or AI) (+1 more)

### Community 70 - "Community 70"
Cohesion: 0.29
Nodes (7): ModelBinding, ModelId, ProviderName, Logical model identifiers and their physical-model resolution per provider.  Age, Logical, agent-facing model identifiers., The concrete model name to send to a given provider for one `ModelId`., StrEnum

### Community 71 - "Community 71"
Cohesion: 0.32
Nodes (5): Any, Path, _chunk(), FailingProvider, test_summarise_chunks_opens_circuit_after_provider_failure()

### Community 72 - "Community 72"
Cohesion: 0.06
Nodes (66): coerce_claim(), coerce_insight(), _coerce_ref(), coerce_refs(), extract_json_list(), Shared LLM-output coercion helpers for capability nodes.  Every node asks the LL, Pull the first JSON array out of ``raw`` and return it as a list of     dicts. R, Validate a ref. If the LLM names a symbol, prefer the known CodeRef     for that (+58 more)

### Community 73 - "Community 73"
Cohesion: 0.29
Nodes (6): Cumulative Picture, Deferred Entry States, Executive Status, Permanent Regression Gate, Phase Scorecard, RAG Ship Report

### Community 74 - "Community 74"
Cohesion: 0.29
Nodes (6): Authoring, Engineering conventions, Graph maintenance (mandatory), Knowledge graph first, RepoPilot — Project Rules (portable), What this project is

### Community 76 - "Community 76"
Cohesion: 0.23
Nodes (14): ChunkHit, CodeRef, _apply_rerank(), mrr(), _query_lane_weights(), Pure-retrieval metrics: recall@k, NDCG@k, MRR over a labeled QA dataset.  Runs t, Rerank the pool head; keep the tail in original order so recall@k holds., RetrievalCaseResult (+6 more)

### Community 78 - "Community 78"
Cohesion: 0.50
Nodes (4): Path, _iter_source_files(), Hard CI rule: nothing in the source tree may branch on a ``purpose`` enum.  Phas, test_no_purpose_enum_in_source_tree()

### Community 79 - "Community 79"
Cohesion: 0.50
Nodes (3): Constraints, Mandatory order of operations, What to return

### Community 80 - "Community 80"
Cohesion: 0.50
Nodes (4): Iteration 1 — Contribute lanes, in detail, Lane A — Issue Triage, Lane B — Quality Scanner, Lane C — Suspicion Scanner

### Community 81 - "Community 81"
Cohesion: 0.50
Nodes (4): Layout, Read in order (cold pickup), RepoPilot — Docs, The one-paragraph story

### Community 84 - "Community 84"
Cohesion: 0.17
Nodes (12): 1. Install Dependencies, 2. Configure Environment, 3. Start Local Services, 4. Run The App, 6. Use The App Locally, 7. Run Checks, 8. Graph Maintenance, Commands You Actually Use (+4 more)

### Community 85 - "Community 85"
Cohesion: 0.27
Nodes (33): Any, AppServices, BaseTourEvent, ChunkPayload, IntentProfile, MonkeyPatch, QAAnswerResponse, RepoStatus (+25 more)

### Community 100 - "Community 100"
Cohesion: 0.31
Nodes (8): build_opportunity_briefing(), ranker_rationale(), Teacher-facing briefing helpers for Phase 5 opportunity cards., Attach the UI-visible Phase 5 briefing surfaces without reranking., Plain-English explanation of planner-derived ranker weights., CapabilityPlan, IntentProfile, Opportunity

### Community 113 - "Community 113"
Cohesion: 0.10
Nodes (14): Path, Shared core: settings, logging, and the LLMProvider abstraction., _find_repo_env(), Application settings, loaded from environment / `.env` via pydantic-settings., Walk up from this file to the repo root and return the ``.env`` path.      Lets, Parse a comma-separated env var into a cleaned list., _split_csv(), EvalContext (+6 more)

### Community 114 - "Community 114"
Cohesion: 0.06
Nodes (31): Alembic environment — uses Settings.postgres_dsn so dev + CI agree., AsyncEngine, DiGraph, AsyncEngine, SymbolMetrics, AsyncEngine, CodeRef, Path (+23 more)

### Community 116 - "Community 116"
Cohesion: 0.39
Nodes (3): ndcg_at_k(), recall_at_k(), TestMetrics

### Community 119 - "Community 119"
Cohesion: 0.40
Nodes (5): AsyncEngine, ChunkContent, CodeRef, Fetch the content of every chunk whose ``(file_path, start_line, end_line)``, read_chunks()

### Community 120 - "Community 120"
Cohesion: 0.25
Nodes (7): Copy-paste prompt, Improved proposal for the chunking bottleneck, Proposed concurrency controls, Proposed fallback and rollout strategy, Proposed success thresholds, RepoPilot Ingestion Parallelization — Codex Execution Prompt, Suggested use

### Community 121 - "Community 121"
Cohesion: 0.10
Nodes (18): _backoff_delay(), _BaseClient, _OpenAICompatibleClient, _parse_retry_after(), The single LLMProvider every agent goes through.  Responsibilities (Phase 0 deli, Exponential backoff with full jitter. attempt=0 is the first retry., Parse a ``Retry-After`` header (delta-seconds or HTTP-date) into seconds.      P, Common interface for provider HTTP shims. (+10 more)

### Community 127 - "Community 127"
Cohesion: 0.40
Nodes (4): Production deployment, Release sequence, Required production environment, Service topology

## Knowledge Gaps
- **230 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `type` (+225 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMProvider` connect `Community 9` to `Community 0`, `Community 1`, `Community 4`, `Community 5`, `Community 6`, `Community 7`, `Community 11`, `Community 12`, `Community 13`, `Community 15`, `Community 16`, `Community 17`, `Community 23`, `Community 24`, `Community 28`, `Community 29`, `Community 35`, `Community 36`, `Community 41`, `Community 43`, `Community 45`, `Community 50`, `Community 60`, `Community 61`, `Community 72`, `Community 85`, `Community 113`, `Community 121`?**
  _High betweenness centrality (0.124) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 85` to `Community 0`, `Community 4`, `Community 5`, `Community 9`, `Community 10`, `Community 12`, `Community 13`, `Community 15`, `Community 16`, `Community 24`, `Community 25`, `Community 27`, `Community 33`, `Community 35`, `Community 41`, `Community 43`, `Community 50`, `Community 55`, `Community 60`, `Community 61`, `Community 65`, `Community 71`, `Community 75`, `Community 76`, `Community 113`, `Community 121`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Why does `IntentProfile` connect `Community 9` to `Community 0`, `Community 1`, `Community 100`, `Community 36`, `Community 37`, `Community 7`, `Community 72`, `Community 10`, `Community 12`, `Community 14`, `Community 17`, `Community 19`, `Community 85`, `Community 23`, `Community 29`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 153 inferred relationships involving `IntentProfile` (e.g. with `Any` and `TourEventType`) actually correct?**
  _`IntentProfile` has 153 INFERRED edges - model-reasoned connections that need verification._
- **Are the 159 inferred relationships involving `LLMProvider` (e.g. with `LLMProvider` and `Any`) actually correct?**
  _`LLMProvider` has 159 INFERRED edges - model-reasoned connections that need verification._
- **Are the 129 inferred relationships involving `Settings` (e.g. with `LLMProvider` and `AsyncEngine`) actually correct?**
  _`Settings` has 129 INFERRED edges - model-reasoned connections that need verification._
- **Are the 74 inferred relationships involving `Claim` (e.g. with `AsyncEngine` and `BaseTourEvent`) actually correct?**
  _`Claim` has 74 INFERRED edges - model-reasoned connections that need verification._