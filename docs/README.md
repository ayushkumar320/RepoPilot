# RepoPilot — Docs

The product slice (clone → index → retrieve → answer → verify) ships on `main`, and the RAG closeout is complete. Start with [`STARTUP_GUIDE.md`](STARTUP_GUIDE.md) when you want to run the project locally.

> Prefer the [Graphify knowledge graph](../graphify-out/) over reading raw — `graphify query "<question>"`. Project rules live in [`../CLAUDE.md`](../CLAUDE.md); this is the human-readable map.

## The one-paragraph story

RepoPilot is now organized as a runnable beta plus archived build history. The live docs explain how to run, understand, and validate the app. The RAG phase ladder remains in the repo as historical evidence for the retrieval-quality work: Phases 1, 3, 4, 5, and 7 shipped; Phases 2 and 6 were evaluated and cleanly deferred.

## Read in order (cold pickup)

1. [`STARTUP_GUIDE.md`](STARTUP_GUIDE.md) — install, environment, services, API, web, checks.
2. [`../README.md`](../README.md) — product overview, architecture diagrams, source map.
3. [`03_ARCHITECTURE.md`](03_ARCHITECTURE.md) — agent topology, state schema, tools, verifier.
4. [`EVAL_SYSTEM.md`](EVAL_SYSTEM.md) — eval harness and retrieval regression gate.
5. [`CURRENT_PHASE.md`](CURRENT_PHASE.md) — shipped closeout status and deferred eval notes.

## Layout

```
docs/
├── README.md              this file — the map
├── STARTUP_GUIDE.md       local startup and operator commands
├── CURRENT_PHASE.md       shipped closeout status + deferred phase notes
├── RAG_PLAN.md            archived retrieval-quality plan
├── 03_ARCHITECTURE.md     agent topology, state, tools, verifier (what the phases modify)
├── EVAL_SYSTEM.md         eval harness and artifact protocol
├── rag/                   archived per-phase RAG specs, risks, and ship closeout
└── archive/               reference — product thesis + tech stack (git retains everything)
```
