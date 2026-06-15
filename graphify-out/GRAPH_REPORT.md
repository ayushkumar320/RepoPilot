# Graph Report - RepoPilot  (2026-06-16)

## Corpus Check
- 83 files · ~56,965 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 798 nodes · 1506 edges · 61 communities (47 shown, 14 thin omitted)
- Extraction: 76% EXTRACTED · 24% INFERRED · 0% AMBIGUOUS · INFERRED: 361 edges (avg confidence: 0.53)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `31311b66`
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

## God Nodes (most connected - your core abstractions)
1. `LLMProvider` - 56 edges
2. `ModelId` - 54 edges
3. `Settings` - 51 edges
4. `Message` - 40 edges
5. `ProviderName` - 32 edges
6. `ModelBinding` - 25 edges
7. `Claim` - 23 edges
8. `Chunk` - 21 edges
9. `LLMResponse` - 20 edges
10. `EmbeddingResponse` - 20 edges

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

## Communities (61 total, 14 thin omitted)

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
Cohesion: 0.07
Nodes (57): AsyncClient, Connection, EmbeddingResponse, ModelBinding, ModelId, ProviderName, Logical model identifiers and their physical-model resolution per provider.  Age, Logical, agent-facing model identifiers. (+49 more)

### Community 17 - "Community 17"
Cohesion: 0.17
Nodes (11): 00 — Claude Build Guide (Standing Context) *(the contract)*, 01 — Problem and Solution *(the thesis / "why")*, 02 — Tech Stack *(the toolbox — every choice + why + what was rejected)*, 03 — Architecture *(the blueprint — the keystone doc)*, 04 — Build Plan *(the schedule — 7 phases, each with a hard gate)*, 05 — Phase Prompts *(the script — paste-ready)*, Build progress at a glance, How the doc set fits together (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (20): ProviderName, Shared fixtures for the core package's tests., FakeClient, make_provider(), make_response(), Test double for an LLM provider client., Build an LLMProvider that uses the supplied fakes for every provider., _msgs() (+12 more)

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
Cohesion: 0.21
Nodes (25): BaseSettings, CloneResult, LLMProvider, Single entrypoint to every LLM call in the system., ModuleSource, Chunk, LLMProvider, Settings (+17 more)

### Community 29 - "Community 29"
Cohesion: 0.09
Nodes (24): BaseModel, QAClaim, Types specific to the Q&A subgraph (sufficiency judge + final answer)., A single grounded claim in the Q&A answer., LangGraph nodes + capability library.  Phase 2 surface: the six deterministic to, ChunkContent, ChunkHit, CodeRef (+16 more)

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (49): Node, Path, Path, Path, ParsedFile, ParsedSymbol, chunk_file(), _class_header_content() (+41 more)

### Community 32 - "Community 32"
Cohesion: 0.15
Nodes (20): AsyncEngine, ChunkContent, LLMProvider, _apply(), _Cache, Claim, _objection_if_rejected(), Per-claim grounding check against ``read_chunks``.  The Verifier is the single l (+12 more)

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
Cohesion: 0.16
Nodes (17): EmbeddedChunk, AsyncEngine, Settings, known_head_sha(), make_engine(), persist_index(), PersistResult, Persist Phase 1 pipeline output to Postgres + pgvector.  The functions here are (+9 more)

### Community 47 - "Community 47"
Cohesion: 0.15
Nodes (14): Path, clone_to_tempdir(), parse_github_url(), GitHub clone + HEAD-SHA helpers for Phase 1 ingestion.  Two entry points:  * :fu, Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c, remote_head_sha() (+6 more)

### Community 48 - "Community 48"
Cohesion: 0.24
Nodes (9): Phase 1 — clone -> parse -> chunk -> graph -> embed -> persist., index_repo(), _iter_python_files(), _path_to_module(), End-to-end Phase 1 pipeline orchestrator.  Wires: clone → parse → chunk → graph, Full ingestion pipeline. Idempotent on ``(repo_url, head_sha)``., _scan_python_files(), Phase 1 quality gate: httpx (~50 kLOC) indexes in ≤ 90 s. (+1 more)

### Community 49 - "Community 49"
Cohesion: 0.11
Nodes (13): Any, ChunkContent, CodeRef, Shared fixtures: stubbed engine + LLMProvider for the unit-testable layer.  We c, FakeChunk, FakeEngine, FakeProvider, make_content() (+5 more)

### Community 50 - "Community 50"
Cohesion: 0.40
Nodes (5): github_issues(), Issue, ``github_issues`` — Phase 5 dependency, stubbed in Phase 2.  The signature is lo, Subset of the GitHub issue shape Lane A scores on., Phase 5 will implement; raises until then so Lane A fails loudly.

### Community 51 - "Community 51"
Cohesion: 0.20
Nodes (21): Claim, AsyncEngine, ChunkContent, LLMProvider, answer_question(), _Context, _extend_context(), _generate_answer() (+13 more)

### Community 53 - "Community 53"
Cohesion: 0.15
Nodes (13): Any, ChunkContent, CodeRef, MonkeyPatch, _chunk(), _patch_tools(), End-to-end Q&A tests against fully stubbed dependencies.  We monkey-patch the th, Returns canned text responses in queue order. (+5 more)

### Community 56 - "Community 56"
Cohesion: 0.20
Nodes (14): Any, MonkeyPatch, Verifier tests: JSON parsing, parse-fail rejection (D4), caching (M1)., _StubEngine, _StubProvider, test_parse_verdict_accepts_clean_json(), test_parse_verdict_extracts_json_from_prose(), test_parse_verdict_returns_none_on_garbage() (+6 more)

### Community 57 - "Community 57"
Cohesion: 0.20
Nodes (6): Shared core: settings, logging, and the LLMProvider abstraction., Application settings, loaded from environment / `.env` via pydantic-settings., Batched async embedder over chunks via the central ``LLMProvider``.  The provide, Test 5 from the Phase 0 TDD checklist., `.env.example` shipped at the repo root must be a valid pydantic-settings source, test_settings_loads_from_env_example()

### Community 58 - "Community 58"
Cohesion: 0.29
Nodes (6): ChunkHit, AsyncEngine, LLMProvider, ``vector_search`` — pgvector cosine k-NN over indexed chunks.  Embeds the query, Return the top-``k`` chunks for ``query`` in ``repo_id``., vector_search()

### Community 59 - "Community 59"
Cohesion: 0.60
Nodes (5): ChunkContent, answer_user_prompt(), Q&A prompt templates.  Three prompts, all under the 2000-token budget from ``doc, _render_chunks(), sufficiency_user_prompt()

## Knowledge Gaps
- **177 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `dev` (+172 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `LLMProvider` connect `Community 25` to `Community 32`, `Community 36`, `Community 45`, `Community 46`, `Community 16`, `Community 18`, `Community 51`, `Community 58`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Why does `Settings` connect `Community 25` to `Community 36`, `Community 46`, `Community 16`, `Community 18`, `Community 19`, `Community 57`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `ModelId` connect `Community 16` to `Community 32`, `Community 46`, `Community 18`, `Community 51`, `Community 25`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `LLMProvider` (e.g. with `Any` and `ChunkHit`) actually correct?**
  _`LLMProvider` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Are the 51 inferred relationships involving `ModelId` (e.g. with `AsyncClient` and `Claim`) actually correct?**
  _`ModelId` has 51 INFERRED edges - model-reasoned connections that need verification._
- **Are the 46 inferred relationships involving `Settings` (e.g. with `AsyncClient` and `CloneResult`) actually correct?**
  _`Settings` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `Message` (e.g. with `Claim` and `ModelBinding`) actually correct?**
  _`Message` has 32 INFERRED edges - model-reasoned connections that need verification._