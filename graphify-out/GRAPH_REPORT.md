# Graph Report - CodebaseArchiologist  (2026-06-16)

## Corpus Check
- 91 files · ~61,211 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 917 nodes · 1827 edges · 67 communities (56 shown, 11 thin omitted)
- Extraction: 74% EXTRACTED · 26% INFERRED · 0% AMBIGUOUS · INFERRED: 467 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3a1e6893`
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

## God Nodes (most connected - your core abstractions)
1. `Settings` - 67 edges
2. `LLMProvider` - 61 edges
3. `ModelId` - 57 edges
4. `Message` - 43 edges
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

## Communities (67 total, 11 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (12): ArchaeologistState, Cartographer, Contribute Elicitation, Flow Tracer, Intent Router, Learn Elicitation, Q&A Subgraph, Teacher (+4 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (24): 03 — Architecture, Agent table, Agent topology, Capability dependencies, Deterministic tools, Failure modes and cost design, How the intent profile flows through the system, Hybrid retrieval pattern (the Q&A spine) (+16 more)

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
Cohesion: 0.15
Nodes (16): AsyncClient, Connection, ModelBinding, Logical model identifiers and their physical-model resolution per provider.  Age, The concrete model name to send to a given provider for one `ModelId`., _BaseClient, _OpenAICompatibleClient, Thread-safe SQLite cache keyed on the canonical request hash. (+8 more)

### Community 17 - "Community 17"
Cohesion: 0.17
Nodes (11): 00 — Claude Build Guide (Standing Context) *(the contract)*, 01 — Problem and Solution *(the thesis / "why")*, 02 — Tech Stack *(the toolbox — every choice + why + what was rejected)*, 03 — Architecture *(the blueprint — the keystone doc)*, 04 — Build Plan *(the schedule — 7 phases, each with a hard gate)*, 05 — Phase Prompts *(the script — paste-ready)*, Build progress at a glance, How the doc set fits together (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (22): RateLimitError, HTTP 429 from a provider — triggers retry/fallback inside the provider., ProviderName, Shared fixtures for the core package's tests., Message, FakeClient, make_provider(), make_response() (+14 more)

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
Cohesion: 0.22
Nodes (8): Current Build Phase, How to advance the phase, Phase 0 — what landed, Phase 1 — what landed, Phase 2 — what landed (most recent), Phase 3 — entry checklist (the active block), Phase 3 — kickoff outline (read after entry checklist clears), Phase ladder

### Community 23 - "Community 23"
Cohesion: 0.40
Nodes (4): Quickstart (local dev), Repo layout, RepoPilot, Status

### Community 25 - "Community 25"
Cohesion: 0.20
Nodes (23): BaseSettings, CloneResult, LLMProvider, Single entrypoint to every LLM call in the system., ModuleSource, AsyncEngine, Settings, Chunk (+15 more)

### Community 28 - "Community 28"
Cohesion: 0.18
Nodes (19): MonkeyPatch, Path, QAResult, The end-to-end output of one Q&A run., GroundingEvalRow, VerifierEvalRow, _async_return(), _dataset_path() (+11 more)

### Community 29 - "Community 29"
Cohesion: 0.11
Nodes (21): BaseModel, LangGraph nodes + capability library.  Phase 2 surface: the six deterministic to, ChunkContent, ChunkHit, CodeRef, GraphQueryResult, Path, Shared Pydantic types used across tools, verifier, and Q&A.  These are the typed (+13 more)

### Community 30 - "Community 30"
Cohesion: 0.18
Nodes (15): IntentProfileEvalRow, Path, PlannerEvalRow, dataset_path(), IntentProfileEvalRow, load_grounding_dataset(), load_intent_dataset(), load_jsonl_rows() (+7 more)

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (49): Node, Path, Path, Path, ParsedFile, ParsedSymbol, chunk_file(), _class_header_content() (+41 more)

### Community 32 - "Community 32"
Cohesion: 0.15
Nodes (20): AsyncEngine, ChunkContent, LLMProvider, _apply(), _Cache, Claim, _objection_if_rejected(), Per-claim grounding check against ``read_chunks``.  The Verifier is the single l (+12 more)

### Community 36 - "Community 36"
Cohesion: 0.22
Nodes (13): MonkeyPatch, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, remote_head_sha(), PipelineResult, Decide whether ``repo_url`` is already-current, stale, or unknown.      Cheap —, revisit_status(), RuntimeError, Idempotency + staleness — exercised against a stubbed DB and stubbed clone.  The (+5 more)

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
Nodes (21): Path, clone_to_tempdir(), parse_github_url(), GitHub clone + HEAD-SHA helpers for Phase 1 ingestion.  Two entry points:  * :fu, Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c, Phase 1 — clone -> parse -> chunk -> graph -> embed -> persist., index_repo() (+13 more)

### Community 48 - "Community 48"
Cohesion: 0.17
Nodes (10): _cache_key(), LLMResponse, In-process embedder using sentence-transformers (Hugging Face weights).      No, Generate a completion. Hits cache first; otherwise walks the fallback chain., Per-binding 429 retry loop with exponential backoff + jitter., Provider-agnostic response shape., _SentenceTransformersEmbedder, ModelId (+2 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (13): Any, ChunkContent, CodeRef, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, FakeChunk, FakeEngine, FakeProvider, make_content() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.40
Nodes (5): github_issues(), Issue, ``github_issues`` — Phase 5 dependency, stubbed in Phase 2.  The signature is lo, Subset of the GitHub issue shape Lane A scores on., Phase 5 will implement; raises until then so Lane A fails loudly.

### Community 51 - "Community 51"
Cohesion: 0.21
Nodes (21): Claim, ModelId, Logical, agent-facing model identifiers., Message, AsyncEngine, ChunkContent, LLMProvider, CodeRef (+13 more)

### Community 53 - "Community 53"
Cohesion: 0.07
Nodes (33): ChunkHit, ChunkContent, AsyncEngine, LLMProvider, Any, ChunkContent, CodeRef, MonkeyPatch (+25 more)

### Community 56 - "Community 56"
Cohesion: 0.20
Nodes (14): Any, MonkeyPatch, Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)., _StubEngine, _StubProvider, test_parse_verdict_accepts_clean_json(), test_parse_verdict_extracts_json_from_prose(), test_parse_verdict_returns_none_on_garbage() (+6 more)

### Community 57 - "Community 57"
Cohesion: 0.17
Nodes (9): Path, Shared core: settings, logging, and the LLMProvider abstraction., _find_repo_env(), Application settings, loaded from environment / `.env` via pydantic-settings., Walk up from this file to the repo root and return the ``.env`` path.      Lets, Batched async embedder over chunks via the central ``LLMProvider``.  The provide, Test 5 from the Phase 0 TDD checklist., `.env.example` shipped at the repo root must be a valid pydantic-settings source (+1 more)

### Community 58 - "Community 58"
Cohesion: 0.15
Nodes (14): ProviderName, EmbeddingResponse, Embed ``text`` via the in-process sentence-transformers embedder.          No HT, Provider-agnostic embedding shape., LLMResponse, Any, EmbeddingResponse, LLMProvider (+6 more)

### Community 59 - "Community 59"
Cohesion: 0.19
Nodes (16): EvalSpec, GroundingEvalMetrics, Namespace, Path, _cmd_list(), _grounding_markdown(), main(), _print_grounding() (+8 more)

### Community 60 - "Community 60"
Cohesion: 0.19
Nodes (11): GroundingEvalRow, Settings, QAResult, _contains_all_keywords(), GroundingEvalCaseResult, GroundingEvalMetrics, _has_expected_refs(), _is_hallucination_safe() (+3 more)

### Community 61 - "Community 61"
Cohesion: 0.24
Nodes (11): Settings, take_rows(), Eval runners for the phase gates., _patched_read_chunks(), Verifier-quality eval runner for the Phase 2 gate., run_verifier_eval(), run_verifier_eval_rows(), VerifierEvalCaseResult (+3 more)

### Community 62 - "Community 62"
Cohesion: 0.26
Nodes (8): Any, EmbeddingResponse, ModelBinding, FakeEmbedder, Tests for ``LLMProvider.embed()`` — cache hit, fresh embed, dim contract., Test double — bypasses the sentence-transformers model load and     returns cann, test_embed_cache_hit_skips_provider(), test_embed_returns_vector()

### Community 63 - "Community 63"
Cohesion: 0.26
Nodes (11): Any, Path, _cmd_status(), _coerce(), _ensure_reports_dir(), find_latest_report(), _now_stamp(), Persisted eval reports.  Each eval run writes a timestamped JSON + Markdown pair (+3 more)

### Community 64 - "Community 64"
Cohesion: 0.29
Nodes (6): _backoff_delay(), ProviderError, The single LLMProvider every agent goes through.  Responsibilities (Phase 0 deli, Exponential backoff with full jitter. attempt=0 is the first retry., All providers in the fallback chain failed., test_backoff_delay_is_bounded()

### Community 65 - "Community 65"
Cohesion: 0.40
Nodes (4): build_eval_context(), EvalContext, Shared runtime helpers for eval runners., resolve_repo_id()

### Community 66 - "Community 66"
Cohesion: 0.50
Nodes (3): QAClaim, Types specific to the Q&A subgraph (sufficiency judge + final answer)., A single grounded claim in the Q&A answer.

## Knowledge Gaps
- **180 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `dev` (+175 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMProvider` connect `Community 25` to `Community 64`, `Community 32`, `Community 65`, `Community 36`, `Community 45`, `Community 46`, `Community 16`, `Community 48`, `Community 18`, `Community 51`, `Community 53`, `Community 58`, `Community 28`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 25` to `Community 64`, `Community 65`, `Community 36`, `Community 46`, `Community 16`, `Community 48`, `Community 18`, `Community 51`, `Community 19`, `Community 57`, `Community 58`, `Community 60`, `Community 61`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `ModelId` connect `Community 51` to `Community 64`, `Community 32`, `Community 46`, `Community 16`, `Community 48`, `Community 18`, `Community 53`, `Community 25`, `Community 58`, `Community 28`, `Community 62`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 61 inferred relationships involving `Settings` (e.g. with `AsyncClient` and `CloneResult`) actually correct?**
  _`Settings` has 61 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `LLMProvider` (e.g. with `Any` and `ChunkHit`) actually correct?**
  _`LLMProvider` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `ModelId` (e.g. with `AsyncClient` and `Claim`) actually correct?**
  _`ModelId` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `Message` (e.g. with `Claim` and `ModelBinding`) actually correct?**
  _`Message` has 35 INFERRED edges - model-reasoned connections that need verification._