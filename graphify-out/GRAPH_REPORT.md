# Graph Report - CodebaseArchiologist  (2026-06-19)

## Corpus Check
- 136 files · ~94,810 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1576 nodes · 4289 edges · 100 communities (83 shown, 17 thin omitted)
- Extraction: 60% EXTRACTED · 40% INFERRED · 0% AMBIGUOUS · INFERRED: 1723 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `05a4f143`
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

## Communities (100 total, 17 thin omitted)

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
Cohesion: 0.33
Nodes (10): ChunkContent, answer_question(), _extend_context(), _generate_answer(), _is_not_found(), _judge_sufficiency(), _parse_claims(), Q&A LangGraph mini-graph — the Phase 2 spine.  ``` vector_search → graph_travers (+2 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (17): Any, EventDict, index_repo(), arq worker function for the Phase 1 ingestion pipeline.  The actual pipeline log, arq job: index a GitHub repo end-to-end. Returns a JSON-able status dict., arq discovery target. Run with: ``arq repopilot_api.jobs.index_repo.WorkerSettin, shutdown(), startup() (+9 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (20): compilerOptions, allowImportingTsExtensions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib (+12 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (25): dependencies, next, react, react-dom, devDependencies, lighthouse, @playwright/test, @types/node (+17 more)

### Community 22 - "Community 22"
Cohesion: 0.12
Nodes (16): Current Build Phase, How to advance the phase, Phase 0 — what landed, Phase 1 — what landed, Phase 2 — what landed (most recent), Phase 3 — what landed, Phase 4 — entry checklist (the active block), Phase 4 — kickoff outline (read after entry checklist clears) (+8 more)

### Community 23 - "Community 23"
Cohesion: 0.40
Nodes (4): Quickstart (local dev), Repo layout, RepoPilot, Status

### Community 25 - "Community 25"
Cohesion: 0.16
Nodes (23): CloneResult, ModuleSource, Chunk, LLMProvider, Settings, Chunk, LLMProvider, Path (+15 more)

### Community 26 - "Community 26"
Cohesion: 0.07
Nodes (36): api, ChunkPayload, ClaimEvent, ClaimStatus, CodeRef, CreateRepoResponse, CreateTourResponse, DiagramEvent (+28 more)

### Community 28 - "Community 28"
Cohesion: 0.13
Nodes (29): Message, AsyncEngine, Claim, LLMProvider, AsyncEngine, ChunkContent, CodeRef, LLMProvider (+21 more)

### Community 29 - "Community 29"
Cohesion: 0.10
Nodes (20): LangGraph nodes + capability library.  Phase 2 surface: the six deterministic to, ChunkContent, ChunkHit, CodeRef, GraphQueryResult, Path, Shared Pydantic types used across tools, verifier, and Q&A.  These are the typed, Pointer into the repo. Every factual claim must carry at least one. (+12 more)

### Community 30 - "Community 30"
Cohesion: 0.07
Nodes (113): AppServices, Any, TourEventType, AsyncEngine, BaseTourEvent, ChunkPayload, CodeRef, IntentProfile (+105 more)

### Community 31 - "Community 31"
Cohesion: 0.11
Nodes (28): Path, Path, Path, ParsedFile, ParsedSymbol, chunk_file(), _class_header_content(), _class_header_end_line() (+20 more)

### Community 32 - "Community 32"
Cohesion: 0.22
Nodes (21): RateLimitError, HTTP 429 from a provider — triggers retry/fallback inside the provider., Message, FakeClient, make_provider(), make_response(), Build an LLMProvider that uses the supplied fakes for every provider., Test double for an LLM provider client. (+13 more)

### Community 36 - "Community 36"
Cohesion: 0.30
Nodes (10): MonkeyPatch, PipelineResult, Decide whether ``repo_url`` is already-current, stale, or unknown.      Cheap —, revisit_status(), Idempotency + staleness — exercised against a stubbed DB and stubbed clone.  The, When the remote HEAD has moved past the indexed SHA → status=stale., _StubEngine, test_revisit_unknown_repo_returns_stale() (+2 more)

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
Cohesion: 0.12
Nodes (10): Alembic environment — uses Settings.postgres_dsn so dev + CI agree., AsyncEngine, ChunkContent, CodeRef, SQLAlchemy schema for Phase 1 ingestion.  Tables:     repos              one row, Minimal pgvector type so alembic can emit `vector(N)` without importing     the, Vector, ``read_chunks`` — the ONLY tool that returns source text.  Per Phase 2 decision (+2 more)

### Community 45 - "Community 45"
Cohesion: 0.14
Nodes (25): ClaimStatus, AsyncEngine, Claim, IntentProfile, LLMProvider, TourSection, Phase2Claim, VerifierObjection (+17 more)

### Community 46 - "Community 46"
Cohesion: 0.10
Nodes (22): EmbeddedChunk, Path, AsyncEngine, Shared core: settings, logging, and the LLMProvider abstraction., _find_repo_env(), Application settings, loaded from environment / `.env` via pydantic-settings., Walk up from this file to the repo root and return the ``.env`` path.      Lets, Parse a comma-separated env var into a cleaned list. (+14 more)

### Community 47 - "Community 47"
Cohesion: 0.11
Nodes (17): Path, clone_to_tempdir(), parse_github_url(), GitHub clone + HEAD-SHA helpers for Phase 1 ingestion.  Two entry points:  * :fu, Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c, remote_head_sha() (+9 more)

### Community 48 - "Community 48"
Cohesion: 0.11
Nodes (44): Run the Cartographer once.      Returns the state diff for the LangGraph reducer, Resolve each symbol's CodeRef from graph_metrics's underlying lookup.      The m, _resolve_refs(), run_cartographer(), _coerce_output_shape(), LLMProvider, Single entrypoint to every LLM call in the system., Modality (+36 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (13): Any, ChunkContent, CodeRef, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, FakeChunk, FakeEngine, FakeProvider, make_content() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.15
Nodes (12): _backoff_delay(), _BaseClient, _cache_key(), The single LLMProvider every agent goes through.  Responsibilities (Phase 0 deli, Exponential backoff with full jitter. attempt=0 is the first retry., Common interface for provider HTTP shims., In-process embedder using sentence-transformers (Hugging Face weights).      No, Per-binding 429 retry loop with exponential backoff + jitter. (+4 more)

### Community 51 - "Community 51"
Cohesion: 0.17
Nodes (11): Connection, ProviderError, Thread-safe SQLite cache keyed on the canonical request hash., Generate a completion. Hits cache first; otherwise walks the fallback chain., Embed ``text`` via the in-process sentence-transformers embedder.          No HT, All providers in the fallback chain failed., _SQLiteCache, ModelId (+3 more)

### Community 53 - "Community 53"
Cohesion: 0.16
Nodes (13): GroundingEvalRow, CodeRef, QAResult, Settings, _contains_all_keywords(), GroundingEvalCaseResult, GroundingEvalMetrics, _has_expected_refs() (+5 more)

### Community 56 - "Community 56"
Cohesion: 0.20
Nodes (11): ModelBinding, Logical model identifiers and their physical-model resolution per provider.  Age, The concrete model name to send to a given provider for one `ModelId`., Any, EmbeddingResponse, ModelBinding, FakeEmbedder, Tests for ``LLMProvider.embed()`` — cache hit, fresh embed, dim contract. (+3 more)

### Community 57 - "Community 57"
Cohesion: 0.12
Nodes (23): _format_paths(), Flow Tracer — produces ``traced_flows`` Insights from call-graph paths.  Reads `, Choose which symbols to trace. Prefer the planner's explicit     targets; otherw, Run the Flow Tracer once.      Returns ``{"traced_flows": [Insight, …]}``. Empty, run_flow_tracer(), _seed_targets(), ModelId, Logical, agent-facing model identifiers. (+15 more)

