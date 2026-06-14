# Graph Report - RepoPilot  (2026-06-15)

## Corpus Check
- 15 files · ~38,910 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 183 nodes · 165 edges · 20 communities (16 shown, 4 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dfed0955`
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

## God Nodes (most connected - your core abstractions)
1. `03 — Architecture` - 18 edges
2. `Second-pass review additions (2026-06-14)` - 12 edges
3. `00 — Claude Build Guide (Standing Context)` - 10 edges
4. `The solution` - 10 edges
5. `04 — Build Plan` - 10 edges
6. `RepoPilot — Project Guide (Single Source of Truth)` - 9 edges
7. `02 — Tech Stack` - 9 edges
8. `06 — Future Improvements (Pre-Build Review)` - 9 edges
9. `05 — Phase Prompts (paste-ready)` - 8 edges
10. `Per-doc summaries` - 8 edges

## Surprising Connections (you probably didn't know these)
- `Intent Router` --references--> `Groq`  [EXTRACTED]
  docs/03_ARCHITECTURE.md → docs/02_TECH_STACK.md
- `Intent Router` --references--> `LangGraph`  [EXTRACTED]
  docs/03_ARCHITECTURE.md → docs/02_TECH_STACK.md
- `Verifier` --references--> `Ollama`  [EXTRACTED]
  docs/03_ARCHITECTURE.md → docs/02_TECH_STACK.md
- `Phase 1: Ingestion` --references--> `tree-sitter`  [EXTRACTED]
  docs/04_BUILD_PLAN.md → docs/02_TECH_STACK.md
- `Phase 1: Ingestion` --references--> `NetworkX`  [EXTRACTED]
  docs/04_BUILD_PLAN.md → docs/02_TECH_STACK.md

## Import Cycles
- None detected.

## Communities (20 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (12): ArchaeologistState, Cartographer, Contribute Elicitation, Flow Tracer, Intent Router, Learn Elicitation, Q&A Subgraph, Teacher (+4 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (23): 03 — Architecture, Agent table, Agent topology, Capability dependencies, Deterministic tools, Failure modes and cost design, How the intent profile flows through the system, Hybrid retrieval pattern (the Q&A spine) (+15 more)

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
Cohesion: 0.11
Nodes (17): 06 — Future Improvements (Pre-Build Review), Application order, How to use this document, Important — fix before the phase where it bites, S1. Mermaid generation is unverifiable and can lie confidently, S2. Per-tour Groq token budget hasn't been calculated; launch concurrency will stall, S3. Intent Profiler has no edit-loop fallback when chip-strip iteration fails, S4. Prompt injection from repo contents isn't acknowledged (+9 more)

### Community 17 - "Community 17"
Cohesion: 0.17
Nodes (11): 00 — Claude Build Guide (Standing Context) *(the contract)*, 01 — Problem and Solution *(the thesis / "why")*, 02 — Tech Stack *(the toolbox — every choice + why + what was rejected)*, 03 — Architecture *(the blueprint — the keystone doc)*, 04 — Build Plan *(the schedule — 7 phases, each with a hard gate)*, 05 — Phase Prompts *(the script — paste-ready)*, 06 — Future Improvements *(the pre-build punch list)*, How the doc set fits together (+3 more)

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (12): M6. Failure modes catalog is thin; the architecture is hand-wavy on partial failures, M7. Decision Archaeology was added as a capability but Phase 3 doesn't include building it, S10. Indexing edge cases (Python 2, `.pyi`, `.ipynb`, vendored deps, generated code) are unspecified, S11. Embedding model versioning + migration story is missing, S12. Concurrent indexing of the same repo is a race condition, S7. Auth, rate-limiting, and GitHub API token sourcing is undefined — Lane A breaks on day one, S8. The "retrieval-path chip on every claim" claim is too broad, S9. No user-feedback mechanism in v1 — we'll learn nothing outside the eval set (+4 more)

### Community 19 - "Community 19"
Cohesion: 0.33
Nodes (6): Critical — must fix before Phase 0, M1. Verifier latency on local Ollama isn't quantified and will blow the Phase 3 gate, M2. Eval dataset labeling is ~30 hours of skilled manual work and isn't on any timeline, M3. Capability "independence" claim is false; the Planner needs a dependency DAG, M4. Phase 4 (Experience) is undersized; realistic budget is 10–14 days, M5. Inconsistent beachhead language between docs/00 and docs/01

## Knowledge Gaps
- **139 isolated node(s):** `graphify`, `What this project is`, `Knowledge graph first`, `Graph maintenance (mandatory)`, `Engineering conventions` (+134 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `06 — Future Improvements (Pre-Build Review)` connect `Community 16` to `Community 18`, `Community 19`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `Second-pass review additions (2026-06-14)` connect `Community 18` to `Community 16`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **What connects `graphify`, `What this project is`, `Knowledge graph first` to the rest of the system?**
  _139 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._
- **Should `Community 6` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Should `Community 7` be split into smaller, more focused modules?**
  _Cohesion score 0.09523809523809523 - nodes in this community are weakly interconnected._
- **Should `Community 16` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._