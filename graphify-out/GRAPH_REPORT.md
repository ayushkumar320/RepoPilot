# Graph Report - CodebaseArchiologist  (2026-06-17)

## Corpus Check
- 96 files · ~64,839 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1007 nodes · 2036 edges · 65 communities (53 shown, 12 thin omitted)
- Extraction: 75% EXTRACTED · 25% INFERRED · 0% AMBIGUOUS · INFERRED: 511 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `64571640`
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

## God Nodes (most connected - your core abstractions)
1. `LLMProvider` - 68 edges
2. `Settings` - 67 edges
3. `ModelId` - 61 edges
4. `Message` - 47 edges
5. `ProviderName` - 35 edges
6. `Claim` - 33 edges
7. `EmbeddingResponse` - 28 edges
8. `ModelBinding` - 25 edges
9. `VerifierVerdict` - 23 edges
10. `LLMResponse` - 23 edges

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

## Communities (65 total, 12 thin omitted)

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
Cohesion: 0.12
Nodes (32): _coerce_keywords(), _coerce_modality_weights(), _coerce_optional_str(), _coerce_output_shape(), _fallback_profile(), _parse_json(), profile_intent(), Intent Profiler — free-text intent → structured ``IntentProfile``.  The Profiler (+24 more)

### Community 17 - "Community 17"
Cohesion: 0.17
Nodes (11): 00 — Claude Build Guide (Standing Context) *(the contract)*, 01 — Problem and Solution *(the thesis / "why")*, 02 — Tech Stack *(the toolbox — every choice + why + what was rejected)*, 03 — Architecture *(the blueprint — the keystone doc)*, 04 — Build Plan *(the schedule — 7 phases, each with a hard gate)*, 05 — Phase Prompts *(the script — paste-ready)*, Build progress at a glance, How the doc set fits together (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.14
Nodes (32): BaseSettings, ModelId, Logical, agent-facing model identifiers., EmbeddingResponse, LLMProvider, Message, Single entrypoint to every LLM call in the system., Provider-agnostic embedding shape. (+24 more)

### Community 19 - "Community 19"
Cohesion: 0.13
Nodes (14): EventDict, FastAPI, Any, create_app(), FastAPI scaffold — health-check only in Phase 0., FastAPI app entrypoint. Endpoints are added in Phase 4., configure_logging(), _drop_chunk_content() (+6 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (18): dependencies, next, react, react-dom, devDependencies, @types/node, @types/react, @types/react-dom (+10 more)

### Community 22 - "Community 22"
Cohesion: 0.18
Nodes (10): Current Build Phase, How to advance the phase, Phase 0 — what landed, Phase 1 — what landed, Phase 2 — what landed (most recent), Phase 3 — entry checklist (the active block), Phase 3 — kickoff outline (read after entry checklist clears), Phase ladder (+2 more)

### Community 23 - "Community 23"
Cohesion: 0.40
Nodes (4): Quickstart (local dev), Repo layout, RepoPilot, Status

### Community 25 - "Community 25"
Cohesion: 0.33
Nodes (11): CloneResult, ModuleSource, Chunk, LLMProvider, Path, Settings, Chunk, One indexable unit of source. Line numbers are 1-based, inclusive. (+3 more)

### Community 28 - "Community 28"
Cohesion: 0.05
Nodes (68): Claim, AsyncEngine, ChunkContent, LLMProvider, Any, ChunkContent, CodeRef, MonkeyPatch (+60 more)

### Community 29 - "Community 29"
Cohesion: 0.05
Nodes (45): ChunkHit, ChunkContent, AsyncEngine, LLMProvider, Any, MonkeyPatch, answer_user_prompt(), Q&A prompt templates.  Three prompts, all under the 2000-token budget from ``doc (+37 more)

### Community 30 - "Community 30"
Cohesion: 0.06
Nodes (55): BaseModel, CapabilityName, CodeRef, CodeRef, QAClaim, Types specific to the Q&A subgraph (sufficiency judge + final answer)., A single grounded claim in the Q&A answer., ArchaeologistError (+47 more)

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (49): Node, Path, Path, Path, ParsedFile, ParsedSymbol, chunk_file(), _class_header_content() (+41 more)

### Community 32 - "Community 32"
Cohesion: 0.17
Nodes (22): RateLimitError, HTTP 429 from a provider — triggers retry/fallback inside the provider., ProviderName, Shared fixtures for the core package's tests., Message, FakeClient, make_provider(), make_response() (+14 more)

### Community 36 - "Community 36"
Cohesion: 0.30
Nodes (10): MonkeyPatch, PipelineResult, Decide whether ``repo_url`` is already-current, stale, or unknown.      Cheap —, revisit_status(), Idempotency + staleness — exercised against a stubbed DB and stubbed clone.  The, When the remote HEAD has moved past the indexed SHA → status=stale., _StubEngine, test_revisit_unknown_repo_returns_stale() (+2 more)

### Community 37 - "Community 37"
Cohesion: 0.07
Nodes (34): AST, AsyncFunctionDef, Call, ClassDef, FunctionDef, Import, ImportFrom, Module (+26 more)

### Community 38 - "Community 38"
Cohesion: 0.20
Nodes (20): GraphQueryResult, AsyncEngine, DiGraph, QueryKind, _prime_cache(), Tests for ``graph_query``: entry points, hubs, callers/callees, layers.  Exercis, test_callees_of_a(), test_callers_of_c() (+12 more)

### Community 39 - "Community 39"
Cohesion: 0.20
Nodes (5): Animal, Dog, Fixture file the chunker tests assert against. Real Python so AST is exact., A base class with one method., A subclass overriding speak().

### Community 40 - "Community 40"
Cohesion: 0.05
Nodes (36): Alembic environment — uses Settings.postgres_dsn so dev + CI agree., AsyncEngine, DiGraph, AsyncEngine, AsyncEngine, CodeRef, Path, AsyncEngine (+28 more)

### Community 45 - "Community 45"
Cohesion: 0.28
Nodes (8): Any, index_repo(), arq worker function for the Phase 1 ingestion pipeline.  The actual pipeline log, arq job: index a GitHub repo end-to-end. Returns a JSON-able status dict., arq discovery target. Run with: ``arq repopilot_api.jobs.index_repo.WorkerSettin, shutdown(), startup(), WorkerSettings

### Community 46 - "Community 46"
Cohesion: 0.18
Nodes (15): EmbeddedChunk, AsyncEngine, Settings, known_head_sha(), make_engine(), persist_index(), PersistResult, Persist Phase 1 pipeline output to Postgres + pgvector.  The functions here are (+7 more)

### Community 47 - "Community 47"
Cohesion: 0.11
Nodes (18): Path, clone_to_tempdir(), parse_github_url(), GitHub clone + HEAD-SHA helpers for Phase 1 ingestion.  Two entry points:  * :fu, Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c, remote_head_sha() (+10 more)

### Community 48 - "Community 48"
Cohesion: 0.25
Nodes (9): embed_chunks(), Batched async embedder over chunks via the central ``LLMProvider``.  The provide, Embed every chunk; results are returned in the same order as ``chunks``., index_repo(), _iter_python_files(), _path_to_module(), End-to-end Phase 1 pipeline orchestrator.  Wires: clone → parse → chunk → graph, Full ingestion pipeline. Idempotent on ``(repo_url, head_sha)``. (+1 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (13): Any, ChunkContent, CodeRef, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, FakeChunk, FakeEngine, FakeProvider, make_content() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.14
Nodes (14): _backoff_delay(), _BaseClient, _cache_key(), LLMResponse, The single LLMProvider every agent goes through.  Responsibilities (Phase 0 deli, Exponential backoff with full jitter. attempt=0 is the first retry., Common interface for provider HTTP shims., In-process embedder using sentence-transformers (Hugging Face weights).      No (+6 more)

### Community 51 - "Community 51"
Cohesion: 0.21
Nodes (9): Connection, ProviderError, Thread-safe SQLite cache keyed on the canonical request hash., Generate a completion. Hits cache first; otherwise walks the fallback chain., Embed ``text`` via the in-process sentence-transformers embedder.          No HT, All providers in the fallback chain failed., _SQLiteCache, ModelId (+1 more)

### Community 53 - "Community 53"
Cohesion: 0.19
Nodes (11): GroundingEvalRow, Settings, QAResult, _contains_all_keywords(), GroundingEvalCaseResult, GroundingEvalMetrics, _has_expected_refs(), _is_hallucination_safe() (+3 more)

### Community 56 - "Community 56"
Cohesion: 0.20
Nodes (11): ModelBinding, Logical model identifiers and their physical-model resolution per provider.  Age, The concrete model name to send to a given provider for one `ModelId`., Any, EmbeddingResponse, ModelBinding, FakeEmbedder, Tests for ``LLMProvider.embed()`` — cache hit, fresh embed, dim contract. (+3 more)

### Community 57 - "Community 57"
Cohesion: 0.20
Nodes (8): Path, Shared core: settings, logging, and the LLMProvider abstraction., _find_repo_env(), Application settings, loaded from environment / `.env` via pydantic-settings., Walk up from this file to the repo root and return the ``.env`` path.      Lets, Test 5 from the Phase 0 TDD checklist., `.env.example` shipped at the repo root must be a valid pydantic-settings source, test_settings_loads_from_env_example()

### Community 58 - "Community 58"
Cohesion: 0.22
Nodes (13): IntentProfileEvalRow, Path, PlannerEvalRow, dataset_path(), load_grounding_dataset(), load_intent_dataset(), load_jsonl_rows(), load_planner_dataset() (+5 more)

### Community 59 - "Community 59"
Cohesion: 0.19
Nodes (16): EvalSpec, GroundingEvalMetrics, Namespace, Path, _cmd_list(), _grounding_markdown(), main(), _print_grounding() (+8 more)

### Community 60 - "Community 60"
Cohesion: 0.22
Nodes (12): AsyncClient, ProviderName, _OpenAICompatibleClient, Speaks the OpenAI chat-completions shape. Used for Groq and Cerebras., Default wiring used by the app. Tests pass `clients` for full control., ProviderName, Settings, Path (+4 more)

### Community 61 - "Community 61"
Cohesion: 0.26
Nodes (11): Any, Path, _cmd_status(), _coerce(), _ensure_reports_dir(), find_latest_report(), _now_stamp(), Persisted eval reports.  Each eval run writes a timestamped JSON + Markdown pair (+3 more)

### Community 62 - "Community 62"
Cohesion: 0.30
Nodes (9): Settings, Eval runners for the phase gates., _patched_read_chunks(), Verifier-quality eval runner for the Phase 2 gate., run_verifier_eval(), run_verifier_eval_rows(), VerifierEvalCaseResult, VerifierEvalMetrics (+1 more)

### Community 63 - "Community 63"
Cohesion: 0.40
Nodes (4): build_eval_context(), EvalContext, Shared runtime helpers for eval runners., resolve_repo_id()

## Knowledge Gaps
- **186 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `dev` (+181 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMProvider` connect `Community 18` to `Community 32`, `Community 36`, `Community 45`, `Community 60`, `Community 46`, `Community 16`, `Community 50`, `Community 51`, `Community 56`, `Community 25`, `Community 28`, `Community 29`, `Community 63`?**
  _High betweenness centrality (0.125) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 18` to `Community 32`, `Community 36`, `Community 46`, `Community 50`, `Community 51`, `Community 19`, `Community 53`, `Community 25`, `Community 60`, `Community 63`, `Community 62`, `Community 57`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `ModelId` connect `Community 18` to `Community 32`, `Community 28`, `Community 46`, `Community 16`, `Community 50`, `Community 51`, `Community 56`, `Community 60`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 61 inferred relationships involving `LLMProvider` (e.g. with `Any` and `ChunkHit`) actually correct?**
  _`LLMProvider` has 61 INFERRED edges - model-reasoned connections that need verification._
- **Are the 61 inferred relationships involving `Settings` (e.g. with `AsyncClient` and `CloneResult`) actually correct?**
  _`Settings` has 61 INFERRED edges - model-reasoned connections that need verification._
- **Are the 58 inferred relationships involving `ModelId` (e.g. with `AsyncClient` and `Claim`) actually correct?**
  _`ModelId` has 58 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `Message` (e.g. with `Claim` and `IntentProfile`) actually correct?**
  _`Message` has 39 INFERRED edges - model-reasoned connections that need verification._