### Community 58 - "Community 58"
Cohesion: 0.15
Nodes (21): IntentProfileEvalRow, Path, PlannerEvalRow, dataset_path(), FileMappingEvalRow, IntentProfileEvalRow, load_file_mapping_dataset(), load_grounding_dataset() (+13 more)

### Community 59 - "Community 59"
Cohesion: 0.17
Nodes (18): EvalSpec, GroundingEvalMetrics, Namespace, Path, _cmd_list(), _cmd_status(), _grounding_markdown(), main() (+10 more)

### Community 60 - "Community 60"
Cohesion: 0.29
Nodes (6): _OpenAICompatibleClient, Speaks the OpenAI chat-completions shape. Used for Groq and Cerebras., Default wiring used by the app. Tests pass `clients` for full control., AsyncClient, Settings, Self

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (13): Any, ChunkContent, CodeRef, MonkeyPatch, _chunk(), _patch_tools(), End-to-end Q&A tests against fully stubbed dependencies.  We monkey-patch the th, Returns canned text responses in queue order. (+5 more)

### Community 62 - "Community 62"
Cohesion: 0.16
Nodes (15): AsyncEngine, Settings, Settings, take_rows(), build_eval_context(), EvalContext, Shared runtime helpers for eval runners., resolve_repo_id() (+7 more)

