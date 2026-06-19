# Graph Report - CodebaseArchiologist  (2026-06-19)

## Corpus Check
- 136 files · ~96,675 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1596 nodes · 4309 edges · 87 communities (70 shown, 17 thin omitted)
- Extraction: 60% EXTRACTED · 40% INFERRED · 0% AMBIGUOUS · INFERRED: 1723 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `43798aba`
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
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 42|Community 42]]
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
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 96|Community 96]]

## God Nodes (most connected - your core abstractions)
1. `IntentProfile` - 162 edges
2. `LLMProvider` - 145 edges
3. `Settings` - 94 edges
4. `ModelId` - 91 edges
5. `Claim` - 83 edges
6. `Message` - 78 edges
7. `CapabilityPlan` - 66 edges
8. `CodeRef` - 60 edges
9. `BaseTourEvent` - 50 edges
10. `Insight` - 45 edges

## Surprising Connections (you probably didn't know these)
- `Any` --uses--> `IntentProfile`  [INFERRED]
  apps/api/src/repopilot_api/models.py → packages/agents/src/repopilot_agents/state.py
- `Any` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `Any` --uses--> `PipelineResult`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/ingestion/src/repopilot_ingestion/pipeline.py
- `WorkerSettings` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `WorkerSettings` --uses--> `PipelineResult`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/ingestion/src/repopilot_ingestion/pipeline.py

## Import Cycles
- 1-file cycle: `apps/api/src/repopilot_api/app.py -> apps/api/src/repopilot_api/app.py`

## Communities (87 total, 17 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (12): ArchaeologistState, Cartographer, Contribute Elicitation, Flow Tracer, Intent Router, Learn Elicitation, Q&A Subgraph, Teacher (+4 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (25): 03 — Architecture, Agent table, Agent topology, Capability dependencies, Deterministic tools, Eval harness vs. product runtime — a hard line, Failure modes and cost design, How the intent profile flows through the system (+17 more)

### Community 2 - "Community 2"
Cohesion: 0.20
Nodes (9): 1. What this project is, 2. How project knowledge is organized, 3. Knowledge Graph first (Graphify), 4. Graph maintenance (mandatory), 5. Claude Code harness (`.claude/`), 6. Engineering conventions, 7. Definition of Done, 8. For contributors (human or AI) (+1 more)

### Community 3 - "Community 3"
Cohesion: 0.67
Nodes (3): Phase 1: Ingestion, NetworkX, tree-sitter

