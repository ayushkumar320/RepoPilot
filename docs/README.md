# RepoPilot — Docs

The product slice (clone → index → retrieve → answer → verify) ships on `main`. Current focus: **measured retrieval quality**, driven by [`RAG_PLAN.md`](RAG_PLAN.md). **Next build: RAG Phase 1 — Recall Lift** (see [`CURRENT_PHASE.md`](CURRENT_PHASE.md)).

> Prefer the [Graphify knowledge graph](../graphify-out/) over reading raw — `graphify query "<question>"`. Project rules live in [`../CLAUDE.md`](../CLAUDE.md); this is the human-readable map.

## The one-paragraph story

Phase 0 baselined the shipped pipeline and found its bottleneck: a k=8 candidate pool that misses gold chunks (some ranked beyond 150). The remaining phases fix that in dependency order — **widen the pool (1)**, **widen what queries catch (2, 3)**, **fix the ordering (4)**, **shrink the prompt cost (5)**, **enrich the corpus (6)** — then **lock it in with a CI regression gate (7)**. Each phase lands only with a measured, significant lift over the previous landed phase; otherwise it's reverted. Phases 1+3+4 are the must-ship minimum; 2, 5, 6 are timeboxed polish.

## Read in order (cold pickup)

1. [`CURRENT_PHASE.md`](CURRENT_PHASE.md) — next build purpose, the improvement chain, active-phase entry state.
2. [`RAG_PLAN.md`](RAG_PLAN.md) — the 7-phase plan: measurement spine, metrics, sequencing rationale, Definition of Done.
3. [`rag/README.md`](rag/README.md) — phase-ladder index: iron rules, timeboxes, priorities, bench commands.
4. The active phase's spec in [`rag/`](rag/) — spec + executable build prompt in one; hand it to a coding agent.
5. [`rag/00_TODAY_PLAN.md`](rag/00_TODAY_PLAN.md) — the 2-day ship schedule and cut lines.

## Layout

```
docs/
├── README.md              this file — the map
├── CURRENT_PHASE.md       always-correct pointer: next build purpose + phase ladder
├── RAG_PLAN.md            the 7-phase retrieval-quality plan (the "why" and the gates)
├── 03_ARCHITECTURE.md     agent topology, state, tools, verifier (what the phases modify)
├── rag/                   per-phase specs 00–07 (each = spec + build prompt), RISKS, 2-day plan
└── archive/               reference — product thesis + tech stack (git retains everything)
```
