# Graph Report - CodebaseArchiologist  (2026-06-17)

## Corpus Check
- 112 files · ~76,324 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1269 nodes · 2984 edges · 85 communities (70 shown, 15 thin omitted)
- Extraction: 67% EXTRACTED · 33% INFERRED · 0% AMBIGUOUS · INFERRED: 992 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cd5291e8`
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
- [[_COMMUNITY_Community 77|Community 77]]
- [[_COMMUNITY_Community 78|Community 78]]
- [[_COMMUNITY_Community 80|Community 80]]
- [[_COMMUNITY_Community 81|Community 81]]
- [[_COMMUNITY_Community 82|Community 82]]
- [[_COMMUNITY_Community 83|Community 83]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]

## God Nodes (most connected - your core abstractions)
1. `LLMProvider` - 122 edges
2. `ModelId` - 92 edges
3. `IntentProfile` - 86 edges
4. `Message` - 78 edges
5. `Settings` - 68 edges
6. `CapabilityPlan` - 53 edges
7. `Claim` - 45 edges
8. `Insight` - 45 edges
9. `Claim` - 44 edges
10. `CodeRef` - 43 edges

## Surprising Connections (you probably didn't know these)
- `Any` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `Any` --uses--> `PipelineResult`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/ingestion/src/repopilot_ingestion/pipeline.py
- `WorkerSettings` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `WorkerSettings` --uses--> `PipelineResult`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/ingestion/src/repopilot_ingestion/pipeline.py
- `startup()` --calls--> `get_settings()`  [EXTRACTED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/settings.py

## Import Cycles
- 1-file cycle: `apps/api/src/repopilot_api/app.py -> apps/api/src/repopilot_api/app.py`

## Communities (85 total, 15 thin omitted)

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
Cohesion: 0.14
Nodes (26): _coerce_keywords(), _coerce_modality_weights(), _coerce_optional_str(), _coerce_output_shape(), _fallback_profile(), _parse_json(), profile_intent(), Intent Profiler — free-text intent → structured ``IntentProfile``.  The Profiler (+18 more)

### Community 17 - "Community 17"
Cohesion: 0.17
Nodes (11): 00 — Claude Build Guide (Standing Context) *(the contract)*, 01 — Problem and Solution *(the thesis / "why")*, 02 — Tech Stack *(the toolbox — every choice + why + what was rejected)*, 03 — Architecture *(the blueprint — the keystone doc)*, 04 — Build Plan *(the schedule — 7 phases, each with a hard gate)*, 05 — Phase Prompts *(the script — paste-ready)*, Build progress at a glance, How the doc set fits together (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.14
Nodes (38): ModelId, Logical, agent-facing model identifiers., LLMProvider, Message, Single entrypoint to every LLM call in the system., LLMResponse, Modality, IntentProfile (+30 more)

### Community 19 - "Community 19"
Cohesion: 0.08
Nodes (22): EventDict, FastAPI, Any, Path, create_app(), FastAPI scaffold — health-check only in Phase 0., FastAPI app entrypoint. Endpoints are added in Phase 4., Shared core: settings, logging, and the LLMProvider abstraction. (+14 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (18): dependencies, next, react, react-dom, devDependencies, @types/node, @types/react, @types/react-dom (+10 more)

### Community 22 - "Community 22"
Cohesion: 0.14
Nodes (13): Current Build Phase, How to advance the phase, Phase 0 — what landed, Phase 1 — what landed, Phase 2 — what landed (most recent), Phase 3 — what landed, Phase 4 — entry checklist (the active block), Phase 4 — kickoff outline (read after entry checklist clears) (+5 more)

### Community 23 - "Community 23"
Cohesion: 0.40
Nodes (4): Quickstart (local dev), Repo layout, RepoPilot, Status

### Community 25 - "Community 25"
Cohesion: 0.17
Nodes (22): CloneResult, ModuleSource, Chunk, LLMProvider, Path, Settings, Chunk, Structural chunker — one chunk per function and per class.  Per the Phase 1 spec (+14 more)

### Community 28 - "Community 28"
Cohesion: 0.16
Nodes (16): AsyncEngine, ChunkContent, LLMProvider, _apply(), _Cache, _objection_if_rejected(), Per-claim grounding check against ``read_chunks``.  The Verifier is the single l, Test helper — clear the verifier verdict cache. (+8 more)

### Community 29 - "Community 29"
Cohesion: 0.17
Nodes (12): ChunkHit, CodeRef, Path, Pointer into the repo. Every factual claim must carry at least one., Result of ``vector_search``: a chunk with retrieval metadata., Result of ``graph_traverse``: an ordered chain of CodeRefs., Validator tests for the shared Phase 2 types., test_chunk_hit_distance_must_be_non_negative() (+4 more)

### Community 30 - "Community 30"
Cohesion: 0.13
Nodes (10): AST, AsyncFunctionDef, Call, ClassDef, FunctionDef, Import, ImportFrom, Walk one module and emit edges into typed lists.      Scope tracking is minimal (+2 more)

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (48): Node, Path, Path, Path, ParsedFile, ParsedSymbol, chunk_file(), _class_header_content() (+40 more)

### Community 32 - "Community 32"
Cohesion: 0.17
Nodes (22): RateLimitError, HTTP 429 from a provider — triggers retry/fallback inside the provider., ProviderName, Shared fixtures for the core package's tests., Message, FakeClient, make_provider(), make_response() (+14 more)

### Community 36 - "Community 36"
Cohesion: 0.31
Nodes (9): MonkeyPatch, Decide whether ``repo_url`` is already-current, stale, or unknown.      Cheap —, revisit_status(), Idempotency + staleness — exercised against a stubbed DB and stubbed clone.  The, When the remote HEAD has moved past the indexed SHA → status=stale., _StubEngine, test_revisit_unknown_repo_returns_stale(), test_revisit_with_advanced_remote_returns_stale_status() (+1 more)

### Community 37 - "Community 37"
Cohesion: 0.15
Nodes (24): Module, DiGraph, build_graph(), _DefSymbol, graph_to_adjacency(), ModuleSource, NetworkX dependency graph builder.  Edges (Phase 1, deterministic — the LLM neve, Resolved module info handed to the graph builder. (+16 more)

### Community 38 - "Community 38"
Cohesion: 0.20
Nodes (20): AsyncEngine, DiGraph, GraphQueryResult, QueryKind, _prime_cache(), Tests for ``graph_query``: entry points, hubs, callers/callees, layers.  Exercis, test_callees_of_a(), test_callers_of_c() (+12 more)

### Community 39 - "Community 39"
Cohesion: 0.20
Nodes (5): Animal, Dog, Fixture file the chunker tests assert against. Real Python so AST is exact., A base class with one method., A subclass overriding speak().

### Community 40 - "Community 40"
Cohesion: 0.05
Nodes (36): Alembic environment — uses Settings.postgres_dsn so dev + CI agree., AsyncEngine, DiGraph, AsyncEngine, SymbolMetrics, AsyncEngine, CodeRef, Path (+28 more)

### Community 45 - "Community 45"
Cohesion: 0.28
Nodes (8): Any, index_repo(), arq worker function for the Phase 1 ingestion pipeline.  The actual pipeline log, arq job: index a GitHub repo end-to-end. Returns a JSON-able status dict., arq discovery target. Run with: ``arq repopilot_api.jobs.index_repo.WorkerSettin, shutdown(), startup(), WorkerSettings

### Community 46 - "Community 46"
Cohesion: 0.18
Nodes (15): EmbeddedChunk, AsyncEngine, Settings, known_head_sha(), make_engine(), persist_index(), PersistResult, Persist Phase 1 pipeline output to Postgres + pgvector.  The functions here are (+7 more)

### Community 47 - "Community 47"
Cohesion: 0.11
Nodes (17): Path, clone_to_tempdir(), parse_github_url(), GitHub clone + HEAD-SHA helpers for Phase 1 ingestion.  Two entry points:  * :fu, Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c, remote_head_sha() (+9 more)

### Community 48 - "Community 48"
Cohesion: 0.17
Nodes (19): _build_fact_bundle_for_test(), _fact_bundle(), Cartographer — produces ``system_map`` Insights from the call graph.  The Cartog, Run the Cartographer once.      Returns the state diff for the LangGraph reducer, Render the fact bundle as a compact text block.      We deliberately avoid prose, Resolve each symbol's CodeRef from graph_metrics's underlying lookup.      The m, _refs_for_symbols(), _resolve_refs() (+11 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (13): Any, ChunkContent, CodeRef, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, FakeChunk, FakeEngine, FakeProvider, make_content() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.16
Nodes (10): _backoff_delay(), LLMResponse, Exponential backoff with full jitter. attempt=0 is the first retry., In-process embedder using sentence-transformers (Hugging Face weights).      No, Per-binding 429 retry loop with exponential backoff + jitter., Provider-agnostic response shape., _SentenceTransformersEmbedder, Any (+2 more)

### Community 51 - "Community 51"
Cohesion: 0.21
Nodes (9): _cache_key(), ProviderError, The single LLMProvider every agent goes through.  Responsibilities (Phase 0 deli, Thread-safe SQLite cache keyed on the canonical request hash., Generate a completion. Hits cache first; otherwise walks the fallback chain., Embed ``text`` via the in-process sentence-transformers embedder.          No HT, All providers in the fallback chain failed., _SQLiteCache (+1 more)

### Community 53 - "Community 53"
Cohesion: 0.17
Nodes (16): GroundingEvalRow, CodeRef, Settings, QAResult, The end-to-end output of one Q&A run., QAResult, GroundingEvalRow, _contains_all_keywords() (+8 more)

### Community 56 - "Community 56"
Cohesion: 0.33
Nodes (6): Any, FakeEmbedder, Tests for ``LLMProvider.embed()`` — cache hit, fresh embed, dim contract., Test double — bypasses the sentence-transformers model load and     returns cann, test_embed_cache_hit_skips_provider(), test_embed_returns_vector()

### Community 57 - "Community 57"
Cohesion: 0.15
Nodes (19): _format_paths(), Flow Tracer — produces ``traced_flows`` Insights from call-graph paths.  Reads `, Choose which symbols to trace. Prefer the planner's explicit     targets; otherw, Run the Flow Tracer once.      Returns ``{"traced_flows": [Insight, …]}``. Empty, run_flow_tracer(), _seed_targets(), AsyncEngine, CapabilityPlan (+11 more)

