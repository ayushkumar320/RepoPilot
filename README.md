# RepoPilot

Paste a public Python GitHub repo URL → get a **purpose-driven, grounded onboarding tour** powered by a multi-agent LLM pipeline whose every claim cites the exact `file:line` it came from.

> **Spec-first project.** The design lives in [`docs/`](docs/) and is queryable via [Graphify](graphify-out/). Code is being built phase-by-phase against the gates in [`docs/04_BUILD_PLAN.md`](docs/04_BUILD_PLAN.md). The pointer to the active phase is [`docs/CURRENT_PHASE.md`](docs/CURRENT_PHASE.md).

## Quickstart (local dev)

Prerequisites: `uv` (≥ 0.4), Docker, Make, Git.

```bash
# 1. Install workspace
uv sync

# 2. Bring up Postgres + pgvector, Redis, Ollama (model preload happens automatically)
docker compose up -d

# 3. Run the full CI suite locally
make ci
```

Phase-by-phase build instructions live in [`docs/05_PHASE_PROMPTS.md`](docs/05_PHASE_PROMPTS.md). Start every build session by reading [`CLAUDE.md`](CLAUDE.md) and [`docs/CURRENT_PHASE.md`](docs/CURRENT_PHASE.md).

## Repo layout

```
apps/
  api/        FastAPI app (endpoints come online in Phase 4)
  web/        Next.js 15 app (Phase 4)
packages/
  core/       shared settings, logging, LLMProvider (the only place agents talk to LLMs)
  ingestion/  tree-sitter + NetworkX + pgvector indexing pipeline (Phase 1)
  agents/     LangGraph nodes + capability library (Phase 2+)
  evals/      datasets + runners gating each phase
docs/         single source of truth for the design — read these before coding
graphify-out/ knowledge graph over code + docs (`graphify query "..."`)
```

## Status

See [`docs/CURRENT_PHASE.md`](docs/CURRENT_PHASE.md) for the live phase pointer.
