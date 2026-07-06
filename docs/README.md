# RepoPilot — Docs

The product slice (clone → index → retrieve → answer → verify) ships on `main`. Current focus: **measured retrieval quality**, driven by [`RAG_PLAN.md`](RAG_PLAN.md).

> Prefer the [Graphify knowledge graph](../graphify-out/) over reading raw — `graphify query "<question>"`. Project rules live in [`../CLAUDE.md`](../CLAUDE.md); this is the human-readable map.

## Read in order (cold pickup)

1. [`CURRENT_PHASE.md`](CURRENT_PHASE.md) — active phase, what's blocking it.
2. [`RAG_PLAN.md`](RAG_PLAN.md) — the 7-phase plan, measurement spine, Definition of Done.
3. [`rag/README.md`](rag/README.md) — the phase-ladder index (iron rules + timeboxes + priority).
4. The active phase's spec in [`rag/`](rag/).

## Layout

```
docs/
├── README.md              this file
├── CURRENT_PHASE.md       always-correct pointer at the active phase
├── RAG_PLAN.md            the 7-phase retrieval-quality plan
├── 03_ARCHITECTURE.md     agent topology, state, tools, verifier
├── rag/                   per-phase specs (00–07 + RISKS + README)
└── archive/               reference — product thesis + tech stack (git retains everything)
```
