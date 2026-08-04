# RepoPilot — Docs

The product slice (clone → index → retrieve → answer → verify) ships on `main`. Start with [`STARTUP_GUIDE.md`](STARTUP_GUIDE.md) when you want to run the project locally.

> Project rules live in [`../CLAUDE.md`](../CLAUDE.md); this is the human-readable map.

## The one-paragraph story

RepoPilot is now organized as a runnable beta with a small public doc set. The live docs explain how to run, understand, and validate the app. Historical product and stack rationale lives under `archive/`; temporary build/phase docs have been removed.

## Read in order (cold pickup)

1. [`STARTUP_GUIDE.md`](STARTUP_GUIDE.md) — install, environment, services, API, web, checks.
2. [`../README.md`](../README.md) — product overview, architecture diagrams, source map.
3. [`03_ARCHITECTURE.md`](03_ARCHITECTURE.md) — agent topology, state schema, tools, verifier.
4. [`INGESTION_PARALLELIZATION_CODEX_PROMPT.md`](INGESTION_PARALLELIZATION_CODEX_PROMPT.md) — execution prompt for bounded parallel scanning and batched embedding.
5. [`archive/`](archive/) — product thesis and historical stack rationale.

## Layout

```
docs/
├── README.md              this file — the map
├── STARTUP_GUIDE.md       local startup and operator commands
├── 03_ARCHITECTURE.md     agent topology, state, tools, verifier
├── INGESTION_PARALLELIZATION_CODEX_PROMPT.md
│                          implementation prompt for faster large-repo indexing
└── archive/               reference — product thesis + tech stack (git retains everything)
```