### Community 63 - "Community 63"
Cohesion: 0.20
Nodes (14): Any, MonkeyPatch, Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)., _StubEngine, _StubProvider, test_parse_verdict_accepts_clean_json(), test_parse_verdict_extracts_json_from_prose(), test_parse_verdict_returns_none_on_garbage() (+6 more)

### Community 65 - "Community 65"
Cohesion: 0.10
Nodes (41): coerce_claim(), coerce_insight(), _coerce_ref(), coerce_refs(), extract_json_list(), Shared LLM-output coercion helpers for capability nodes.  Every node asks the LL, Pull the first JSON array out of ``raw`` and return it as a list of     dicts. R, Validate a ref. If the LLM names a symbol, prefer the known CodeRef     for that (+33 more)

### Community 66 - "Community 66"
Cohesion: 0.12
Nodes (31): _derive_ranker_weights(), _infer_flow_targets(), _infer_shape(), _pick_hub_bias(), plan(), Capability Planner — deterministic ``IntentProfile`` → ``CapabilityPlan``.  The, Deterministic planner. See ``docs/03_ARCHITECTURE.md`` § "The     Capability Pla, Pick a hub-bias tilt for the Cartographer.      Data-heavy intents → "data_hubs" (+23 more)

### Community 67 - "Community 67"
Cohesion: 0.15
Nodes (28): Any, CodeRef, TourSection, _claim(), engine(), Verifier-loop tests: actionability rubric + retry budget + flagging.  The ground, Queues responses keyed on which prompt is being graded.      The verifier loop i, _ref() (+20 more)

### Community 68 - "Community 68"
Cohesion: 0.11
Nodes (31): IntentProfile, Any, CodeRef, MonkeyPatch, TourSection, ArchaeologistState, CapabilityPlan, Deterministic Planner output. Verifiable in CI. (+23 more)

### Community 69 - "Community 69"
Cohesion: 0.17
Nodes (21): MonkeyPatch, Path, QAResult, The end-to-end output of one Q&A run., GroundingEvalRow, VerifierEvalRow, _async_return(), _dataset_path() (+13 more)

### Community 70 - "Community 70"
Cohesion: 0.21
Nodes (21): Node, _class_base_names(), _class_method_names(), _extract_imports(), _extract_symbols(), _first_docstring(), ImportEdge, _iter_block_children() (+13 more)

### Community 71 - "Community 71"
Cohesion: 0.17
Nodes (18): CodeRef, QAExchange, One completed Q&A turn. v1 keeps the last 8; the prompt only consumes     the cu, Validator tests for ``ArchaeologistState`` and its sub-models.  These tests pin, _ref(), test_claim_defaults_unverified(), test_claim_rejects_relevance_out_of_unit_interval(), test_claim_requires_at_least_one_ref() (+10 more)

