# Graph Report - CodebaseArchiologist  (2026-06-20)

## Corpus Check
- 142 files · ~86,184 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1669 nodes · 4490 edges · 105 communities (87 shown, 18 thin omitted)
- Extraction: 59% EXTRACTED · 41% INFERRED · 0% AMBIGUOUS · INFERRED: 1821 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `480e13a4`
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
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]

## God Nodes (most connected - your core abstractions)
1. `IntentProfile` - 163 edges
2. `LLMProvider` - 146 edges
3. `Settings` - 108 edges
4. `ModelId` - 91 edges
5. `Claim` - 84 edges
6. `Claim` - 80 edges
7. `Message` - 78 edges
8. `CapabilityPlan` - 66 edges
9. `CodeRef` - 60 edges
10. `BaseTourEvent` - 51 edges

## Surprising Connections (you probably didn't know these)
- `Any` --uses--> `IntentProfile`  [INFERRED]
  apps/api/src/repopilot_api/models.py → packages/agents/src/repopilot_agents/state.py
- `RedisSettings` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `RedisSettings` --uses--> `PipelineResult`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/ingestion/src/repopilot_ingestion/pipeline.py
- `Any` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `Any` --uses--> `PipelineResult`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/ingestion/src/repopilot_ingestion/pipeline.py

## Import Cycles
- 1-file cycle: `apps/api/src/repopilot_api/app.py -> apps/api/src/repopilot_api/app.py`

## Communities (105 total, 18 thin omitted)

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
Cohesion: 0.24
Nodes (11): AsyncEngine, Settings, take_rows(), resolve_repo_id(), _patched_read_chunks(), Verifier-quality eval runner for the Phase 2 gate., run_verifier_eval(), run_verifier_eval_rows() (+3 more)

