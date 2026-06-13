# Graph Report - RepoPilot  (2026-06-14)

## Corpus Check
- 13 files · ~21,740 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 117 nodes · 101 edges · 16 communities (12 shown, 4 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dd705575`
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

## God Nodes (most connected - your core abstractions)
1. `03 — Architecture` - 13 edges
2. `04 — Build Plan` - 10 edges
3. `RepoPilot — Project Guide (Single Source of Truth)` - 9 edges
4. `00 — Claude Build Guide (Standing Context)` - 9 edges
5. `02 — Tech Stack` - 9 edges
6. `05 — Phase Prompts (paste-ready)` - 8 edges
7. `RepoPilot — Project Rules (portable)` - 6 edges
8. `01 — Problem and Solution` - 5 edges
9. `The solution` - 5 edges
10. `Intent Router` - 5 edges

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

## Communities (16 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (12): ArchaeologistState, Cartographer, Contribute Elicitation, Flow Tracer, Intent Router, Learn Elicitation, Q&A Subgraph, Teacher (+4 more)

### Community 1 - "Community 1"
Cohesion: 0.12
Nodes (16): 03 — Architecture, Agent table, Agent topology, Deterministic tools, Failure modes and cost design, How pre-context flows through the system, Hybrid retrieval pattern (the Q&A spine), Iteration 1 — Contribute lanes, in detail (+8 more)

### Community 2 - "Community 2"
Cohesion: 0.20
Nodes (9): 1. What this project is, 2. How project knowledge is organized, 3. Knowledge Graph first (Graphify), 4. Graph maintenance (mandatory), 5. Claude Code harness (`.claude/`), 6. Engineering conventions, 7. Definition of Done, 8. For contributors (human or AI) (+1 more)

### Community 3 - "Community 3"
Cohesion: 0.67
Nodes (3): Phase 1: Ingestion, NetworkX, tree-sitter

### Community 6 - "Community 6"
Cohesion: 0.15
Nodes (12): 00 — Claude Build Guide (Standing Context), Agent roster, Iteration 1 — Contribute = opportunity engine, not issue browser, Iteration 2 — No stat dumps. Output contract, enforced four ways., Per-PR Definition of Done, Pre-context capture runs IN PARALLEL with indexing — never after it, Project one-liner, State schema rules (+4 more)

### Community 7 - "Community 7"
Cohesion: 0.17
Nodes (11): 01 — Problem and Solution, Hard scope fence — what v1 will NOT do, Learn vs. Contribute — what each tour delivers, Success criteria, The beachhead user, The core bet, The five principles (the contract this product lives or dies by), The problem (+3 more)

### Community 8 - "Community 8"
Cohesion: 0.17
Nodes (11): 02 — Tech Stack, ASCII full-stack diagram, Backend layer, Code intelligence layer (deterministic, NO LLM), Frontend layer, Groq free-tier survival strategy, LLM layer, Orchestration layer (+3 more)

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

## Knowledge Gaps
- **85 isolated node(s):** `graphify`, `What this project is`, `Knowledge graph first`, `Graph maintenance (mandatory)`, `Engineering conventions` (+80 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What connects `graphify`, `What this project is`, `Knowledge graph first` to the rest of the system?**
  _85 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._