### Community 72 - "Community 72"
Cohesion: 0.18
Nodes (20): CapabilityPlan, IntentProfile, IntentProfile, _format_active(), _format_keywords(), _format_tilt_line(), _format_weights(), Goal-anchor prompt block — shared across every generation node.  Every generatio (+12 more)

### Community 73 - "Community 73"
Cohesion: 0.18
Nodes (25): ArchaeologistState, Any, AsyncEngine, LLMProvider, build_graph(), _capability_planner_node(), _cartographer_node(), _flow_tracer_node() (+17 more)

### Community 74 - "Community 74"
Cohesion: 0.27
Nodes (13): CodeRef, Opportunity, _metrics(), _opp(), _profile(), Phase 5 Contribute-mode unit tests., _ref(), test_briefing_surfaces_intent_match_and_rationale() (+5 more)

### Community 75 - "Community 75"
Cohesion: 0.19
Nodes (11): build_opportunity_briefing(), ranker_rationale(), Teacher-facing briefing helpers for Phase 5 opportunity cards., Attach the UI-visible Phase 5 briefing surfaces without reranking., Plain-English explanation of planner-derived ranker weights., CapabilityPlan, IntentProfile, Opportunity (+3 more)

### Community 76 - "Community 76"
Cohesion: 0.27
Nodes (10): AsyncEngine, SymbolMetrics, _chunk_content(), _cyclomatic(), graph_metrics(), _has_tests(), ``graph_metrics`` — per-symbol metric pack used by Cartographer, Lanes A/B/C.  F, Return the metric pack for ``symbol``. Missing symbol → zeroed pack. (+2 more)

### Community 77 - "Community 77"
Cohesion: 0.29
Nodes (10): Any, Path, _coerce(), _ensure_reports_dir(), find_latest_report(), _now_stamp(), Persisted eval reports.  Each eval run writes a timestamped JSON + Markdown pair, Write a JSON + Markdown report pair. Returns ``(json_path, md_path)``. (+2 more)

### Community 78 - "Community 78"
Cohesion: 0.29
Nodes (6): ChunkHit, AsyncEngine, LLMProvider, ``vector_search`` — pgvector cosine k-NN over indexed chunks.  Embeds the query, Return the top-``k`` chunks for ``query`` in ``repo_id``., vector_search()

### Community 79 - "Community 79"
Cohesion: 0.29
Nodes (9): lane_c_language_violation(), _matches_focus(), Lane C — guarded structural suspicions., Return the banned phrase when Lane C language is too certain., Build guarded suspicion opportunities from deterministic candidates.      Phase, run_lane_c_suspicion(), CodeRef, IntentProfile (+1 more)

### Community 80 - "Community 80"
Cohesion: 0.24
Nodes (12): ProviderName, EmbeddingResponse, LLMResponse, Provider-agnostic response shape., Provider-agnostic embedding shape., LLMResponse, LLMProvider, Path (+4 more)

### Community 81 - "Community 81"
Cohesion: 0.60
Nodes (5): ChunkContent, answer_user_prompt(), Q&A prompt templates.  Three prompts, all under the 2000-token budget from ``doc, _render_chunks(), sufficiency_user_prompt()

### Community 82 - "Community 82"
Cohesion: 0.16
Nodes (23): approachability_score(), Lane A — issue triage backed by graph approachability., Score issue approachability from graph facts, not GitHub labels., Rank issues and keep the next three rejected reasons., _ref_for_issue(), run_lane_a_triage(), triage_issues(), Issue (+15 more)

### Community 83 - "Community 83"
Cohesion: 0.50
Nodes (4): Path, _iter_source_files(), Hard CI rule: nothing in the source tree may branch on a ``purpose`` enum.  Phas, test_no_purpose_enum_in_source_tree()

### Community 84 - "Community 84"
Cohesion: 0.50
Nodes (3): QAClaim, Types specific to the Q&A subgraph (sufficiency judge + final answer)., A single grounded claim in the Q&A answer.

