# Graph Report - CodebaseArchiologist  (2026-07-17)

## Corpus Check
- 210 files · ~114,575 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1961 nodes · 5072 edges · 111 communities (93 shown, 18 thin omitted)
- Extraction: 64% EXTRACTED · 36% INFERRED · 0% AMBIGUOUS · INFERRED: 1850 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f9c00303`
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
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_detect_quality_opportunities|detect_quality_opportunities]]
- [[_COMMUNITY_graph_query.py|graph_query.py]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_RAG Phase Ladder — README|RAG Phase Ladder — README]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY_._refs_non_empty|._refs_non_empty]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY_._refs_non_empty|._refs_non_empty]]
- [[_COMMUNITY___init__.py|__init__.py]]
- [[_COMMUNITY_test_evals_imports.py|test_evals_imports.py]]
- [[_COMMUNITY_styles.d.ts|styles.d.ts]]
- [[_COMMUNITY_Cartographer|Cartographer]]
- [[_COMMUNITY_Contribute Elicitation|Contribute Elicitation]]
- [[_COMMUNITY_Flow Tracer|Flow Tracer]]
- [[_COMMUNITY_Intent Router|Intent Router]]
- [[_COMMUNITY_Community 131|Community 131]]
- [[_COMMUNITY_test_qa_multi_query.py|test_qa_multi_query.py]]
- [[_COMMUNITY_patched_carto_tools|patched_carto_tools]]

## God Nodes (most connected - your core abstractions)
1. `IntentProfile` - 163 edges
2. `LLMProvider` - 155 edges
3. `Settings` - 120 edges
4. `Message` - 84 edges
5. `Claim` - 82 edges
6. `Claim` - 82 edges
7. `CapabilityPlan` - 66 edges
8. `CodeRef` - 60 edges
9. `BaseTourEvent` - 51 edges
10. `Insight` - 45 edges

## Surprising Connections (you probably didn't know these)
- `RedisSettings` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `Any` --uses--> `IntentProfile`  [INFERRED]
  apps/api/src/repopilot_api/models.py → packages/agents/src/repopilot_agents/state.py
- `Any` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `WorkerSettings` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `CreateRepoRequest` --uses--> `IntentProfile`  [INFERRED]
  apps/api/src/repopilot_api/models.py → packages/agents/src/repopilot_agents/state.py

## Import Cycles
- 1-file cycle: `apps/api/src/repopilot_api/app.py -> apps/api/src/repopilot_api/app.py`

## Communities (111 total, 18 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (116): AppServices, Any, TourEventType, AsyncEngine, BaseTourEvent, ChunkPayload, CodeRef, IntentProfile (+108 more)

### Community 1 - "Community 1"
Cohesion: 0.13
Nodes (10): AST, AsyncFunctionDef, Call, ClassDef, FunctionDef, Import, ImportFrom, Walk one module and emit edges into typed lists.      Scope tracking is minimal (+2 more)

### Community 2 - "Community 2"
Cohesion: 0.07
Nodes (36): api, ChunkPayload, ClaimEvent, ClaimStatus, CodeRef, CreateRepoResponse, CreateTourResponse, DiagramEvent (+28 more)

### Community 3 - "Community 3"
Cohesion: 0.08
Nodes (44): Node, Path, Path, Any, Path, _class_base_names(), _class_method_names(), _decorators() (+36 more)

### Community 4 - "Community 4"
Cohesion: 0.29
Nodes (7): ModelBinding, ModelId, ProviderName, Logical model identifiers and their physical-model resolution per provider.  Age, Logical, agent-facing model identifiers., The concrete model name to send to a given provider for one `ModelId`., StrEnum

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (32): _build_fact_bundle_for_test(), _fact_bundle(), Cartographer — produces ``system_map`` Insights from the call graph.  The Cartog, Run the Cartographer once.      Returns the state diff for the LangGraph reducer, Render the fact bundle as a compact text block.      We deliberately avoid prose, Resolve each symbol's CodeRef from graph_metrics's underlying lookup.      The m, _refs_for_symbols(), _resolve_refs() (+24 more)

### Community 6 - "Community 6"
Cohesion: 0.06
Nodes (42): ChunkHit, AsyncEngine, ChunkHit, AsyncEngine, ChunkHit, LLMProvider, Any, ChunkHit (+34 more)

### Community 7 - "Community 7"
Cohesion: 0.16
Nodes (22): approachability_score(), Lane A — issue triage backed by graph approachability., Score issue approachability from graph facts, not GitHub labels., Rank issues and keep the next three rejected reasons., _ref_for_issue(), run_lane_a_triage(), triage_issues(), Issue (+14 more)

### Community 8 - "Community 8"
Cohesion: 0.08
Nodes (45): _extract_openai_compatible_text(), RateLimitError, Extract assistant text from OpenAI-compatible payload variants.      Some provid, HTTP 429 from a provider — triggers retry/fallback inside the provider.      ``r, Shared fixtures for the core package's tests., Any, EmbeddingResponse, ModelBinding (+37 more)

### Community 9 - "Community 9"
Cohesion: 0.08
Nodes (25): dependencies, next, react, react-dom, devDependencies, lighthouse, @playwright/test, @types/node (+17 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (21): IntentProfileEvalRow, Path, PlannerEvalRow, dataset_path(), FileMappingEvalRow, IntentProfileEvalRow, load_file_mapping_dataset(), load_grounding_dataset() (+13 more)

### Community 11 - "Community 11"
Cohesion: 0.08
Nodes (28): Path, AsyncEngine, ChunkHit, LLMProvider, Any, RAG Phase 1: ``vector_search`` pool widening + metadata filters.  The pgvector S, _RecordingConn, _RecordingEngine (+20 more)

### Community 12 - "Community 12"
Cohesion: 0.18
Nodes (13): Any, index_repo(), arq worker function for the Phase 1 ingestion pipeline.  The actual pipeline log, Build arq RedisSettings from Settings.redis_url.      Without this, arq falls ba, arq job: index a GitHub repo end-to-end. Returns a JSON-able status dict., arq discovery target. Run with: ``arq repopilot_api.jobs.index_repo.WorkerSettin, _redis_settings_from_url(), shutdown() (+5 more)

### Community 13 - "Community 13"
Cohesion: 0.23
Nodes (13): Any, MonkeyPatch, CodeRef, Pointer into the repo. Every factual claim must carry at least one., The semaphore must cap in-flight verifier calls at max_concurrency., _StubEngine, _StubProvider, test_verify_claim_parse_fail_rejects() (+5 more)

### Community 14 - "Community 14"
Cohesion: 0.12
Nodes (29): _derive_ranker_weights(), _infer_flow_targets(), _infer_shape(), _pick_hub_bias(), plan(), Capability Planner — deterministic ``IntentProfile`` → ``CapabilityPlan``.  The, Deterministic planner. See ``docs/03_ARCHITECTURE.md`` § "The     Capability Pla, Pick a hub-bias tilt for the Cartographer.      Data-heavy intents → "data_hubs" (+21 more)

### Community 15 - "Community 15"
Cohesion: 0.12
Nodes (21): EmbeddedChunk, AsyncEngine, Settings, AsyncEngine, Settings, known_head_sha(), make_engine(), persist_index() (+13 more)

### Community 16 - "Community 16"
Cohesion: 0.30
Nodes (11): ChunkContent, _clip_ranges(), compress_chunk(), compress_chunks(), _compression_user_prompt(), _merge_ranges(), _parse_keep_ranges(), Phase 5 context compression: keep the answerer's view lean, not the verifier's. (+3 more)

### Community 17 - "Community 17"
Cohesion: 0.15
Nodes (24): detect_quality_opportunities(), _difficulty(), QualityCandidate, Lane B — deterministic code-health opportunities., Transform deterministic detector hits into unified opportunities., run_lane_b_quality(), IntentProfile, Opportunity (+16 more)

### Community 18 - "Community 18"
Cohesion: 0.11
Nodes (33): ArchaeologistState, BaseException, Any, AsyncEngine, LLMProvider, Any, build_graph(), _capability_planner_node() (+25 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (20): 01 — Problem and Solution, Fine-grained mapping: example stated intents → what the Capability Planner picks, Four concrete walkthroughs (out of infinitely many possible), Hard scope fence — what v1 will NOT do, How the flow handles "hard-to-context-map" responses, Key features (at a glance), Success criteria, The core bet (+12 more)

### Community 20 - "Community 20"
Cohesion: 0.11
Nodes (18): 03 — Architecture, Agent table, Agent topology, Capability dependencies, Deterministic tools, Eval harness vs. product runtime — a hard line, Failure modes and cost design, Hybrid retrieval pattern (the Q&A spine) (+10 more)

### Community 21 - "Community 21"
Cohesion: 0.05
Nodes (65): AsyncEngine, ChunkContent, ChunkHit, Claim, LLMProvider, QuerySpec, ChunkContent, Any (+57 more)

### Community 22 - "Community 22"
Cohesion: 0.18
Nodes (16): MonkeyPatch, Path, GroundingEvalRow, _async_return(), _dataset_path(), _DummyContext, _DummyEngine, _DummyProvider (+8 more)

### Community 23 - "Community 23"
Cohesion: 0.20
Nodes (19): CloneResult, ModuleSource, Chunk, LLMProvider, Path, Settings, Chunk, One indexable unit of source. Line numbers are 1-based, inclusive. (+11 more)

### Community 24 - "Community 24"
Cohesion: 0.10
Nodes (20): compilerOptions, allowImportingTsExtensions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib (+12 more)

### Community 25 - "Community 25"
Cohesion: 0.13
Nodes (14): GroundingEvalRow, CodeRef, QAResult, Settings, _contains_all_keywords(), GroundingEvalCaseResult, GroundingEvalMetrics, _has_expected_refs() (+6 more)

### Community 26 - "Community 26"
Cohesion: 0.12
Nodes (16): Agent Graph, API Surface, Architecture At A Glance, Current Build State, Design Principles, Development Workflow, Documentation Map, Graph Connections That Matter (+8 more)

### Community 27 - "Community 27"
Cohesion: 0.19
Nodes (17): EvalSpec, GroundingEvalMetrics, Namespace, Path, _cmd_list(), _cmd_status(), _grounding_markdown(), main() (+9 more)

### Community 28 - "Community 28"
Cohesion: 0.13
Nodes (22): Path, ParsedFile, ParsedSymbol, _build_enriched_text(), chunk_file(), _class_header_content(), _class_header_end_line(), enrich_chunks_with_neighbors() (+14 more)

### Community 29 - "Community 29"
Cohesion: 0.15
Nodes (22): _coerce_section(), _collect_refs(), _format_source_bundle(), Teacher — weaves Insights into goal-anchored ``TourSection``s.  The Teacher is t, Run the Teacher once.      Returns ``{"draft_tour": [TourSection, …]}``. Empty l, Index every CodeRef from upstream insights by symbol so the Teacher     can only, run_teacher(), CapabilityPlan (+14 more)

### Community 30 - "Community 30"
Cohesion: 0.19
Nodes (19): CapabilityPlan, IntentProfile, _format_active(), _format_keywords(), _format_tilt_line(), _format_weights(), Goal-anchor prompt block — shared across every generation node.  Every generatio, Render the goal-anchor block for the given (profile, plan) pair.      Output is (+11 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (13): Any, ChunkContent, CodeRef, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, FakeChunk, FakeEngine, FakeProvider, make_content() (+5 more)

### Community 32 - "Community 32"
Cohesion: 0.29
Nodes (6): AsyncEngine, ChunkContent, CodeRef, ``read_chunks`` — the ONLY tool that returns source text.  Per Phase 2 decision, Fetch the content of every chunk whose ``(file_path, start_line, end_line)``, read_chunks()

### Community 33 - "Community 33"
Cohesion: 0.13
Nodes (16): Path, clone_to_tempdir(), parse_github_url(), GitHub clone + HEAD-SHA helpers for Phase 1 ingestion.  Two entry points:  * :fu, Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c, remote_head_sha() (+8 more)

### Community 34 - "Community 34"
Cohesion: 0.22
Nodes (14): coerce_claim(), coerce_insight(), _coerce_ref(), coerce_refs(), Shared LLM-output coercion helpers for capability nodes.  Every node asks the LL, Validate a ref. If the LLM names a symbol, prefer the known CodeRef     for that, Validate a single ``Insight`` payload. Returns ``None`` if any     required fiel, Any (+6 more)

### Community 35 - "Community 35"
Cohesion: 0.28
Nodes (14): build_graph(), ModuleSource, Resolved module info handed to the graph builder., Build a directed graph from a collection of Python module sources.      Nodes ar, Every node carries all six bucket keys, even when empty.      Phase 2's determin, test_adjacency_keys_are_stable(), Graph-builder tests — call / import / inherit edges from a synthetic repo., Multi-module path: A.run -> B.helper. Phase 2's tools build on this. (+6 more)

### Community 36 - "Community 36"
Cohesion: 0.10
Nodes (33): IntentProfile, CapabilityPlan, IntentProfile, Any, CodeRef, MonkeyPatch, TourSection, ArchaeologistState (+25 more)

### Community 37 - "Community 37"
Cohesion: 0.20
Nodes (16): CodeRef, QAExchange, One completed Q&A turn. v1 keeps the last 8; the prompt only consumes     the cu, Validator tests for ``ArchaeologistState`` and its sub-models.  These tests pin, _ref(), test_claim_defaults_unverified(), test_claim_rejects_relevance_out_of_unit_interval(), test_claim_requires_at_least_one_ref() (+8 more)

### Community 38 - "Community 38"
Cohesion: 0.07
Nodes (46): AsyncEngine, DiGraph, AsyncEngine, SymbolMetrics, AsyncEngine, DiGraph, GraphQueryResult, AsyncEngine (+38 more)

### Community 39 - "Community 39"
Cohesion: 0.15
Nodes (15): ChunkContent, CodeRef, ChunkContent, MonkeyPatch, attribute_refs(), Claim → ref attribution via the Phase 4 cross-encoder.  The verifier judges each, Return the refs of the ``k`` chunks most relevant to ``claim_text``.      Best-f, _chunk() (+7 more)

### Community 40 - "Community 40"
Cohesion: 0.28
Nodes (4): Layout, Read in order (cold pickup), RepoPilot — Docs, The one-paragraph story

### Community 41 - "Community 41"
Cohesion: 0.31
Nodes (9): MonkeyPatch, Decide whether ``repo_url`` is already-current, stale, or unknown.      Cheap —, revisit_status(), Idempotency + staleness — exercised against a stubbed DB and stubbed clone.  The, When the remote HEAD has moved past the indexed SHA → status=stale., _StubEngine, test_revisit_unknown_repo_returns_stale(), test_revisit_with_advanced_remote_returns_stale_status() (+1 more)

### Community 42 - "Community 42"
Cohesion: 0.19
Nodes (11): build_opportunity_briefing(), ranker_rationale(), Teacher-facing briefing helpers for Phase 5 opportunity cards., Attach the UI-visible Phase 5 briefing surfaces without reranking., Plain-English explanation of planner-derived ranker weights., CapabilityPlan, IntentProfile, Opportunity (+3 more)

### Community 43 - "Community 43"
Cohesion: 0.14
Nodes (9): Animal, Dog, Kennel, login(), Fixture file the chunker tests assert against. Real Python so AST is exact., A base class with one method., A subclass overriding speak()., Validate session csrf redirect. (+1 more)

### Community 44 - "Community 44"
Cohesion: 0.31
Nodes (10): Settings, VerifierEvalRow, Eval runners for the phase gates., _patched_read_chunks(), Verifier-quality eval runner for the Phase 2 gate., run_verifier_eval(), run_verifier_eval_rows(), VerifierEvalCaseResult (+2 more)

### Community 45 - "Community 45"
Cohesion: 0.21
Nodes (13): CrossEncoderReranker, ChunkContent, ChunkHit, _hit_and_content(), RAG Phase 4: cross-encoder wrapper + rerank pipeline (stubbed encoder).  The rea, Scores by keyword overlap with the query; counts calls., reranker(), _StubEncoder (+5 more)

### Community 46 - "Community 46"
Cohesion: 0.21
Nodes (10): Module, DiGraph, _DefSymbol, graph_to_adjacency(), NetworkX dependency graph builder.  Edges (Phase 1, deterministic — the LLM neve, Serialise to the JSONB sidecar shape stored in ``graph_adjacency``.      ``{node, _walk_definitions(), Tests for ``graph_to_adjacency`` — JSONB sidecar shape Phase 2 will read. (+2 more)

### Community 47 - "Community 47"
Cohesion: 0.17
Nodes (12): ChunkContent, ChunkContent, ChunkHit, Cross-encoder reranker over (query, chunk) pairs via ``fastembed``.  Unlike the, The text the cross-encoder sees for one chunk (symbol-prefixed)., Process-wide reranker so the ONNX model loads once., rerank_text(), shared_reranker() (+4 more)

### Community 48 - "Community 48"
Cohesion: 0.21
Nodes (13): jaccard(), mmr_select(), Maximal Marginal Relevance — diversity-aware top-k selection (pure).  ``MMR(c) =, Return indices of up to ``k`` items, MMR-ordered (pure function).      ``relevan, _tokens(), RAG Phase 4: MMR diversity selection (pure function)., test_constant_relevance_normalises_safely(), test_empty_and_zero_k() (+5 more)

### Community 49 - "Community 49"
Cohesion: 0.27
Nodes (9): Any, ChunkContent, _chunk(), Phase 5 compression tests: safe parsing, clipping, and answerer-only view., _StubProvider, test_answer_prompt_uses_compressed_view_only(), test_compress_chunk_falls_back_on_invalid_json(), test_compress_chunk_keeps_clipped_merged_ranges() (+1 more)

### Community 50 - "Community 50"
Cohesion: 0.22
Nodes (13): Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)., test_parse_verdict_accepts_clean_json(), test_parse_verdict_extracts_json_from_prose(), test_parse_verdict_ignores_decoy_json_without_decision(), test_parse_verdict_returns_none_on_garbage(), test_parse_verdict_returns_none_on_invalid_decision(), test_parse_verdict_returns_none_when_only_think_block(), test_parse_verdict_strips_closed_think_block() (+5 more)

### Community 51 - "Community 51"
Cohesion: 0.17
Nodes (9): Settings, take_rows(), LatencyEvalMetrics, percentile(), Latency runner: p50/p95 wall-clock timings around ``answer_question``., Nearest-rank percentile over a pre-sorted list., run_latency_eval(), T (+1 more)

### Community 52 - "Community 52"
Cohesion: 0.25
Nodes (10): lane_c_language_violation(), _matches_focus(), Lane C — guarded structural suspicions., Return the banned phrase when Lane C language is too certain., Build guarded suspicion opportunities from deterministic candidates.      Phase, run_lane_c_suspicion(), CodeRef, IntentProfile (+2 more)

### Community 53 - "Community 53"
Cohesion: 0.15
Nodes (12): 02 — Tech Stack, ASCII full-stack diagram, Backend layer, Code intelligence layer (deterministic, NO LLM), Frontend layer, Groq free-tier survival strategy, LLM layer, Orchestration layer (+4 more)

### Community 54 - "Community 54"
Cohesion: 0.14
Nodes (26): _coerce_keywords(), _coerce_modality_weights(), _coerce_optional_str(), _coerce_output_shape(), _fallback_profile(), _parse_json(), profile_intent(), Intent Profiler — free-text intent → structured ``IntentProfile``.  The Profiler (+18 more)

### Community 55 - "Community 55"
Cohesion: 0.25
Nodes (4): paired_bootstrap(), Paired bootstrap significance test between two metric arrays.  Used by every pha, SignificanceResult, TestSignificance

### Community 56 - "Community 56"
Cohesion: 0.27
Nodes (7): Any, ChunkContent, _chunk(), Phase 5 safety invariant: verifier must always see the full chunk content.  The, _StubProvider, test_compress_chunks_runs_in_parallel_and_handles_errors(), test_verifier_sees_full_content_after_compression()

### Community 57 - "Community 57"
Cohesion: 0.39
Nodes (8): _lane_weight(), opportunity_score(), rank_opportunities(), Deterministic Phase 5 opportunity ranker., Compute a deterministic weighted score for one opportunity., Return opportunities in stable best-first order. No LLM reranking., CapabilityPlan, Opportunity

### Community 58 - "Community 58"
Cohesion: 0.25
Nodes (7): EventDict, Any, configure_logging(), _drop_chunk_content(), Structlog setup: JSON renderer in prod/CI, human-friendly renderer in dev/tests., Strip any field carrying raw repo content. Logs must never persist source code., Wire up structlog. Idempotent — safe to call from app startup and from tests.

### Community 59 - "Community 59"
Cohesion: 0.28
Nodes (5): Any, MonkeyPatch, CrossEncoderReranker, Lazy-loading, score-caching wrapper around ``fastembed.TextCrossEncoder``., Relevance score per text (higher = more relevant). Cached per pair.

### Community 60 - "Community 60"
Cohesion: 0.08
Nodes (29): ChunkHit, CodeRef, QuerySpec, Settings, CodeRef, _apply_rerank(), mrr(), ndcg_at_k() (+21 more)

### Community 61 - "Community 61"
Cohesion: 0.32
Nodes (5): Any, Path, _chunk(), FailingProvider, test_summarise_chunks_opens_circuit_after_provider_failure()

### Community 62 - "Community 62"
Cohesion: 0.67
Nodes (3): How the intent profile flows through the system, Q&A multi-turn (schema-reserved in v1, surfaced post-v0.1), What "always-on" means for Q&A specifically

### Community 63 - "Community 63"
Cohesion: 0.29
Nodes (10): Any, Path, _coerce(), _ensure_reports_dir(), find_latest_report(), _now_stamp(), Persisted eval reports.  Each eval run writes a timestamped JSON + Markdown pair, Write a JSON + Markdown report pair. Returns ``(json_path, md_path)``. (+2 more)

### Community 67 - "Community 67"
Cohesion: 0.33
Nodes (11): Path, aggregate(), bench_repo(), main(), Top-level RAG-phase bench runner.  Usage::      uv run python -m repopilot_evals, Compare ``_after`` to ``_before`` per repo; fail on guardrail breaches.      Gua, Gate sanity check: baseline vs itself must be 'not significant'., results_dir() (+3 more)

### Community 68 - "Community 68"
Cohesion: 0.22
Nodes (9): 1. What this project is, 2. How project knowledge is organized, 3. Knowledge Graph first (Graphify), 4. Graph maintenance (mandatory), 5. Codex harness (`.Codex/`), 6. Engineering conventions, 7. Definition of Done, 8. For contributors (human or AI) (+1 more)

### Community 69 - "Community 69"
Cohesion: 0.22
Nodes (9): 1. What this project is, 2. How project knowledge is organized, 3. Knowledge Graph first (Graphify), 4. Graph maintenance (mandatory), 5. Claude Code harness (`.claude/`), 6. Engineering conventions, 7. Definition of Done, 8. For contributors (human or AI) (+1 more)

### Community 70 - "Community 70"
Cohesion: 0.09
Nodes (19): LangGraph nodes + capability library.  Phase 2 surface: the six deterministic to, ChunkContent, ChunkHit, GraphQueryResult, Path, Shared Pydantic types used across tools, verifier, and Q&A.  These are the typed, Result of ``read_chunks``: a CodeRef paired with the source text it points at., Result of ``vector_search``: a chunk with retrieval metadata. (+11 more)

### Community 71 - "Community 71"
Cohesion: 0.08
Nodes (17): Alembic environment — uses Settings.postgres_dsn so dev + CI agree., Path, Shared core: settings, logging, and the LLMProvider abstraction., _find_repo_env(), Application settings, loaded from environment / `.env` via pydantic-settings., Walk up from this file to the repo root and return the ``.env`` path.      Lets, Parse a comma-separated env var into a cleaned list., _split_csv() (+9 more)

### Community 78 - "Community 78"
Cohesion: 0.08
Nodes (55): ClaimStatus, AsyncEngine, Claim, IntentProfile, LLMProvider, TourSection, Any, CodeRef (+47 more)

### Community 80 - "Community 80"
Cohesion: 0.42
Nodes (8): Path, accept_row(), load(), main(), Terminal review loop for candidate eval labels (Phase 0, Option A).  Walks every, review(), save(), show_row()

### Community 84 - "Community 84"
Cohesion: 0.15
Nodes (12): 1. Install Dependencies, 2. Configure Environment, 3. Start Local Services, 4. Run The App, 6. Use The App Locally, 7. Run Checks, 8. Graph Maintenance, Commands You Actually Use (+4 more)

### Community 85 - "Community 85"
Cohesion: 0.09
Nodes (43): BaseSettings, IntentClass, EmbeddingResponse, LLMProvider, Message, ProviderError, Provider-agnostic embedding shape., Single entrypoint to every LLM call in the system. (+35 more)

### Community 86 - "Community 86"
Cohesion: 0.29
Nodes (6): Authoring, Engineering conventions, Graph maintenance (mandatory), Knowledge graph first, RepoPilot — Project Rules (portable), What this project is

### Community 89 - "Community 89"
Cohesion: 0.50
Nodes (4): Path, _iter_source_files(), Hard CI rule: nothing in the source tree may branch on a ``purpose`` enum.  Phas, test_no_purpose_enum_in_source_tree()

### Community 92 - "detect_quality_opportunities"
Cohesion: 0.50
Nodes (3): Constraints, Mandatory order of operations, What to return

### Community 104 - "Community 104"
Cohesion: 0.19
Nodes (15): _apply(), _Cache, _objection_if_rejected(), Per-claim grounding check against ``read_chunks``.  The Verifier is the single l, Test helper — clear the verifier verdict cache., Verify one claim. Updates ``claim.status`` and ``claim.verifier_note`` in place., Verify N claims concurrently, bounded to avoid 429 stampedes (M1).      ``max_co, The structured response we require from the verifier model. (+7 more)

### Community 111 - "._refs_non_empty"
Cohesion: 0.29
Nodes (6): Cumulative Picture, Deferred Entry States, Executive Status, Permanent Regression Gate, Phase Scorecard, RAG Ship Report

### Community 118 - "Contribute Elicitation"
Cohesion: 0.08
Nodes (31): Connection, _backoff_delay(), _BaseClient, _cache_key(), LLMResponse, _OpenAICompatibleClient, _parse_retry_after(), The single LLMProvider every agent goes through.  Responsibilities (Phase 0 deli (+23 more)

### Community 131 - "Community 131"
Cohesion: 0.50
Nodes (4): Iteration 1 — Contribute lanes, in detail, Lane A — Issue Triage, Lane B — Quality Scanner, Lane C — Suspicion Scanner

### Community 141 - "test_qa_multi_query.py"
Cohesion: 0.33
Nodes (6): ChunkHit, MonkeyPatch, _hit(), Fast-lane tests for Phase 2 multi-query retrieval fan-out., test_initial_retrieval_applies_single_extracted_path(), test_initial_retrieval_fuses_rewrite_lanes()

### Community 144 - "patched_carto_tools"
Cohesion: 0.17
Nodes (25): extract_json_list(), Pull the first JSON array out of ``raw`` and return it as a list of     dicts. R, CapabilityPlan, IntentProfile, MonkeyPatch, _insight(), patched_carto_tools(), patched_traverse() (+17 more)

## Knowledge Gaps
- **212 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `type` (+207 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMProvider` connect `Community 85` to `Community 0`, `Community 36`, `Community 5`, `Community 6`, `Community 8`, `Community 104`, `Community 11`, `Community 12`, `Community 78`, `Community 15`, `Community 16`, `patched_carto_tools`, `Community 18`, `Community 21`, `Contribute Elicitation`, `Community 23`, `Community 54`, `Community 29`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 85` to `Community 0`, `Community 3`, `Community 71`, `Community 8`, `Community 44`, `Community 12`, `Community 15`, `Community 51`, `Contribute Elicitation`, `Community 23`, `Community 25`, `Community 60`, `Community 61`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Why does `IntentProfile` connect `Community 29` to `Community 0`, `Community 36`, `Community 5`, `Community 37`, `Community 7`, `Community 42`, `Community 78`, `Community 14`, `patched_carto_tools`, `Community 17`, `Community 18`, `Community 52`, `Community 85`, `Community 54`, `Community 30`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 147 inferred relationships involving `IntentProfile` (e.g. with `Any` and `TourEventType`) actually correct?**
  _`IntentProfile` has 147 INFERRED edges - model-reasoned connections that need verification._
- **Are the 147 inferred relationships involving `LLMProvider` (e.g. with `Any` and `AsyncEngine`) actually correct?**
  _`LLMProvider` has 147 INFERRED edges - model-reasoned connections that need verification._
- **Are the 113 inferred relationships involving `Settings` (e.g. with `AsyncEngine` and `BaseTourEvent`) actually correct?**
  _`Settings` has 113 INFERRED edges - model-reasoned connections that need verification._
- **Are the 75 inferred relationships involving `Message` (e.g. with `ClaimStatus` and `IntentClass`) actually correct?**
  _`Message` has 75 INFERRED edges - model-reasoned connections that need verification._