### Community 58 - "Community 58"
Cohesion: 0.16
Nodes (18): IntentProfileEvalRow, Path, PlannerEvalRow, dataset_path(), IntentProfileEvalRow, load_grounding_dataset(), load_intent_dataset(), load_jsonl_rows() (+10 more)

### Community 59 - "Community 59"
Cohesion: 0.12
Nodes (27): EvalSpec, GroundingEvalMetrics, Namespace, Path, Any, Path, _cmd_list(), _cmd_status() (+19 more)

### Community 60 - "Community 60"
Cohesion: 0.18
Nodes (18): AsyncClient, Connection, ModelBinding, ProviderName, Logical model identifiers and their physical-model resolution per provider.  Age, The concrete model name to send to a given provider for one `ModelId`., _BaseClient, _OpenAICompatibleClient (+10 more)

### Community 61 - "Community 61"
Cohesion: 0.16
Nodes (15): Any, ChunkContent, CodeRef, MonkeyPatch, _chunk(), _patch_tools(), End-to-end Q&A tests against fully stubbed dependencies.  We monkey-patch the th, Returns canned text responses in queue order. (+7 more)

### Community 62 - "Community 62"
Cohesion: 0.19
Nodes (11): Settings, build_eval_context(), EvalContext, Shared runtime helpers for eval runners., resolve_repo_id(), _patched_read_chunks(), Verifier-quality eval runner for the Phase 2 gate., run_verifier_eval_rows() (+3 more)

