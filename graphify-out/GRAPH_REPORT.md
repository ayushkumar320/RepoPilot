# Graph Report - RepoPilot  (2026-08-04)

## Corpus Check
- 217 files · ~128,285 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2155 nodes · 5659 edges · 122 communities (101 shown, 21 thin omitted)
- Extraction: 64% EXTRACTED · 36% INFERRED · 0% AMBIGUOUS · INFERRED: 2053 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e55bb060`
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
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 91|Community 91]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]
- [[_COMMUNITY_Community 108|Community 108]]
- [[_COMMUNITY_Community 109|Community 109]]
- [[_COMMUNITY_Community 110|Community 110]]
- [[_COMMUNITY_Community 111|Community 111]]
- [[_COMMUNITY_Community 114|Community 114]]
- [[_COMMUNITY_Community 120|Community 120]]
- [[_COMMUNITY_Community 121|Community 121]]
- [[_COMMUNITY_Community 127|Community 127]]
- [[_COMMUNITY_Community 132|Community 132]]

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
- `AccountUsage` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/access.py → packages/core/src/repopilot_core/llm/provider.py
- `UsageReservation` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/access.py → packages/core/src/repopilot_core/llm/provider.py

## Import Cycles
- 1-file cycle: `apps/api/src/repopilot_api/app.py -> apps/api/src/repopilot_api/app.py`

## Communities (122 total, 21 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.14
Nodes (12): EventDict, Any, create_app(), FastAPI app for the Phase 4 API contract., FastAPI app entrypoint. Endpoints are added in Phase 4., configure_logging(), _drop_chunk_content(), Structlog setup: JSON renderer in prod/CI, human-friendly renderer in dev/tests. (+4 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (60): ClaimStatus, AsyncEngine, Claim, IntentProfile, LLMProvider, TourSection, CodeRef, Any (+52 more)

### Community 2 - "Community 2"
Cohesion: 0.05
Nodes (133): LLMProvider, Any, TourEventType, AsyncEngine, BaseTourEvent, ChunkPayload, CodeRef, GraphQueryResult (+125 more)

### Community 3 - "Community 3"
Cohesion: 0.16
Nodes (28): Node, Parser, _class_base_names(), _class_method_names(), _decorators(), _docstring_tokens(), _extract_imports(), _extract_symbols() (+20 more)

### Community 4 - "Community 4"
Cohesion: 0.27
Nodes (5): LatencyEvalMetrics, Per-stage latency breakdown — the point of P1 instrumentation., A stage the pipeline skipped (no rerank, no hops) is not an error., Old artifacts with no stage data still serialize cleanly., TestStageAttribution

### Community 5 - "Community 5"
Cohesion: 0.05
Nodes (48): AccountUsage, api, ApiError, ChunkPayload, ClaimEvent, ClaimStatus, CodeRef, CreateRepoResponse (+40 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (44): ChunkHit, AsyncEngine, ChunkHit, AsyncEngine, ChunkHit, LLMProvider, Any, ChunkHit (+36 more)

### Community 7 - "Community 7"
Cohesion: 0.11
Nodes (38): approachability_score(), Lane A — issue triage backed by graph approachability., Score issue approachability from graph facts, not GitHub labels., Rank issues and keep the next three rejected reasons., _ref_for_issue(), run_lane_a_triage(), triage_issues(), detect_quality_opportunities() (+30 more)

### Community 8 - "Community 8"
Cohesion: 0.21
Nodes (11): Any, EmbeddingResponse, ModelBinding, BatchEmbedder, FakeEmbedder, Tests for ``LLMProvider.embed()`` — cache hit, fresh embed, dim contract., Test double — bypasses the sentence-transformers model load and     returns cann, test_embed_cache_hit_skips_provider() (+3 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (40): Path, Path, Path, Path, ParsedFile, ParsedSymbol, _build_enriched_text(), chunk_file() (+32 more)

### Community 10 - "Community 10"
Cohesion: 0.20
Nodes (8): LangGraph nodes + capability library.  Phase 2 surface: the six deterministic to, ChunkContent, GraphQueryResult, Shared Pydantic types used across tools, verifier, and Q&A.  These are the typed, Result of ``read_chunks``: a CodeRef paired with the source text it points at., Result of ``graph_metrics``: per-symbol metric pack., Result of ``graph_query``: one row of an entry-points / hubs / layers query., SymbolMetrics

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (22): AsyncEngine, ChunkHit, LLMProvider, Any, RAG Phase 1: ``vector_search`` pool widening + metadata filters.  The pgvector S, _RecordingConn, _RecordingEngine, _run() (+14 more)

### Community 12 - "Community 12"
Cohesion: 0.17
Nodes (31): RateLimitError, HTTP 429 from a provider — triggers retry/fallback inside the provider.      ``r, ProviderName, Message, FakeClient, make_provider(), make_response(), Build an LLMProvider that uses the supplied fakes for every provider. (+23 more)

### Community 13 - "Community 13"
Cohesion: 0.39
Nodes (8): _lane_weight(), opportunity_score(), rank_opportunities(), Deterministic Phase 5 opportunity ranker., Compute a deterministic weighted score for one opportunity., Return opportunities in stable best-first order. No LLM reranking., CapabilityPlan, Opportunity

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (29): _derive_ranker_weights(), _infer_flow_targets(), _infer_shape(), _pick_hub_bias(), plan(), Capability Planner — deterministic ``IntentProfile`` → ``CapabilityPlan``.  The, Deterministic planner. See ``docs/03_ARCHITECTURE.md`` § "The     Capability Pla, Pick a hub-bias tilt for the Cartographer.      Data-heavy intents → "data_hubs" (+21 more)

### Community 15 - "Community 15"
Cohesion: 0.23
Nodes (16): AppServices, BaseModel, FastAPI, ArchaeologistError, Every fail-edge in the graph emits one of these., AccountUsageResponse, AskTourRequest, CreateRepoRequest (+8 more)

### Community 16 - "Community 16"
Cohesion: 0.07
Nodes (29): dependencies, geist, next, @phosphor-icons/react, react, react-dom, devDependencies, lighthouse (+21 more)

### Community 17 - "Community 17"
Cohesion: 0.13
Nodes (24): IntentProfile, Any, CodeRef, MonkeyPatch, TourSection, ArchaeologistState, The single shared LangGraph state. See ``docs/03_ARCHITECTURE.md``., fake_engine() (+16 more)

### Community 18 - "Community 18"
Cohesion: 0.13
Nodes (22): QAExchange, One completed Q&A turn. v1 keeps the last 8; the prompt only consumes     the cu, Validator tests for ``ArchaeologistState`` and its sub-models.  These tests pin, _ref(), test_claim_defaults_unverified(), test_claim_rejects_relevance_out_of_unit_interval(), test_claim_requires_at_least_one_ref(), test_insight_accepts_complete_fields() (+14 more)

### Community 19 - "Community 19"
Cohesion: 0.17
Nodes (24): ArchaeologistState, Any, AsyncEngine, LLMProvider, build_graph(), _capability_planner_node(), _cartographer_node(), _flow_tracer_node() (+16 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (21): 03 — Architecture, Agent table, Agent topology, Capability dependencies, Deterministic tools, Eval harness vs. product runtime — a hard line, Failure modes and cost design, How the intent profile flows through the system (+13 more)

### Community 21 - "Community 21"
Cohesion: 0.09
Nodes (37): LLMProvider, Any, ChunkContent, CodeRef, MonkeyPatch, answer_question(), _Context, _estimate_tokens() (+29 more)

### Community 22 - "Community 22"
Cohesion: 0.18
Nodes (19): MonkeyPatch, Path, GroundingEvalRow, VerifierEvalRow, _async_return(), _dataset_path(), _DummyContext, _DummyEngine (+11 more)

### Community 23 - "Community 23"
Cohesion: 0.13
Nodes (27): _coerce_keywords(), _coerce_modality_weights(), _coerce_optional_str(), _coerce_output_shape(), _fallback_profile(), _parse_json(), profile_intent(), Intent Profiler — free-text intent → structured ``IntentProfile``.  The Profiler (+19 more)

### Community 24 - "Community 24"
Cohesion: 0.07
Nodes (25): Any, index_repo(), arq worker function for the Phase 1 ingestion pipeline.  The actual pipeline log, Build arq RedisSettings from Settings.redis_url.      Without this, arq falls ba, arq job: index a GitHub repo end-to-end. Returns a JSON-able status dict., arq discovery target. Run with: ``arq repopilot_api.jobs.index_repo.WorkerSettin, _redis_settings_from_url(), shutdown() (+17 more)

### Community 25 - "Community 25"
Cohesion: 0.13
Nodes (15): GroundingEvalRow, CodeRef, QAResult, Settings, _contains_all_keywords(), GroundingEvalCaseResult, GroundingEvalMetrics, _has_expected_refs() (+7 more)

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (16): Agent Graph, API Surface, Architecture At A Glance, Current Build State, Design Principles, Development Workflow, Documentation Map, Graph Connections That Matter (+8 more)

### Community 27 - "Community 27"
Cohesion: 0.17
Nodes (18): EvalSpec, GroundingEvalMetrics, Namespace, Path, _cmd_list(), _cmd_status(), _grounding_markdown(), main() (+10 more)

### Community 28 - "Community 28"
Cohesion: 0.08
Nodes (36): ChunkContent, LLMProvider, ChunkContent, Any, ChunkContent, Any, ChunkContent, _clip_ranges() (+28 more)

### Community 29 - "Community 29"
Cohesion: 0.33
Nodes (3): ndcg_at_k(), recall_at_k(), TestMetrics

### Community 30 - "Community 30"
Cohesion: 0.17
Nodes (20): lane_c_language_violation(), _matches_focus(), Lane C — guarded structural suspicions., Return the banned phrase when Lane C language is too certain., Build guarded suspicion opportunities from deterministic candidates.      Phase, run_lane_c_suspicion(), CodeRef, IntentProfile (+12 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (13): Any, ChunkContent, CodeRef, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, FakeChunk, FakeEngine, FakeProvider, make_content() (+5 more)

### Community 32 - "Community 32"
Cohesion: 0.23
Nodes (23): ModuleSource, Chunk, CloneResult, LLMProvider, Path, Settings, Chunk, One indexable unit of source. Line numbers are 1-based, inclusive. (+15 more)

### Community 33 - "Community 33"
Cohesion: 0.17
Nodes (20): Chunk, Path, CloneResult, MonkeyPatch, Path, chunk_text_file(), _context_language(), iter_generic_files() (+12 more)

### Community 34 - "Community 34"
Cohesion: 0.20
Nodes (20): AsyncEngine, DiGraph, GraphQueryResult, QueryKind, _prime_cache(), Tests for ``graph_query``: entry points, hubs, callers/callees, layers.  Exercis, test_callees_of_a(), test_callers_of_c() (+12 more)

### Community 35 - "Community 35"
Cohesion: 0.18
Nodes (9): _extract_openai_compatible_text(), _parse_retry_after(), Parse a ``Retry-After`` header (delta-seconds or HTTP-date) into seconds.      P, Extract assistant text from OpenAI-compatible payload variants.      Some provid, test_extract_openai_compatible_text_accepts_block_content(), test_extract_openai_compatible_text_accepts_string_content(), test_extract_openai_compatible_text_falls_back_to_choice_text(), test_extract_openai_compatible_text_raises_on_missing_text() (+1 more)

### Community 36 - "Community 36"
Cohesion: 0.10
Nodes (20): 01 — Problem and Solution, Fine-grained mapping: example stated intents → what the Capability Planner picks, Four concrete walkthroughs (out of infinitely many possible), Hard scope fence — what v1 will NOT do, How the flow handles "hard-to-context-map" responses, Key features (at a glance), Success criteria, The core bet (+12 more)

### Community 37 - "Community 37"
Cohesion: 0.18
Nodes (10): ChunkHit, Path, Result of ``vector_search``: a chunk with retrieval metadata., Result of ``graph_traverse``: an ordered chain of CodeRefs., Validator tests for the shared Phase 2 types., test_chunk_hit_distance_must_be_non_negative(), test_coderef_accepts_equal_lines(), test_coderef_rejects_end_before_start() (+2 more)

### Community 38 - "Community 38"
Cohesion: 0.29
Nodes (9): Chunk, LLMProvider, Settings, embed_chunks(), _embed_items(), True batched embedding orchestration over repository chunks., Return a deterministic normalized vector when the local embedder rejects a chunk, Embed every chunk; results are returned in the same order as ``chunks``. (+1 more)

### Community 39 - "Community 39"
Cohesion: 0.15
Nodes (15): ChunkContent, CodeRef, ChunkContent, MonkeyPatch, attribute_refs(), Claim → ref attribution via the Phase 4 cross-encoder.  The verifier judges each, Return the refs of the ``k`` chunks most relevant to ``claim_text``.      Best-f, _chunk() (+7 more)

### Community 41 - "Community 41"
Cohesion: 0.11
Nodes (26): EmbeddedChunk, AsyncEngine, Chunk, LLMProvider, Message, Settings, delete_incomplete_index(), known_head_sha() (+18 more)

### Community 42 - "Community 42"
Cohesion: 0.10
Nodes (20): compilerOptions, allowImportingTsExtensions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib (+12 more)

### Community 43 - "Community 43"
Cohesion: 0.19
Nodes (19): CapabilityPlan, IntentProfile, _format_active(), _format_keywords(), _format_tilt_line(), _format_weights(), Goal-anchor prompt block — shared across every generation node.  Every generatio, Render the goal-anchor block for the given (profile, plan) pair.      Output is (+11 more)

### Community 44 - "Community 44"
Cohesion: 0.13
Nodes (15): Path, clone_to_tempdir(), parse_github_url(), GitHub clone + HEAD-SHA helpers for Phase 1 ingestion.  Two entry points:  * :fu, Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c, Phase 1 — clone -> parse -> chunk -> graph -> embed -> persist., Pure-logic tests around URL parsing and the revisit/staleness contract.  The net (+7 more)

### Community 45 - "Community 45"
Cohesion: 0.29
Nodes (6): _OpenAICompatibleClient, Speaks the OpenAI chat-completions shape. Used for Groq and Cerebras., Default wiring used by the app. Tests pass `clients` for full control., AsyncClient, Settings, Self

### Community 46 - "Community 46"
Cohesion: 0.07
Nodes (34): AST, AsyncFunctionDef, Call, ClassDef, FunctionDef, Import, ImportFrom, Module (+26 more)

### Community 47 - "Community 47"
Cohesion: 0.19
Nodes (13): build_query_spec(), fallback_query_spec(), _infer_intent(), _looks_multi_hop(), _merge_fallback_hints(), _normalize_paths(), _parse_query_spec(), QuerySpec (+5 more)

### Community 48 - "Community 48"
Cohesion: 0.14
Nodes (9): Animal, Dog, Kennel, login(), Fixture file the chunker tests assert against. Real Python so AST is exact., A base class with one method., A subclass overriding speak()., Validate session csrf redirect. (+1 more)

### Community 49 - "Community 49"
Cohesion: 0.21
Nodes (13): CrossEncoderReranker, ChunkContent, ChunkHit, _hit_and_content(), RAG Phase 4: cross-encoder wrapper + rerank pipeline (stubbed encoder).  The rea, Scores by keyword overlap with the query; counts calls., reranker(), _StubEncoder (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.13
Nodes (18): Connection, _cache_key(), _embedding_cache_key(), EmbeddingResponse, ProviderError, The single LLMProvider every agent goes through.  Responsibilities (Phase 0 deli, Provider-agnostic embedding shape., Thread-safe SQLite cache keyed on the canonical request hash. (+10 more)

### Community 51 - "Community 51"
Cohesion: 0.24
Nodes (8): BaseException, Any, _Provider, Tests for Phase 2 query understanding., test_build_query_spec_falls_back_on_parse_error(), test_build_query_spec_falls_back_on_provider_error(), test_build_query_spec_parses_json_and_preserves_raw_question(), test_retrieval_queries_dedupes_and_caps_rewrites()

### Community 52 - "Community 52"
Cohesion: 0.28
Nodes (5): Any, MonkeyPatch, CrossEncoderReranker, Lazy-loading, score-caching wrapper around ``fastembed.TextCrossEncoder``., Relevance score per text (higher = more relevant). Cached per pair.

### Community 53 - "Community 53"
Cohesion: 0.19
Nodes (12): Path, AsyncEngine, Settings, build_eval_context(), EvalContext, Shared runtime helpers for eval runners., resolve_repo_id(), _is_noise() (+4 more)

### Community 54 - "Community 54"
Cohesion: 0.14
Nodes (13): ChunkContent, ChunkContent, ChunkHit, Cross-encoder reranker over (query, chunk) pairs via ``fastembed``.  Unlike the, The text the cross-encoder sees for one chunk (symbol-prefixed)., Process-wide reranker so the ONNX model loads once., rerank_text(), shared_reranker() (+5 more)

### Community 55 - "Community 55"
Cohesion: 0.14
Nodes (22): IntentProfileEvalRow, Path, Settings, PlannerEvalRow, dataset_path(), FileMappingEvalRow, load_file_mapping_dataset(), load_grounding_dataset() (+14 more)

### Community 56 - "Community 56"
Cohesion: 0.21
Nodes (13): jaccard(), mmr_select(), Maximal Marginal Relevance — diversity-aware top-k selection (pure).  ``MMR(c) =, Return indices of up to ``k`` items, MMR-ordered (pure function).      ``relevan, _tokens(), RAG Phase 4: MMR diversity selection (pure function)., test_constant_relevance_normalises_safely(), test_empty_and_zero_k() (+5 more)

### Community 57 - "Community 57"
Cohesion: 0.19
Nodes (18): ChunkHit, CodeRef, QuerySpec, Settings, _apply_rerank(), mrr(), _query_lane_weights(), Pure-retrieval metrics: recall@k, NDCG@k, MRR over a labeled QA dataset.  Runs t (+10 more)

### Community 58 - "Community 58"
Cohesion: 0.24
Nodes (11): MonkeyPatch, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, remote_head_sha(), Decide whether ``repo_url`` is already-current, stale, or unknown.      Cheap —, revisit_status(), Idempotency + staleness — exercised against a stubbed DB and stubbed clone.  The, When the remote HEAD has moved past the indexed SHA → status=stale., _StubEngine (+3 more)

### Community 59 - "Community 59"
Cohesion: 0.15
Nodes (12): 02 — Tech Stack, ASCII full-stack diagram, Backend layer, Code intelligence layer (deterministic, NO LLM), Frontend layer, Groq free-tier survival strategy, LLM layer, Orchestration layer (+4 more)

### Community 60 - "Community 60"
Cohesion: 0.08
Nodes (42): AsyncEngine, ChunkContent, LLMProvider, Any, MonkeyPatch, CodeRef, Pointer into the repo. Every factual claim must carry at least one., Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1). (+34 more)

### Community 61 - "Community 61"
Cohesion: 0.33
Nodes (11): Path, aggregate(), bench_repo(), main(), Top-level RAG-phase bench runner.  Usage::      uv run python -m repopilot_evals, Compare ``_after`` to ``_before`` per repo; fail on guardrail breaches.      Gua, Gate sanity check: baseline vs itself must be 'not significant'., results_dir() (+3 more)

### Community 62 - "Community 62"
Cohesion: 0.23
Nodes (7): CodeRef, ref_matches(), Unit tests for the pure retrieval-metric math (no DB, no LLM)., _ref(), TestRefMatches, TestRelevanceVector, TestScoreCase

### Community 63 - "Community 63"
Cohesion: 0.25
Nodes (4): paired_bootstrap(), Paired bootstrap significance test between two metric arrays.  Used by every pha, SignificanceResult, TestSignificance

### Community 64 - "Community 64"
Cohesion: 0.31
Nodes (8): build_opportunity_briefing(), ranker_rationale(), Teacher-facing briefing helpers for Phase 5 opportunity cards., Attach the UI-visible Phase 5 briefing surfaces without reranking., Plain-English explanation of planner-derived ranker weights., CapabilityPlan, IntentProfile, Opportunity

### Community 65 - "Community 65"
Cohesion: 0.43
Nodes (7): Settings, _patched_read_chunks(), Verifier-quality eval runner for the Phase 2 gate., run_verifier_eval(), run_verifier_eval_rows(), VerifierEvalCaseResult, VerifierEvalRow

### Community 66 - "Community 66"
Cohesion: 0.42
Nodes (8): Path, accept_row(), load(), main(), Terminal review loop for candidate eval labels (Phase 0, Option A).  Walks every, review(), save(), show_row()

### Community 67 - "Community 67"
Cohesion: 0.27
Nodes (5): LatencyEvalMetrics, percentile(), Nearest-rank percentile over a pre-sorted list., Mean fraction of a question's total wall-clock spent in ``stage``.          Comp, TestPercentile

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
Cohesion: 0.12
Nodes (34): coerce_claim(), coerce_insight(), _coerce_ref(), coerce_refs(), extract_json_list(), Shared LLM-output coercion helpers for capability nodes.  Every node asks the LL, Pull the first JSON array out of ``raw`` and return it as a list of     dicts. R, Validate a ref. If the LLM names a symbol, prefer the known CodeRef     for that (+26 more)

### Community 73 - "Community 73"
Cohesion: 0.29
Nodes (6): Cumulative Picture, Deferred Entry States, Executive Status, Permanent Regression Gate, Phase Scorecard, RAG Ship Report

### Community 74 - "Community 74"
Cohesion: 0.29
Nodes (6): Authoring, Engineering conventions, Graph maintenance (mandatory), Knowledge graph first, RepoPilot — Project Rules (portable), What this project is

### Community 75 - "Community 75"
Cohesion: 0.08
Nodes (44): _build_fact_bundle_for_test(), _fact_bundle(), Cartographer — produces ``system_map`` Insights from the call graph.  The Cartog, Run the Cartographer once.      Returns the state diff for the LangGraph reducer, Render the fact bundle as a compact text block.      We deliberately avoid prose, Resolve each symbol's CodeRef from graph_metrics's underlying lookup.      The m, _refs_for_symbols(), _resolve_refs() (+36 more)

### Community 76 - "Community 76"
Cohesion: 0.18
Nodes (8): LLMResponse, Provider-agnostic response shape., Path, Settings, Shared fixtures for the core package's tests., FakeEmbedder, Test double for the sentence-transformers in-process embedder.      Returns dete, tmp_settings()

### Community 79 - "Community 79"
Cohesion: 0.50
Nodes (4): Path, _iter_source_files(), Hard CI rule: nothing in the source tree may branch on a ``purpose`` enum.  Phas, test_no_purpose_enum_in_source_tree()

### Community 80 - "Community 80"
Cohesion: 0.50
Nodes (3): Constraints, Mandatory order of operations, What to return

### Community 81 - "Community 81"
Cohesion: 0.50
Nodes (4): Layout, Read in order (cold pickup), RepoPilot — Docs, The one-paragraph story

### Community 82 - "Community 82"
Cohesion: 0.08
Nodes (42): _format_paths(), Flow Tracer — produces ``traced_flows`` Insights from call-graph paths.  Reads `, Choose which symbols to trace. Prefer the planner's explicit     targets; otherw, Run the Flow Tracer once.      Returns ``{"traced_flows": [Insight, …]}``. Empty, run_flow_tracer(), _seed_targets(), IntentClass, LLMProvider (+34 more)