### Community 87 - "Community 87"
Cohesion: 0.20
Nodes (9): AsyncEngine, DiGraph, invalidate(), load_graph(), Shared loader/cache for the per-repo NetworkX graph.  Per Phase 2 decision **D5*, Return the cached NetworkX graph for ``repo_id``; build it on miss., Drop the cached graph for ``repo_id``. Call when re-indexing., Test helper — clear all cached graphs. (+1 more)

### Community 88 - "Community 88"
Cohesion: 0.39
Nodes (8): detect_quality_opportunities(), _difficulty(), QualityCandidate, Lane B — deterministic code-health opportunities., Transform deterministic detector hits into unified opportunities., run_lane_b_quality(), IntentProfile, Opportunity

### Community 89 - "Community 89"
Cohesion: 0.39
Nodes (8): _lane_weight(), opportunity_score(), rank_opportunities(), Deterministic Phase 5 opportunity ranker., Compute a deterministic weighted score for one opportunity., Return opportunities in stable best-first order. No LLM reranking., CapabilityPlan, Opportunity

### Community 90 - "Community 90"
Cohesion: 0.36
Nodes (7): _build_fact_bundle_for_test(), _fact_bundle(), Cartographer — produces ``system_map`` Insights from the call graph.  The Cartog, Render the fact bundle as a compact text block.      We deliberately avoid prose, _refs_for_symbols(), GraphQueryResult, SymbolMetrics

### Community 91 - "Community 91"
Cohesion: 0.36
Nodes (7): AsyncEngine, CodeRef, Path, graph_traverse(), ``graph_traverse`` — BFS over the per-repo dependency graph.  The "complete-the-, BFS from ``start`` along the requested edge types; return all paths up to depth., _resolve_refs()

### Community 92 - "Community 92"
Cohesion: 0.29
Nodes (3): Shared fixtures for the core package's tests., FakeEmbedder, Test double for the sentence-transformers in-process embedder.      Returns dete

### Community 93 - "Community 93"
Cohesion: 0.47
Nodes (4): Path, _chunk(), FailingProvider, test_summarise_chunks_opens_circuit_after_provider_failure()

## Knowledge Gaps
- **218 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `type` (+213 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMProvider` connect `Community 48` to `Community 16`, `Community 18`, `Community 19`, `Community 25`, `Community 28`, `Community 30`, `Community 32`, `Community 36`, `Community 45`, `Community 46`, `Community 50`, `Community 51`, `Community 56`, `Community 57`, `Community 60`, `Community 62`, `Community 65`, `Community 67`, `Community 68`, `Community 69`, `Community 73`, `Community 78`, `Community 80`, `Community 90`, `Community 92`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Why does `IntentProfile` connect `Community 48` to `Community 65`, `Community 66`, `Community 67`, `Community 68`, `Community 71`, `Community 72`, `Community 73`, `Community 74`, `Community 75`, `Community 45`, `Community 79`, `Community 16`, `Community 82`, `Community 88`, `Community 57`, `Community 90`, `Community 30`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 30` to `Community 32`, `Community 36`, `Community 46`, `Community 60`, `Community 80`, `Community 48`, `Community 50`, `Community 51`, `Community 19`, `Community 53`, `Community 92`, `Community 25`, `Community 59`, `Community 28`, `Community 93`, `Community 62`, `Community 57`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **Are the 146 inferred relationships involving `IntentProfile` (e.g. with `Any` and `TourEventType`) actually correct?**
  _`IntentProfile` has 146 INFERRED edges - model-reasoned connections that need verification._
- **Are the 138 inferred relationships involving `LLMProvider` (e.g. with `Any` and `AsyncEngine`) actually correct?**
  _`LLMProvider` has 138 INFERRED edges - model-reasoned connections that need verification._
- **Are the 88 inferred relationships involving `Settings` (e.g. with `AsyncEngine` and `BaseTourEvent`) actually correct?**
  _`Settings` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Are the 88 inferred relationships involving `ModelId` (e.g. with `ClaimStatus` and `Connection`) actually correct?**
  _`ModelId` has 88 INFERRED edges - model-reasoned connections that need verification._