### Community 6 - "Community 6"
Cohesion: 0.14
Nodes (13): 00 — Claude Build Guide (Standing Context), Agent roster, Documentation layering — read in this order, every phase, Iteration 1 — Contribute = opportunity engine, not issue browser, Iteration 2 — No stat dumps. Output contract, enforced four ways., Per-PR Definition of Done, Pre-context capture runs IN PARALLEL with indexing — never after it, Project one-liner (+5 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (20): 01 — Problem and Solution, Fine-grained mapping: example stated intents → what the Capability Planner picks, Four concrete walkthroughs (out of infinitely many possible), Hard scope fence — what v1 will NOT do, How the flow handles "hard-to-context-map" responses, Key features (at a glance), Success criteria, The core bet (+12 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (12): 02 — Tech Stack, ASCII full-stack diagram, Backend layer, Code intelligence layer (deterministic, NO LLM), Frontend layer, Groq free-tier survival strategy, LLM layer, Orchestration layer (+4 more)

### Community 9 - "Community 9"
Cohesion: 0.18
Nodes (10): 04 — Build Plan, Per-PR Definition of Done, Phase 0 — Foundation, Phase 1 — Ingestion, Phase 2 — Hybrid Retrieval + Grounded Q&A (THE SPINE), Phase 3 — Orchestration + Learn subgraph, Phase 4 — Experience, Phase 5 — Contribute mode (Iteration 1) (+2 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (12): 05 — Phase Prompts (paste-ready), Phase 0 prompt — Foundation, Phase 1 — as built (post-merge addendum), Phase 1 prompt — Ingestion, Phase 2 — as built (post-merge addendum), Phase 2 — explicit deferrals (must clear before Phase 3 starts), Phase 2 — pre-build plan (decisions + build order), Phase 2 prompt — Hybrid Retrieval + Grounded Q&A (the spine) (+4 more)

### Community 13 - "Community 13"
Cohesion: 0.29
Nodes (6): Authoring, Engineering conventions, Graph maintenance (mandatory), Knowledge graph first, RepoPilot — Project Rules (portable), What this project is

### Community 14 - "Community 14"
Cohesion: 0.50
Nodes (3): Constraints, Mandatory order of operations, What to return

### Community 16 - "Community 16"
Cohesion: 0.16
Nodes (23): _coerce_keywords(), _coerce_modality_weights(), _coerce_optional_str(), _fallback_profile(), _parse_json(), profile_intent(), Intent Profiler — free-text intent → structured ``IntentProfile``.  The Profiler, The minimal-but-valid profile used when the LLM fails us.      Matches the "inte (+15 more)

### Community 17 - "Community 17"
Cohesion: 0.17
Nodes (11): 00 — Claude Build Guide (Standing Context) *(the contract)*, 01 — Problem and Solution *(the thesis / "why")*, 02 — Tech Stack *(the toolbox — every choice + why + what was rejected)*, 03 — Architecture *(the blueprint — the keystone doc)*, 04 — Build Plan *(the schedule — 7 phases, each with a hard gate)*, 05 — Phase Prompts *(the script — paste-ready)*, Build progress at a glance, How the doc set fits together (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.15
Nodes (24): AsyncEngine, ChunkContent, Claim, LLMProvider, answer_question(), _Context, _extend_context(), _generate_answer() (+16 more)

### Community 19 - "Community 19"
Cohesion: 0.28
Nodes (8): Any, index_repo(), arq worker function for the Phase 1 ingestion pipeline.  The actual pipeline log, arq job: index a GitHub repo end-to-end. Returns a JSON-able status dict., arq discovery target. Run with: ``arq repopilot_api.jobs.index_repo.WorkerSettin, shutdown(), startup(), WorkerSettings

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (20): compilerOptions, allowImportingTsExtensions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib (+12 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (25): dependencies, next, react, react-dom, devDependencies, lighthouse, @playwright/test, @types/node (+17 more)

### Community 22 - "Community 22"
Cohesion: 0.11
Nodes (17): Current Build Phase, How to advance the phase, Phase 0 — what landed, Phase 1 — what landed, Phase 2 — what landed (most recent), Phase 3 — what landed, Phase 4 — entry checklist (the active block), Phase 4 — kickoff outline (read after entry checklist clears) (+9 more)

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (23): 1. Clone and install, 2. Create `.env`, 3. Start data services, 4. Run the API, 5. Run the web app, 6. Run checks, Agent Graph, API Surface (+15 more)

### Community 25 - "Community 25"
Cohesion: 0.15
Nodes (25): CloneResult, ModuleSource, Chunk, LLMProvider, Settings, Chunk, LLMProvider, Path (+17 more)

### Community 26 - "Community 26"
Cohesion: 0.07
Nodes (36): api, ChunkPayload, ClaimEvent, ClaimStatus, CodeRef, CreateRepoResponse, CreateTourResponse, DiagramEvent (+28 more)

### Community 28 - "Community 28"
Cohesion: 0.15
Nodes (20): AsyncEngine, ChunkContent, LLMProvider, _apply(), _Cache, Claim, _objection_if_rejected(), Per-claim grounding check against ``read_chunks``.  The Verifier is the single l (+12 more)

### Community 29 - "Community 29"
Cohesion: 0.07
Nodes (31): ChunkHit, ChunkContent, AsyncEngine, LLMProvider, answer_user_prompt(), Q&A prompt templates.  Three prompts, all under the 2000-token budget from ``doc, _render_chunks(), sufficiency_user_prompt() (+23 more)

### Community 30 - "Community 30"
Cohesion: 0.07
Nodes (109): AppServices, Any, TourEventType, AsyncEngine, BaseTourEvent, ChunkPayload, CodeRef, IntentProfile (+101 more)

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (48): Node, Path, Path, Path, ParsedFile, ParsedSymbol, chunk_file(), _class_header_content() (+40 more)

### Community 32 - "Community 32"
Cohesion: 0.16
Nodes (24): RateLimitError, All providers in the fallback chain failed., HTTP 429 from a provider — triggers retry/fallback inside the provider., ProviderName, Shared fixtures for the core package's tests., Message, FakeClient, make_provider() (+16 more)

### Community 36 - "Community 36"
Cohesion: 0.31
Nodes (9): MonkeyPatch, Decide whether ``repo_url`` is already-current, stale, or unknown.      Cheap —, revisit_status(), Idempotency + staleness — exercised against a stubbed DB and stubbed clone.  The, When the remote HEAD has moved past the indexed SHA → status=stale., _StubEngine, test_revisit_unknown_repo_returns_stale(), test_revisit_with_advanced_remote_returns_stale_status() (+1 more)

### Community 37 - "Community 37"
Cohesion: 0.07
Nodes (34): AST, AsyncFunctionDef, Call, ClassDef, FunctionDef, Import, ImportFrom, Module (+26 more)

### Community 38 - "Community 38"
Cohesion: 0.20
Nodes (20): AsyncEngine, DiGraph, GraphQueryResult, QueryKind, _prime_cache(), Tests for ``graph_query``: entry points, hubs, callers/callees, layers.  Exercis, test_callees_of_a(), test_callers_of_c() (+12 more)

### Community 39 - "Community 39"
Cohesion: 0.20
Nodes (5): Animal, Dog, Fixture file the chunker tests assert against. Real Python so AST is exact., A base class with one method., A subclass overriding speak().

### Community 40 - "Community 40"
Cohesion: 0.29
Nodes (6): AsyncEngine, ChunkContent, CodeRef, ``read_chunks`` — the ONLY tool that returns source text.  Per Phase 2 decision, Fetch the content of every chunk whose ``(file_path, start_line, end_line)``, read_chunks()

### Community 45 - "Community 45"
Cohesion: 0.21
Nodes (14): EmbeddedChunk, AsyncEngine, Settings, known_head_sha(), make_engine(), persist_index(), PersistResult, Persist Phase 1 pipeline output to Postgres + pgvector.  The functions here are (+6 more)

### Community 46 - "Community 46"
Cohesion: 0.08
Nodes (23): EventDict, Any, Path, Settings, Shared core: settings, logging, and the LLMProvider abstraction., configure_logging(), _drop_chunk_content(), Structlog setup: JSON renderer in prod/CI, human-friendly renderer in dev/tests. (+15 more)

### Community 47 - "Community 47"
Cohesion: 0.11
Nodes (17): Path, clone_to_tempdir(), parse_github_url(), GitHub clone + HEAD-SHA helpers for Phase 1 ingestion.  Two entry points:  * :fu, Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c, remote_head_sha() (+9 more)

### Community 48 - "Community 48"
Cohesion: 0.15
Nodes (31): _coerce_section(), _collect_refs(), _format_source_bundle(), Teacher — weaves Insights into goal-anchored ``TourSection``s.  The Teacher is t, Run the Teacher once.      Returns ``{"draft_tour": [TourSection, …]}``. Empty l, Index every CodeRef from upstream insights by symbol so the Teacher     can only, run_teacher(), Claim (+23 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (13): Any, ChunkContent, CodeRef, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, FakeChunk, FakeEngine, FakeProvider, make_content() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.12
Nodes (17): _backoff_delay(), _BaseClient, _OpenAICompatibleClient, The single LLMProvider every agent goes through.  Responsibilities (Phase 0 deli, Exponential backoff with full jitter. attempt=0 is the first retry., Common interface for provider HTTP shims., Speaks the OpenAI chat-completions shape. Used for Groq and Cerebras., In-process embedder using sentence-transformers (Hugging Face weights).      No (+9 more)

### Community 51 - "Community 51"
Cohesion: 0.20
Nodes (9): Connection, _cache_key(), Thread-safe SQLite cache keyed on the canonical request hash., Generate a completion. Hits cache first; otherwise walks the fallback chain., Embed ``text`` via the in-process sentence-transformers embedder.          No HT, _SQLiteCache, ModelId, Path (+1 more)

### Community 53 - "Community 53"
Cohesion: 0.16
Nodes (13): GroundingEvalRow, CodeRef, QAResult, Settings, _contains_all_keywords(), GroundingEvalCaseResult, GroundingEvalMetrics, _has_expected_refs() (+5 more)

### Community 56 - "Community 56"
Cohesion: 0.20
Nodes (11): ModelBinding, Logical model identifiers and their physical-model resolution per provider.  Age, The concrete model name to send to a given provider for one `ModelId`., Any, EmbeddingResponse, ModelBinding, FakeEmbedder, Tests for ``LLMProvider.embed()`` — cache hit, fresh embed, dim contract. (+3 more)

### Community 57 - "Community 57"
Cohesion: 0.11
Nodes (44): Resolve each symbol's CodeRef from graph_metrics's underlying lookup.      The m, _resolve_refs(), _format_paths(), Flow Tracer — produces ``traced_flows`` Insights from call-graph paths.  Reads `, Choose which symbols to trace. Prefer the planner's explicit     targets; otherw, Run the Flow Tracer once.      Returns ``{"traced_flows": [Insight, …]}``. Empty, run_flow_tracer(), _seed_targets() (+36 more)

### Community 58 - "Community 58"
Cohesion: 0.10
Nodes (32): IntentProfileEvalRow, Path, AsyncEngine, Settings, PlannerEvalRow, dataset_path(), FileMappingEvalRow, IntentProfileEvalRow (+24 more)

### Community 59 - "Community 59"
Cohesion: 0.11
Nodes (28): EvalSpec, GroundingEvalMetrics, Namespace, Path, Any, Path, _cmd_list(), _cmd_status() (+20 more)

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (13): Any, ChunkContent, CodeRef, MonkeyPatch, _chunk(), _patch_tools(), End-to-end Q&A tests against fully stubbed dependencies.  We monkey-patch the th, Returns canned text responses in queue order. (+5 more)

### Community 63 - "Community 63"
Cohesion: 0.20
Nodes (14): Any, MonkeyPatch, Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)., _StubEngine, _StubProvider, test_parse_verdict_accepts_clean_json(), test_parse_verdict_extracts_json_from_prose(), test_parse_verdict_returns_none_on_garbage() (+6 more)

### Community 65 - "Community 65"
Cohesion: 0.12
Nodes (36): Run the Cartographer once.      Returns the state diff for the LangGraph reducer, run_cartographer(), coerce_claim(), coerce_insight(), _coerce_ref(), coerce_refs(), extract_json_list(), Shared LLM-output coercion helpers for capability nodes.  Every node asks the LL (+28 more)

### Community 66 - "Community 66"
Cohesion: 0.12
Nodes (29): _derive_ranker_weights(), _infer_flow_targets(), _infer_shape(), _pick_hub_bias(), plan(), Capability Planner — deterministic ``IntentProfile`` → ``CapabilityPlan``.  The, Deterministic planner. See ``docs/03_ARCHITECTURE.md`` § "The     Capability Pla, Pick a hub-bias tilt for the Cartographer.      Data-heavy intents → "data_hubs" (+21 more)

### Community 67 - "Community 67"
Cohesion: 0.10
Nodes (44): IntentProfile, TourSection, Any, CodeRef, MonkeyPatch, TourSection, VerifierObjection, _claim() (+36 more)

### Community 68 - "Community 68"
Cohesion: 0.12
Nodes (26): AsyncEngine, IntentProfile, Any, MonkeyPatch, build_graph(), Build + compile the full ``ArchaeologistState`` LangGraph.      Pass a Postgres, ArchaeologistState, The single shared LangGraph state. See ``docs/03_ARCHITECTURE.md``. (+18 more)

### Community 69 - "Community 69"
Cohesion: 0.19
Nodes (17): MonkeyPatch, Path, GroundingEvalRow, VerifierEvalRow, _async_return(), _dataset_path(), _DummyContext, _DummyEngine (+9 more)

### Community 71 - "Community 71"
Cohesion: 0.14
Nodes (19): CodeRef, QAExchange, One completed Q&A turn. v1 keeps the last 8; the prompt only consumes     the cu, Validator tests for ``ArchaeologistState`` and its sub-models.  These tests pin, _ref(), test_claim_defaults_unverified(), test_claim_rejects_relevance_out_of_unit_interval(), test_claim_requires_at_least_one_ref() (+11 more)

### Community 72 - "Community 72"
Cohesion: 0.19
Nodes (19): CapabilityPlan, IntentProfile, _format_active(), _format_keywords(), _format_tilt_line(), _format_weights(), Goal-anchor prompt block — shared across every generation node.  Every generatio, Render the goal-anchor block for the given (profile, plan) pair.      Output is (+11 more)

### Community 73 - "Community 73"
Cohesion: 0.20
Nodes (22): ArchaeologistState, Any, LLMProvider, _capability_planner_node(), _cartographer_node(), _flow_tracer_node(), _intent_profiler_node(), _lane_a_node() (+14 more)

### Community 74 - "Community 74"
Cohesion: 0.12
Nodes (28): lane_c_language_violation(), _matches_focus(), Lane C — guarded structural suspicions., Return the banned phrase when Lane C language is too certain., Build guarded suspicion opportunities from deterministic candidates.      Phase, run_lane_c_suspicion(), _lane_weight(), opportunity_score() (+20 more)

### Community 75 - "Community 75"
Cohesion: 0.11
Nodes (31): build_opportunity_briefing(), ranker_rationale(), Teacher-facing briefing helpers for Phase 5 opportunity cards., Attach the UI-visible Phase 5 briefing surfaces without reranking., Plain-English explanation of planner-derived ranker weights., detect_quality_opportunities(), _difficulty(), QualityCandidate (+23 more)

### Community 76 - "Community 76"
Cohesion: 0.06
Nodes (30): Alembic environment — uses Settings.postgres_dsn so dev + CI agree., AsyncEngine, DiGraph, AsyncEngine, SymbolMetrics, AsyncEngine, CodeRef, Path (+22 more)

### Community 80 - "Community 80"
Cohesion: 0.19
Nodes (15): ProviderName, EmbeddingResponse, LLMResponse, Provider-agnostic response shape., Provider-agnostic embedding shape., LLMResponse, Any, EmbeddingResponse (+7 more)

### Community 82 - "Community 82"
Cohesion: 0.18
Nodes (20): approachability_score(), Lane A — issue triage backed by graph approachability., Score issue approachability from graph facts, not GitHub labels., Rank issues and keep the next three rejected reasons., _ref_for_issue(), run_lane_a_triage(), triage_issues(), Issue (+12 more)

### Community 83 - "Community 83"
Cohesion: 0.50
Nodes (4): Path, _iter_source_files(), Hard CI rule: nothing in the source tree may branch on a ``purpose`` enum.  Phas, test_no_purpose_enum_in_source_tree()

### Community 90 - "Community 90"
Cohesion: 0.36
Nodes (7): _build_fact_bundle_for_test(), _fact_bundle(), Cartographer — produces ``system_map`` Insights from the call graph.  The Cartog, Render the fact bundle as a compact text block.      We deliberately avoid prose, _refs_for_symbols(), GraphQueryResult, SymbolMetrics

### Community 93 - "Community 93"
Cohesion: 0.18
Nodes (17): BaseSettings, ProviderError, Chunk, LLMProvider, Message, Settings, Any, Path (+9 more)

## Knowledge Gaps
- **235 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `type` (+230 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMProvider` connect `Community 57` to `Community 16`, `Community 18`, `Community 19`, `Community 25`, `Community 28`, `Community 29`, `Community 30`, `Community 32`, `Community 45`, `Community 46`, `Community 48`, `Community 50`, `Community 51`, `Community 56`, `Community 58`, `Community 65`, `Community 67`, `Community 68`, `Community 73`, `Community 75`, `Community 80`, `Community 90`, `Community 93`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Why does `IntentProfile` connect `Community 75` to `Community 65`, `Community 66`, `Community 67`, `Community 68`, `Community 71`, `Community 72`, `Community 73`, `Community 74`, `Community 48`, `Community 16`, `Community 82`, `Community 57`, `Community 90`, `Community 30`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 93` to `Community 32`, `Community 45`, `Community 46`, `Community 80`, `Community 50`, `Community 51`, `Community 53`, `Community 25`, `Community 58`, `Community 59`, `Community 30`, `Community 57`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Are the 146 inferred relationships involving `IntentProfile` (e.g. with `Any` and `TourEventType`) actually correct?**
  _`IntentProfile` has 146 INFERRED edges - model-reasoned connections that need verification._
- **Are the 138 inferred relationships involving `LLMProvider` (e.g. with `Any` and `AsyncEngine`) actually correct?**
  _`LLMProvider` has 138 INFERRED edges - model-reasoned connections that need verification._
- **Are the 88 inferred relationships involving `Settings` (e.g. with `AsyncEngine` and `BaseTourEvent`) actually correct?**
  _`Settings` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Are the 88 inferred relationships involving `ModelId` (e.g. with `ClaimStatus` and `Connection`) actually correct?**
  _`ModelId` has 88 INFERRED edges - model-reasoned connections that need verification._