# Graph Report - RepoPilot  (2026-06-16)

## Corpus Check
- 64 files · ~47,096 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 578 nodes · 1070 edges · 45 communities (34 shown, 11 thin omitted)
- Extraction: 76% EXTRACTED · 24% INFERRED · 0% AMBIGUOUS · INFERRED: 254 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a684bd78`
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
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 42|Community 42]]

## God Nodes (most connected - your core abstractions)
1. `Settings` - 51 edges
2. `ModelId` - 38 edges
3. `LLMProvider` - 37 edges
4. `ProviderName` - 32 edges
5. `ModelBinding` - 25 edges
6. `Message` - 24 edges
7. `Chunk` - 21 edges
8. `LLMResponse` - 20 edges
9. `EmbeddingResponse` - 20 edges
10. `FakeClient` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Any` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `Any` --uses--> `PipelineResult`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/ingestion/src/repopilot_ingestion/pipeline.py
- `WorkerSettings` --uses--> `LLMProvider`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/core/src/repopilot_core/llm/provider.py
- `WorkerSettings` --uses--> `PipelineResult`  [INFERRED]
  apps/api/src/repopilot_api/jobs/index_repo.py → packages/ingestion/src/repopilot_ingestion/pipeline.py
- `create_app()` --calls--> `configure_logging()`  [EXTRACTED]
  apps/api/src/repopilot_api/app.py → packages/core/src/repopilot_core/logging.py

## Import Cycles
- 1-file cycle: `apps/api/src/repopilot_api/app.py -> apps/api/src/repopilot_api/app.py`

## Communities (45 total, 11 thin omitted)

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
Cohesion: 0.22
Nodes (8): 05 — Phase Prompts (paste-ready), Phase 0 prompt — Foundation, Phase 1 prompt — Ingestion, Phase 2 prompt — Hybrid Retrieval + Grounded Q&A (the spine), Phase 3 prompt — Orchestration + Learn subgraph, Phase 4 prompt — Experience (FastAPI + Next.js + synchronized code viewer), Phase 5 prompt — Contribute mode (Iteration 1), Phase 6 prompt — Harden and ship

### Community 13 - "Community 13"
Cohesion: 0.29
Nodes (6): Authoring, Engineering conventions, Graph maintenance (mandatory), Knowledge graph first, RepoPilot — Project Rules (portable), What this project is

### Community 14 - "Community 14"
Cohesion: 0.50
Nodes (3): Constraints, Mandatory order of operations, What to return

### Community 16 - "Community 16"
Cohesion: 0.08
Nodes (52): AsyncClient, Connection, EmbeddingResponse, ModelBinding, ModelId, ProviderName, Logical model identifiers and their physical-model resolution per provider.  Age, Logical, agent-facing model identifiers. (+44 more)

### Community 17 - "Community 17"
Cohesion: 0.18
Nodes (10): 00 — Claude Build Guide (Standing Context) *(the contract)*, 01 — Problem and Solution *(the thesis / "why")*, 02 — Tech Stack *(the toolbox — every choice + why + what was rejected)*, 03 — Architecture *(the blueprint — the keystone doc)*, 04 — Build Plan *(the schedule — 7 phases, each with a hard gate)*, 05 — Phase Prompts *(the script — paste-ready)*, How the doc set fits together, One-paragraph takeaway (+2 more)

### Community 18 - "Community 18"
Cohesion: 0.16
Nodes (22): _backoff_delay(), Exponential backoff with full jitter. attempt=0 is the first retry., ProviderName, FakeClient, make_provider(), make_response(), Shared fixtures for the core package's tests., Test double for an LLM provider client. (+14 more)

### Community 19 - "Community 19"
Cohesion: 0.10
Nodes (20): Any, EventDict, FastAPI, index_repo(), arq worker function for the Phase 1 ingestion pipeline.  The actual pipeline log, arq job: index a GitHub repo end-to-end. Returns a JSON-able status dict., shutdown(), startup() (+12 more)