### Community 63 - "Community 63"
Cohesion: 0.20
Nodes (14): Any, MonkeyPatch, Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)., _StubEngine, _StubProvider, test_parse_verdict_accepts_clean_json(), test_parse_verdict_extracts_json_from_prose(), test_parse_verdict_returns_none_on_garbage() (+6 more)

### Community 65 - "Community 65"
Cohesion: 0.18
Nodes (24): extract_json_list(), Pull the first JSON array out of ``raw`` and return it as a list of     dicts. R, CapabilityPlan, IntentProfile, _insight(), _plan(), _profile(), Unit tests for the Cartographer / Flow Tracer / Teacher nodes.  These tests pin (+16 more)

### Community 66 - "Community 66"
Cohesion: 0.12
Nodes (31): _derive_ranker_weights(), _infer_flow_targets(), _infer_shape(), _pick_hub_bias(), plan(), Capability Planner — deterministic ``IntentProfile`` → ``CapabilityPlan``.  The, Deterministic planner. See ``docs/03_ARCHITECTURE.md`` § "The     Capability Pla, Pick a hub-bias tilt for the Cartographer.      Data-heavy intents → "data_hubs" (+23 more)

### Community 67 - "Community 67"
Cohesion: 0.06
Nodes (92): BaseModel, ClaimStatus, AsyncEngine, Claim, IntentProfile, LLMProvider, TourSection, CodeRef (+84 more)

