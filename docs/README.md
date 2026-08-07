# RepoPilot — Docs

The product slice (clone → index → retrieve → answer → verify) ships on `main`. Start with [`STARTUP_GUIDE.md`](STARTUP_GUIDE.md) when you want to run the project locally.

> Project rules live in [`../CLAUDE.md`](../CLAUDE.md); this is the human-readable map.

## The one-paragraph story

RepoPilot is now organized as a runnable beta with a small public doc set. The live docs explain how to run, understand, and validate the app. Historical product and stack rationale lives under `archive/`; temporary build/phase docs have been removed.

## Read in order (cold pickup)

1. [`STATUS.md`](STATUS.md) — where the project stands right now: what shipped, what is next, what is known-broken. Read this first when picking work up.
2. [`STARTUP_GUIDE.md`](STARTUP_GUIDE.md) — install, environment, services, API, web, checks.
3. [`../README.md`](../README.md) — product overview, architecture diagrams, source map.
4. [`03_ARCHITECTURE.md`](03_ARCHITECTURE.md) — agent topology, state schema, tools, verifier.
5. [`archive/`](archive/) — product thesis and historical stack rationale.

## Layout

```
docs/
├── README.md              this file — the map
├── STATUS.md              current state: shipped, next, known-broken
├── STARTUP_GUIDE.md       local startup and operator commands
├── 03_ARCHITECTURE.md     agent topology, state, tools, verifier
├── DEPLOYMENT.md          production containers, migration, release sequence
├── STATEFUL.md            accounts, saved tours, BYOK provider keys
└── archive/               reference — product thesis + tech stack (git retains everything)
```