### Community 20 - "Community 20"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 21 - "Community 21"
Cohesion: 0.11
Nodes (18): dependencies, next, react, react-dom, devDependencies, @types/node, @types/react, @types/react-dom (+10 more)

### Community 22 - "Community 22"
Cohesion: 0.29
Nodes (6): Current Build Phase, How to advance the phase, Pending Phase 0 verifications (host-bound, do these on your machine), Phase 0 — what landed, Phase 1 — kickoff checklist, Phase ladder

### Community 23 - "Community 23"
Cohesion: 0.40
Nodes (4): Quickstart (local dev), Repo layout, RepoPilot, Status

### Community 25 - "Community 25"
Cohesion: 0.07
Nodes (60): AsyncEngine, BaseSettings, CloneResult, EmbeddedChunk, arq discovery target. Run with: ``arq repopilot_api.jobs.index_repo.WorkerSettin, WorkerSettings, EmbeddingResponse, LLMProvider (+52 more)

### Community 31 - "Community 31"
Cohesion: 0.08
Nodes (50): Node, Path, Path, Path, ParsedFile, ParsedSymbol, chunk_file(), _class_header_content() (+42 more)

### Community 36 - "Community 36"
Cohesion: 0.09
Nodes (25): MonkeyPatch, Path, clone_to_tempdir(), parse_github_url(), GitHub clone + HEAD-SHA helpers for Phase 1 ingestion.  Two entry points:  * :fu, Return ``(owner, name)`` for a public GitHub URL.      Raises ``ValueError`` for, Return the current default-branch HEAD SHA via ``git ls-remote HEAD``.      Used, Shallow-clone ``repo_url`` into a tempdir; clean up on exit.      The yielded :c (+17 more)

### Community 37 - "Community 37"
Cohesion: 0.15
Nodes (24): DiGraph, Module, build_graph(), _DefSymbol, graph_to_adjacency(), ModuleSource, NetworkX dependency graph builder.  Edges (Phase 1, deterministic — the LLM neve, Resolved module info handed to the graph builder. (+16 more)

### Community 38 - "Community 38"
Cohesion: 0.13
Nodes (10): AST, AsyncFunctionDef, Call, ClassDef, FunctionDef, Import, ImportFrom, Walk one module and emit edges into typed lists.      Scope tracking is minimal (+2 more)

### Community 39 - "Community 39"
Cohesion: 0.20
Nodes (5): Animal, Dog, Fixture file the chunker tests assert against. Real Python so AST is exact., A base class with one method., A subclass overriding speak().

### Community 40 - "Community 40"
Cohesion: 0.20
Nodes (4): Alembic environment — uses Settings.postgres_dsn so dev + CI agree., SQLAlchemy schema for Phase 1 ingestion.  Tables:     repos              one row, Minimal pgvector type so alembic can emit `vector(N)` without importing     the, Vector

## Knowledge Gaps
- **161 isolated node(s):** `nextConfig`, `name`, `private`, `version`, `dev` (+156 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Community 25` to `Community 16`, `Community 18`, `Community 19`?**
  _High betweenness centrality (0.082) - this node is a cross-community bridge._
- **Why does `LLMProvider` connect `Community 25` to `Community 16`, `Community 18`, `Community 19`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `_Resolver` connect `Community 38` to `Community 37`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 46 inferred relationships involving `Settings` (e.g. with `AsyncClient` and `AsyncEngine`) actually correct?**
  _`Settings` has 46 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `ModelId` (e.g. with `AsyncClient` and `Connection`) actually correct?**
  _`ModelId` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `LLMProvider` (e.g. with `Any` and `CloneResult`) actually correct?**
  _`LLMProvider` has 29 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `ProviderName` (e.g. with `AsyncClient` and `Connection`) actually correct?**
  _`ProviderName` has 30 INFERRED edges - model-reasoned connections that need verification._