### Community 68 - "Community 68"
Cohesion: 0.18
Nodes (15): Any, MonkeyPatch, build_graph(), Build + compile the full ``ArchaeologistState`` LangGraph.      Pass a Postgres, fake_engine(), _NullProvider, End-to-end LangGraph wiring tests.  Mock the per-node bodies so the graph runs i, Cold-start path: no profile, no plan. The profiler must run, the     planner mus (+7 more)

### Community 69 - "Community 69"
Cohesion: 0.18
Nodes (16): MonkeyPatch, Path, VerifierEvalRow, _async_return(), _dataset_path(), _DummyContext, _DummyEngine, _DummyProvider (+8 more)

### Community 70 - "Community 70"
Cohesion: 0.23
Nodes (14): _coerce_section(), _collect_refs(), _format_source_bundle(), Teacher — weaves Insights into goal-anchored ``TourSection``s.  The Teacher is t, Run the Teacher once.      Returns ``{"draft_tour": [TourSection, …]}``. Empty l, Index every CodeRef from upstream insights by symbol so the Teacher     can only, run_teacher(), CapabilityPlan (+6 more)

### Community 71 - "Community 71"
Cohesion: 0.30
Nodes (11): coerce_claim(), coerce_insight(), _coerce_ref(), coerce_refs(), Shared LLM-output coercion helpers for capability nodes.  Every node asks the LL, Validate a ref. If the LLM names a symbol, prefer the known CodeRef     for that, Validate a single ``Insight`` payload. Returns ``None`` if any     required fiel, Any (+3 more)

### Community 72 - "Community 72"
Cohesion: 0.18
Nodes (20): CapabilityPlan, IntentProfile, IntentProfile, _format_active(), _format_keywords(), _format_tilt_line(), _format_weights(), Goal-anchor prompt block — shared across every generation node.  Every generatio (+12 more)

### Community 73 - "Community 73"
Cohesion: 0.17
Nodes (21): ArchaeologistState, Any, AsyncEngine, IntentProfile, LLMProvider, _capability_planner_node(), _cartographer_node(), _flow_tracer_node() (+13 more)

### Community 75 - "Community 75"
Cohesion: 0.50
Nodes (4): MonkeyPatch, patched_carto_tools(), patched_traverse(), Stub the deterministic tools the Cartographer calls.      The fact bundle is sma