### Community 7 - "Community 7"
Cohesion: 0.10
Nodes (20): 01 — Problem and Solution, Fine-grained mapping: example stated intents → what the Capability Planner picks, Four concrete walkthroughs (out of infinitely many possible), Hard scope fence — what v1 will NOT do, How the flow handles "hard-to-context-map" responses, Key features (at a glance), Success criteria, The core bet (+12 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (12): 02 — Tech Stack, ASCII full-stack diagram, Backend layer, Code intelligence layer (deterministic, NO LLM), Frontend layer, Groq free-tier survival strategy, LLM layer, Orchestration layer (+4 more)

### Community 9 - "Community 9"
Cohesion: 0.07
Nodes (32): AppServices, BaseModel, EventDict, FastAPI, Any, ArchaeologistError, Every fail-edge in the graph emits one of these., ChunkContent (+24 more)

### Community 10 - "Community 10"
Cohesion: 0.14
Nodes (13): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, After Phase 6 (+5 more)

### Community 13 - "Community 13"
Cohesion: 0.29
Nodes (6): Authoring, Engineering conventions, Graph maintenance (mandatory), Knowledge graph first, RepoPilot — Project Rules (portable), What this project is

### Community 14 - "Community 14"
Cohesion: 0.50
Nodes (3): Constraints, Mandatory order of operations, What to return

### Community 16 - "Community 16"
Cohesion: 0.13
Nodes (27): _coerce_keywords(), _coerce_modality_weights(), _coerce_optional_str(), _coerce_output_shape(), _fallback_profile(), _parse_json(), profile_intent(), Intent Profiler — free-text intent → structured ``IntentProfile``.  The Profiler (+19 more)

### Community 17 - "Community 17"
Cohesion: 0.17
Nodes (11): 01 — Problem and Solution, 02 — Tech Stack, 03 — Architecture, Doc layout, One-paragraph takeaway, Per-doc summaries, rag/00–06, RAG_PLAN (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.33
Nodes (9): answer_question(), _Context, _extend_context(), _generate_answer(), _is_not_found(), _parse_claims(), Q&A LangGraph mini-graph — the Phase 2 spine.  ``` vector_search → graph_travers, One sentence per line → one Claim per line.      Refs are attached by matching s (+1 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (17): Any, index_repo(), arq worker function for the Phase 1 ingestion pipeline.  The actual pipeline log, Build arq RedisSettings from Settings.redis_url.      Without this, arq falls ba, arq job: index a GitHub repo end-to-end. Returns a JSON-able status dict., arq discovery target. Run with: ``arq repopilot_api.jobs.index_repo.WorkerSettin, _redis_settings_from_url(), shutdown() (+9 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (20): compilerOptions, allowImportingTsExtensions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib (+12 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (25): dependencies, next, react, react-dom, devDependencies, lighthouse, @playwright/test, @types/node (+17 more)

### Community 22 - "Community 22"
Cohesion: 0.29
Nodes (6): Current Build Phase, How to advance the phase, RAG Phase 0 — entry checklist, RAG phase ladder, What just happened, What's still load-bearing from the previous product build

### Community 23 - "Community 23"
Cohesion: 0.08
Nodes (23): 1. Clone and install, 2. Create `.env`, 3. Start data services, 4. Run the API, 5. Run the web app, 6. Run checks, Agent Graph, API Surface (+15 more)

### Community 25 - "Community 25"
Cohesion: 0.20
Nodes (14): CloneResult, ModuleSource, Chunk, LLMProvider, Path, Settings, CloneResult, Canonical primary key used across the schema: ``owner/name@sha``. (+6 more)

### Community 26 - "Community 26"
Cohesion: 0.07
Nodes (36): api, ChunkPayload, ClaimEvent, ClaimStatus, CodeRef, CreateRepoResponse, CreateTourResponse, DiagramEvent (+28 more)

### Community 28 - "Community 28"
Cohesion: 0.16
Nodes (18): AsyncEngine, ChunkContent, LLMProvider, _apply(), _Cache, _objection_if_rejected(), Per-claim grounding check against ``read_chunks``.  The Verifier is the single l, Test helper — clear the verifier verdict cache. (+10 more)

### Community 29 - "Community 29"
Cohesion: 0.15
Nodes (14): LangGraph nodes + capability library.  Phase 2 surface: the six deterministic to, ChunkHit, CodeRef, Path, Shared Pydantic types used across tools, verifier, and Q&A.  These are the typed, Pointer into the repo. Every factual claim must carry at least one., Result of ``vector_search``: a chunk with retrieval metadata., Result of ``graph_traverse``: an ordered chain of CodeRefs. (+6 more)

### Community 30 - "Community 30"
Cohesion: 0.08
Nodes (106): Any, TourEventType, AsyncEngine, BaseTourEvent, ChunkPayload, CodeRef, IntentProfile, QAAnswerResponse (+98 more)

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (49): Node, Path, Path, Path, ParsedFile, ParsedSymbol, chunk_file(), _class_header_content() (+41 more)

### Community 32 - "Community 32"
Cohesion: 0.20
Nodes (22): RateLimitError, HTTP 429 from a provider — triggers retry/fallback inside the provider., ProviderName, Message, FakeClient, make_provider(), make_response(), Build an LLMProvider that uses the supplied fakes for every provider. (+14 more)

### Community 36 - "Community 36"
Cohesion: 0.30
Nodes (10): MonkeyPatch, PipelineResult, Decide whether ``repo_url`` is already-current, stale, or unknown.      Cheap —, revisit_status(), Idempotency + staleness — exercised against a stubbed DB and stubbed clone.  The, When the remote HEAD has moved past the indexed SHA → status=stale., _StubEngine, test_revisit_unknown_repo_returns_stale() (+2 more)

### Community 37 - "Community 37"
Cohesion: 0.15
Nodes (24): Module, DiGraph, build_graph(), _DefSymbol, graph_to_adjacency(), ModuleSource, NetworkX dependency graph builder.  Edges (Phase 1, deterministic — the LLM neve, Resolved module info handed to the graph builder. (+16 more)

### Community 38 - "Community 38"
Cohesion: 0.09
Nodes (36): AsyncEngine, DiGraph, AsyncEngine, DiGraph, GraphQueryResult, AsyncEngine, CodeRef, Path (+28 more)

### Community 39 - "Community 39"
Cohesion: 0.20
Nodes (5): Animal, Dog, Fixture file the chunker tests assert against. Real Python so AST is exact., A base class with one method., A subclass overriding speak().

### Community 40 - "Community 40"
Cohesion: 0.29
Nodes (6): AsyncEngine, ChunkContent, CodeRef, ``read_chunks`` — the ONLY tool that returns source text.  Per Phase 2 decision, Fetch the content of every chunk whose ``(file_path, start_line, end_line)``, read_chunks()

### Community 45 - "Community 45"
Cohesion: 0.14
Nodes (20): EmbeddedChunk, AsyncEngine, Settings, SQLAlchemy schema for Phase 1 ingestion.  Tables:     repos              one row, EmbeddedChunk, Batched async embedder over chunks via the central ``LLMProvider``.  The provide, Return a deterministic normalized vector when the local embedder rejects a chunk, _stable_fallback_vector() (+12 more)

### Community 46 - "Community 46"
Cohesion: 0.12
Nodes (11): Alembic environment — uses Settings.postgres_dsn so dev + CI agree., Path, Shared core: settings, logging, and the LLMProvider abstraction., _find_repo_env(), Application settings, loaded from environment / `.env` via pydantic-settings., Walk up from this file to the repo root and return the ``.env`` path.      Lets, Parse a comma-separated env var into a cleaned list., _split_csv() (+3 more)

### Community 47 - "Community 47"
Cohesion: 0.11
Nodes (17): Path, clone_to_tempdir(), parse_github_url(), GitHub clone + HEAD-SHA helpers for Phase 1 ingestion.  Two entry points:  * :fu, Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c, remote_head_sha() (+9 more)

### Community 48 - "Community 48"
Cohesion: 0.15
Nodes (12): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, Honest notes (+4 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (13): Any, ChunkContent, CodeRef, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, FakeChunk, FakeEngine, FakeProvider, make_content() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.16
Nodes (11): _backoff_delay(), LLMResponse, The single LLMProvider every agent goes through.  Responsibilities (Phase 0 deli, Exponential backoff with full jitter. attempt=0 is the first retry., In-process embedder using sentence-transformers (Hugging Face weights).      No, Per-binding 429 retry loop with exponential backoff + jitter., Provider-agnostic response shape., _SentenceTransformersEmbedder (+3 more)

### Community 51 - "Community 51"
Cohesion: 0.21
Nodes (8): Connection, _cache_key(), Thread-safe SQLite cache keyed on the canonical request hash., Generate a completion. Hits cache first; otherwise walks the fallback chain., Embed ``text`` via the in-process sentence-transformers embedder.          No HT, _SQLiteCache, ModelId, Path

### Community 53 - "Community 53"
Cohesion: 0.16
Nodes (13): GroundingEvalRow, CodeRef, QAResult, Settings, _contains_all_keywords(), GroundingEvalCaseResult, GroundingEvalMetrics, _has_expected_refs() (+5 more)

### Community 56 - "Community 56"
Cohesion: 0.17
Nodes (15): ProviderName, Logical model identifiers and their physical-model resolution per provider.  Age, EmbeddingResponse, Provider-agnostic embedding shape., LLMResponse, LLMProvider, Any, EmbeddingResponse (+7 more)

### Community 57 - "Community 57"
Cohesion: 0.14
Nodes (42): AsyncEngine, CapabilityPlan, Insight, IntentProfile, LLMProvider, Claim, Insight, AsyncEngine (+34 more)

### Community 58 - "Community 58"
Cohesion: 0.19
Nodes (17): IntentProfileEvalRow, Path, PlannerEvalRow, dataset_path(), FileMappingEvalRow, load_file_mapping_dataset(), load_grounding_dataset(), load_intent_dataset() (+9 more)

### Community 59 - "Community 59"
Cohesion: 0.17
Nodes (18): EvalSpec, GroundingEvalMetrics, Namespace, Path, _cmd_list(), _cmd_status(), _grounding_markdown(), main() (+10 more)

### Community 60 - "Community 60"
Cohesion: 0.15
Nodes (12): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, Honest notes (+4 more)

### Community 61 - "Community 61"
Cohesion: 0.15
Nodes (13): Any, ChunkContent, CodeRef, MonkeyPatch, _chunk(), _patch_tools(), End-to-end Q&A tests against fully stubbed dependencies.  We monkey-patch the th, Returns canned text responses in queue order. (+5 more)

### Community 62 - "Community 62"
Cohesion: 0.15
Nodes (12): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, Critical safety rule (+4 more)

### Community 63 - "Community 63"
Cohesion: 0.20
Nodes (14): Any, MonkeyPatch, Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)., _StubEngine, _StubProvider, test_parse_verdict_accepts_clean_json(), test_parse_verdict_extracts_json_from_prose(), test_parse_verdict_returns_none_on_garbage() (+6 more)

### Community 65 - "Community 65"
Cohesion: 0.10
Nodes (43): Run the Cartographer once.      Returns the state diff for the LangGraph reducer, run_cartographer(), coerce_claim(), coerce_insight(), _coerce_ref(), coerce_refs(), extract_json_list(), Shared LLM-output coercion helpers for capability nodes.  Every node asks the LL (+35 more)

### Community 66 - "Community 66"
Cohesion: 0.12
Nodes (29): _derive_ranker_weights(), _infer_flow_targets(), _infer_shape(), _pick_hub_bias(), plan(), Capability Planner — deterministic ``IntentProfile`` → ``CapabilityPlan``.  The, Deterministic planner. See ``docs/03_ARCHITECTURE.md`` § "The     Capability Pla, Pick a hub-bias tilt for the Cartographer.      Data-heavy intents → "data_hubs" (+21 more)

### Community 67 - "Community 67"
Cohesion: 0.11
Nodes (31): ClaimStatus, AsyncEngine, Claim, IntentProfile, LLMProvider, TourSection, MonkeyPatch, TourSection (+23 more)

### Community 68 - "Community 68"
Cohesion: 0.16
Nodes (17): Any, fake_engine(), _insight(), _NullProvider, _opportunity(), End-to-end LangGraph wiring tests.  Mock the per-node bodies so the graph runs i, Confirmed-profile path: profile + plan are already set, so the     profiler is a, Cold-start path: no profile, no plan. The profiler must run, the     planner mus (+9 more)

### Community 69 - "Community 69"
Cohesion: 0.18
Nodes (19): MonkeyPatch, Path, QAResult, The end-to-end output of one Q&A run., GroundingEvalRow, VerifierEvalRow, _async_return(), _dataset_path() (+11 more)

### Community 70 - "Community 70"
Cohesion: 0.17
Nodes (11): Definition of Done (for the whole plan), Eval datasets we will use, For contributors, Metrics, in priority order, Per-phase doc template (what every `docs/rag/<n>_*.md` looks like), RAG Quality Plan — RepoPilot Retrieval Upgrade, Sequencing rationale (why this order), The 7 phases at a glance (+3 more)

### Community 71 - "Community 71"
Cohesion: 0.13
Nodes (22): QAExchange, One completed Q&A turn. v1 keeps the last 8; the prompt only consumes     the cu, Validator tests for ``ArchaeologistState`` and its sub-models.  These tests pin, _ref(), test_claim_defaults_unverified(), test_claim_rejects_relevance_out_of_unit_interval(), test_claim_requires_at_least_one_ref(), test_insight_accepts_complete_fields() (+14 more)

### Community 72 - "Community 72"
Cohesion: 0.19
Nodes (19): CapabilityPlan, IntentProfile, _format_active(), _format_keywords(), _format_tilt_line(), _format_weights(), Goal-anchor prompt block — shared across every generation node.  Every generatio, Render the goal-anchor block for the given (profile, plan) pair.      Output is (+11 more)

### Community 73 - "Community 73"
Cohesion: 0.16
Nodes (28): ArchaeologistState, Any, AsyncEngine, IntentProfile, LLMProvider, build_graph(), _capability_planner_node(), _cartographer_node() (+20 more)

### Community 74 - "Community 74"
Cohesion: 0.35
Nodes (11): _metrics(), _opp(), _profile(), Phase 5 Contribute-mode unit tests., _ref(), test_briefing_surfaces_intent_match_and_rationale(), test_lane_a_approachability_uses_graph_not_labels(), test_lane_b_dead_code_excludes_entry_points() (+3 more)

### Community 75 - "Community 75"
Cohesion: 0.21
Nodes (15): detect_quality_opportunities(), _difficulty(), QualityCandidate, Lane B — deterministic code-health opportunities., Transform deterministic detector hits into unified opportunities., run_lane_b_quality(), IntentProfile, Opportunity (+7 more)

### Community 76 - "Community 76"
Cohesion: 0.09
Nodes (20): AST, AsyncFunctionDef, Call, ClassDef, FunctionDef, Import, ImportFrom, AsyncEngine (+12 more)

### Community 77 - "Community 77"
Cohesion: 0.17
Nodes (11): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, Honest notes (+3 more)

### Community 78 - "Community 78"
Cohesion: 0.29
Nodes (10): Any, Path, _coerce(), _ensure_reports_dir(), find_latest_report(), _now_stamp(), Persisted eval reports.  Each eval run writes a timestamped JSON + Markdown pair, Write a JSON + Markdown report pair. Returns ``(json_path, md_path)``. (+2 more)

### Community 79 - "Community 79"
Cohesion: 0.18
Nodes (10): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, 7. Implementation order, Honest notes (+2 more)

### Community 80 - "Community 80"
Cohesion: 0.17
Nodes (25): ModelId, Logical, agent-facing model identifiers., LLMProvider, Message, Single entrypoint to every LLM call in the system., LLMProvider, OutputShape, AsyncEngine (+17 more)

### Community 81 - "Community 81"
Cohesion: 0.20
Nodes (9): 1. Goal, 2. Why now, 3. What changes in the code, 4. What changes in the eval, 5. Gate, 6. Stop conditions, Honest notes for future-me, Open questions to resolve before starting (+1 more)

### Community 82 - "Community 82"
Cohesion: 0.19
Nodes (19): approachability_score(), Lane A — issue triage backed by graph approachability., Score issue approachability from graph facts, not GitHub labels., Rank issues and keep the next three rejected reasons., _ref_for_issue(), run_lane_a_triage(), triage_issues(), Issue (+11 more)

### Community 83 - "Community 83"
Cohesion: 0.50
Nodes (4): Path, _iter_source_files(), Hard CI rule: nothing in the source tree may branch on a ``purpose`` enum.  Phas, test_no_purpose_enum_in_source_tree()

### Community 84 - "Community 84"
Cohesion: 0.29
Nodes (6): ChunkHit, AsyncEngine, LLMProvider, ``vector_search`` — pgvector cosine k-NN over indexed chunks.  Embeds the query, Return the top-``k`` chunks for ``query`` in ``repo_id``., vector_search()

### Community 87 - "Community 87"
Cohesion: 0.24
Nodes (11): ModelBinding, The concrete model name to send to a given provider for one `ModelId`., _BaseClient, _OpenAICompatibleClient, Common interface for provider HTTP shims., Speaks the OpenAI chat-completions shape. Used for Groq and Cerebras., Default wiring used by the app. Tests pass `clients` for full control., AsyncClient (+3 more)

### Community 88 - "Community 88"
Cohesion: 0.60
Nodes (5): ChunkContent, answer_user_prompt(), Q&A prompt templates.  Three prompts, all under the 2000-token budget from ``doc, _render_chunks(), sufficiency_user_prompt()

### Community 89 - "Community 89"
Cohesion: 0.17
Nodes (25): Any, CodeRef, _claim(), engine(), Verifier-loop tests: actionability rubric + retry budget + flagging.  The ground, Queues responses keyed on which prompt is being graded.      The verifier loop i, _ref(), _ScriptedProvider (+17 more)

### Community 90 - "Community 90"
Cohesion: 0.15
Nodes (12): Priority order for acting on this doc, R1 — The eval foundation is too thin for the effects being measured (ROOT RISK), R2 — Per-phase latency budgets are mathematically inconsistent with the global gate, R3 — "Significant on at least one of three datasets" inflates false positives, R4 — The verifier is load-bearing but unvalidated, R5 — Phases optimize around a fixed, non-code-specialized embedding model, R6 — Phases are measured pairwise, but the effects interact, R7 — Synthetic-content safety rests on a single test (+4 more)

### Community 91 - "Community 91"
Cohesion: 0.25
Nodes (10): _build_fact_bundle_for_test(), _fact_bundle(), Cartographer — produces ``system_map`` Insights from the call graph.  The Cartog, Render the fact bundle as a compact text block.      We deliberately avoid prose, Resolve each symbol's CodeRef from graph_metrics's underlying lookup.      The m, _refs_for_symbols(), _resolve_refs(), CodeRef (+2 more)

### Community 92 - "Community 92"
Cohesion: 0.27
Nodes (8): build_opportunity_briefing(), ranker_rationale(), Teacher-facing briefing helpers for Phase 5 opportunity cards., Attach the UI-visible Phase 5 briefing surfaces without reranking., Plain-English explanation of planner-derived ranker weights., CapabilityPlan, IntentProfile, ``ArchaeologistState`` and the Pydantic v2 schema it composes.  This is the Phas

### Community 93 - "Community 93"
Cohesion: 0.16
Nodes (21): ProviderError, All providers in the fallback chain failed., Chunk, LLMProvider, Settings, Chunk, LLMProvider, Message (+13 more)

### Community 100 - "Community 100"
Cohesion: 0.29
Nodes (9): lane_c_language_violation(), _matches_focus(), Lane C — guarded structural suspicions., Return the banned phrase when Lane C language is too certain., Build guarded suspicion opportunities from deterministic candidates.      Phase, run_lane_c_suspicion(), CodeRef, IntentProfile (+1 more)

### Community 101 - "Community 101"
Cohesion: 0.39
Nodes (8): _lane_weight(), opportunity_score(), rank_opportunities(), Deterministic Phase 5 opportunity ranker., Compute a deterministic weighted score for one opportunity., Return opportunities in stable best-first order. No LLM reranking., CapabilityPlan, Opportunity

### Community 102 - "Community 102"
Cohesion: 0.36
Nodes (7): _format_paths(), Flow Tracer — produces ``traced_flows`` Insights from call-graph paths.  Reads `, Choose which symbols to trace. Prefer the planner's explicit     targets; otherw, Run the Flow Tracer once.      Returns ``{"traced_flows": [Insight, …]}``. Empty, run_flow_tracer(), _seed_targets(), CapabilityPlan

### Community 103 - "Community 103"
Cohesion: 0.29
Nodes (3): Shared fixtures for the core package's tests., FakeEmbedder, Test double for the sentence-transformers in-process embedder.      Returns dete

## Knowledge Gaps
- **281 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `type` (+276 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMProvider` connect `Community 80` to `Community 6`, `Community 16`, `Community 18`, `Community 19`, `Community 25`, `Community 28`, `Community 30`, `Community 32`, `Community 36`, `Community 45`, `Community 50`, `Community 51`, `Community 56`, `Community 57`, `Community 65`, `Community 67`, `Community 68`, `Community 69`, `Community 73`, `Community 84`, `Community 87`, `Community 89`, `Community 91`, `Community 93`, `Community 102`, `Community 103`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Why does `IntentProfile` connect `Community 57` to `Community 65`, `Community 66`, `Community 67`, `Community 100`, `Community 68`, `Community 102`, `Community 71`, `Community 72`, `Community 73`, `Community 9`, `Community 75`, `Community 16`, `Community 80`, `Community 82`, `Community 89`, `Community 91`, `Community 92`, `Community 30`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 30` to `Community 32`, `Community 36`, `Community 6`, `Community 103`, `Community 45`, `Community 46`, `Community 80`, `Community 50`, `Community 51`, `Community 19`, `Community 53`, `Community 87`, `Community 56`, `Community 25`, `Community 59`, `Community 93`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Are the 147 inferred relationships involving `IntentProfile` (e.g. with `Any` and `TourEventType`) actually correct?**
  _`IntentProfile` has 147 INFERRED edges - model-reasoned connections that need verification._
- **Are the 139 inferred relationships involving `LLMProvider` (e.g. with `Any` and `AsyncEngine`) actually correct?**
  _`LLMProvider` has 139 INFERRED edges - model-reasoned connections that need verification._
- **Are the 101 inferred relationships involving `Settings` (e.g. with `AsyncEngine` and `BaseTourEvent`) actually correct?**
  _`Settings` has 101 INFERRED edges - model-reasoned connections that need verification._
- **Are the 88 inferred relationships involving `ModelId` (e.g. with `ClaimStatus` and `Connection`) actually correct?**
  _`ModelId` has 88 INFERRED edges - model-reasoned connections that need verification._