### Community 83 - "Community 83"
Cohesion: 0.50
Nodes (4): Iteration 1 — Contribute lanes, in detail, Lane A — Issue Triage, Lane B — Quality Scanner, Lane C — Suspicion Scanner

### Community 84 - "Community 84"
Cohesion: 0.15
Nodes (13): 1. Install Dependencies, 2. Configure Environment, 3. Start Local Services, 4. Run The App, 6. Use The App Locally, 7. Run Checks, 8. Graph Maintenance, Commands You Actually Use (+5 more)

### Community 89 - "Community 89"
Cohesion: 0.29
Nodes (10): Any, Path, _coerce(), _ensure_reports_dir(), find_latest_report(), _now_stamp(), Persisted eval reports.  Each eval run writes a timestamped JSON + Markdown pair, Write a JSON + Markdown report pair. Returns ``(json_path, md_path)``. (+2 more)

### Community 90 - "Community 90"
Cohesion: 0.32
Nodes (5): Stages whose p95 grew most, worst first — the latency culprits.      Returns ``[, top_stage_regressions(), A latency breach must name the stage that caused it., Old _before.json has no stage keys — stay silent, don't invent a cause., TestTopStageRegressions

### Community 114 - "Community 114"
Cohesion: 0.05
Nodes (36): Alembic environment — uses Settings.postgres_dsn so dev + CI agree., AsyncEngine, DiGraph, AsyncEngine, SymbolMetrics, AsyncEngine, CodeRef, Path (+28 more)

### Community 120 - "Community 120"
Cohesion: 0.25
Nodes (7): Copy-paste prompt, Improved proposal for the chunking bottleneck, Proposed concurrency controls, Proposed fallback and rollout strategy, Proposed success thresholds, RepoPilot Ingestion Parallelization — Codex Execution Prompt, Suggested use

### Community 121 - "Community 121"
Cohesion: 0.16
Nodes (10): _backoff_delay(), _BaseClient, Exponential backoff with full jitter. attempt=0 is the first retry., Common interface for provider HTTP shims., In-process embedder using sentence-transformers (Hugging Face weights).      No, Per-binding 429 retry loop with exponential backoff + jitter., _SentenceTransformersEmbedder, Any (+2 more)

### Community 127 - "Community 127"
Cohesion: 0.40
Nodes (4): Production deployment, Release sequence, Required production environment, Service topology

### Community 132 - "Community 132"
Cohesion: 0.33
Nodes (6): ChunkHit, MonkeyPatch, _hit(), Fast-lane tests for Phase 2 multi-query retrieval fan-out., test_initial_retrieval_applies_single_extracted_path(), test_initial_retrieval_fuses_rewrite_lanes()

## Knowledge Gaps
- **230 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `type` (+225 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMProvider` connect `Community 82` to `Community 1`, `Community 2`, `Community 6`, `Community 11`, `Community 12`, `Community 17`, `Community 19`, `Community 21`, `Community 22`, `Community 23`, `Community 24`, `Community 28`, `Community 32`, `Community 38`, `Community 41`, `Community 45`, `Community 47`, `Community 50`, `Community 53`, `Community 60`, `Community 72`, `Community 75`, `Community 76`, `Community 121`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 2` to `Community 9`, `Community 12`, `Community 24`, `Community 25`, `Community 27`, `Community 32`, `Community 33`, `Community 38`, `Community 41`, `Community 45`, `Community 50`, `Community 53`, `Community 55`, `Community 57`, `Community 65`, `Community 67`, `Community 71`, `Community 76`, `Community 77`, `Community 82`, `Community 121`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `IntentProfile` connect `Community 1` to `Community 64`, `Community 2`, `Community 7`, `Community 72`, `Community 75`, `Community 43`, `Community 14`, `Community 15`, `Community 17`, `Community 82`, `Community 19`, `Community 18`, `Community 23`, `Community 30`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Are the 153 inferred relationships involving `IntentProfile` (e.g. with `Any` and `TourEventType`) actually correct?**
  _`IntentProfile` has 153 INFERRED edges - model-reasoned connections that need verification._
- **Are the 159 inferred relationships involving `LLMProvider` (e.g. with `LLMProvider` and `Any`) actually correct?**
  _`LLMProvider` has 159 INFERRED edges - model-reasoned connections that need verification._
- **Are the 129 inferred relationships involving `Settings` (e.g. with `LLMProvider` and `AsyncEngine`) actually correct?**
  _`Settings` has 129 INFERRED edges - model-reasoned connections that need verification._
- **Are the 74 inferred relationships involving `Claim` (e.g. with `AsyncEngine` and `BaseTourEvent`) actually correct?**
  _`Claim` has 74 INFERRED edges - model-reasoned connections that need verification._