### Community 77 - "Community 77"
Cohesion: 0.20
Nodes (8): LangGraph nodes + capability library.  Phase 2 surface: the six deterministic to, ChunkContent, GraphQueryResult, Shared Pydantic types used across tools, verifier, and Q&A.  These are the typed, Result of ``read_chunks``: a CodeRef paired with the source text it points at., Result of ``graph_metrics``: per-symbol metric pack., Result of ``graph_query``: one row of an entry-points / hubs / layers query., SymbolMetrics

### Community 78 - "Community 78"
Cohesion: 0.29
Nodes (6): ChunkHit, AsyncEngine, LLMProvider, ``vector_search`` — pgvector cosine k-NN over indexed chunks.  Embeds the query, Return the top-``k`` chunks for ``query`` in ``repo_id``., vector_search()

### Community 80 - "Community 80"
Cohesion: 0.15
Nodes (17): BaseSettings, EmbeddingResponse, Provider-agnostic embedding shape., Any, EmbeddingResponse, Path, Settings, AsyncEngine (+9 more)

### Community 81 - "Community 81"
Cohesion: 0.60
Nodes (5): ChunkContent, answer_user_prompt(), Q&A prompt templates.  Three prompts, all under the 2000-token budget from ``doc, _render_chunks(), sufficiency_user_prompt()

### Community 82 - "Community 82"
Cohesion: 0.40
Nodes (5): github_issues(), Issue, ``github_issues`` — Phase 5 dependency, stubbed in Phase 2.  The signature is lo, Subset of the GitHub issue shape Lane A scores on., Phase 5 will implement; raises until then so Lane A fails loudly.

### Community 83 - "Community 83"
Cohesion: 0.50
Nodes (4): Path, _iter_source_files(), Hard CI rule: nothing in the source tree may branch on a ``purpose`` enum.  Phas, test_no_purpose_enum_in_source_tree()

### Community 84 - "Community 84"
Cohesion: 0.50
Nodes (3): QAClaim, Types specific to the Q&A subgraph (sufficiency judge + final answer)., A single grounded claim in the Q&A answer.

## Knowledge Gaps
- **188 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `dev` (+183 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMProvider` connect `Community 18` to `Community 16`, `Community 25`, `Community 28`, `Community 32`, `Community 45`, `Community 46`, `Community 48`, `Community 50`, `Community 51`, `Community 53`, `Community 57`, `Community 60`, `Community 61`, `Community 62`, `Community 65`, `Community 67`, `Community 68`, `Community 70`, `Community 73`, `Community 74`, `Community 75`, `Community 78`, `Community 80`?**
  _High betweenness centrality (0.173) - this node is a cross-community bridge._
- **Why does `ModelId` connect `Community 18` to `Community 32`, `Community 67`, `Community 70`, `Community 28`, `Community 46`, `Community 80`, `Community 48`, `Community 50`, `Community 51`, `Community 16`, `Community 53`, `Community 56`, `Community 57`, `Community 60`, `Community 61`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 80` to `Community 32`, `Community 46`, `Community 18`, `Community 50`, `Community 51`, `Community 53`, `Community 19`, `Community 25`, `Community 60`, `Community 62`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 115 inferred relationships involving `LLMProvider` (e.g. with `Any` and `ArchaeologistState`) actually correct?**
  _`LLMProvider` has 115 INFERRED edges - model-reasoned connections that need verification._
- **Are the 89 inferred relationships involving `ModelId` (e.g. with `AsyncClient` and `ClaimStatus`) actually correct?**
  _`ModelId` has 89 INFERRED edges - model-reasoned connections that need verification._
- **Are the 70 inferred relationships involving `IntentProfile` (e.g. with `ArchaeologistState` and `ClaimStatus`) actually correct?**
  _`IntentProfile` has 70 INFERRED edges - model-reasoned connections that need verification._
- **Are the 70 inferred relationships involving `Message` (e.g. with `ClaimStatus` and `ModelBinding`) actually correct?**
  _`Message` has 70 INFERRED edges - model-reasoned connections that need verification._