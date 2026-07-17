# RepoPilot Startup Guide

This guide is the local operator runbook for RepoPilot. It covers a fresh clone, local services, the API, the web app, and the checks to run before handing the project to someone else.

## Prerequisites

- Python 3.12
- `uv`
- Node.js 20+
- npm
- Docker Desktop or Docker Engine
- Git
- Optional: `graphify` for repo-knowledge graph updates

## 1. Install Dependencies

From the repository root:

```bash
uv sync --all-packages --all-groups
cd apps/web
npm install
cd ../..
```

## 2. Configure Environment

Create a local `.env` from the checked-in template:

```bash
cp .env.example .env
```

For a real tour, add at least one chat provider key to `.env`:

```bash
GROQ_API_KEY=...
CEREBRAS_API_KEY=...
HUGGINGFACE_API_KEY=...
```

Notes:

- Unit tests can run without provider keys.
- Real repo indexing and tour generation need provider capacity.
- Embeddings use `nomic-ai/nomic-embed-text-v1.5` through sentence-transformers and download on first use.
- `GITHUB_PAT` is optional unless you are exercising GitHub issue-context flows.
- Leave the default local datastore settings unless you are pointing at external services:

```bash
POSTGRES_DSN=postgresql+psycopg://repopilot:repopilot@localhost:5432/repopilot
REDIS_URL=redis://localhost:6379/0
REPOPILOT_WEB_ORIGINS=http://127.0.0.1:3000,http://localhost:3000
```

## 3. Start Local Services

```bash
make docker-up
make db-migrate
```

This starts:

- Postgres 16 + pgvector on `localhost:5432`
- Redis on `localhost:6379`

To stop and clear local service volumes:

```bash
make docker-down
```

## 4. Run The API

Terminal 1:

```bash
uv run uvicorn repopilot_api.app:app --app-dir apps/api/src --reload --host 127.0.0.1 --port 8000
```

Open the API docs at:

```text
http://127.0.0.1:8000/docs
```

The local API indexes submitted repositories in-process through the runtime service layer. No separate worker process is required for the normal dev flow.

## 5. Run The Web App

Terminal 2:

```bash
cd apps/web
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

## 6. Use The App Locally

1. Paste a public Python GitHub repo URL.
2. Wait for indexing to finish.
3. Enter what you are trying to learn or change in the repo.
4. Generate a tour or ask grounded follow-up questions.

Good smoke-test repos are small-to-medium Python projects. Very large repos will depend more heavily on model-provider quota and first-run embedding downloads.

## 7. Run Checks

Before committing or handing off:

```bash
UV_CACHE_DIR=.uv-cache uv run ruff format --check .
UV_CACHE_DIR=.uv-cache uv run ruff check .
UV_CACHE_DIR=.uv-cache uv run pytest -m "not slow and not integration"
```

Common Make targets:

```bash
make install
make lint
make typecheck
make test
make ci
```

Web checks:

```bash
cd apps/web
npm run typecheck
npm run test:store
```

Browser and Lighthouse checks need the web app running:

```bash
cd apps/web
npm run test:e2e
npm run test:lighthouse
```

## 8. Eval And Graph Maintenance

For retrieval eval runs, use the phase bench runner documented in `docs/EVAL_SYSTEM.md` and `docs/rag/README.md`.

After major code, architecture, or multi-file documentation changes, update the committed Graphify graph:

```bash
graphify update .
git add graphify-out/graph.json graphify-out/manifest.json
```

The CI retrieval gate requires a fresh `evals/results/rag_phaseN/_after.json` whenever a pull request touches retrieval paths.

## Troubleshooting

If `uv` tries to use a home cache that the sandbox cannot read, use the workspace cache:

```bash
UV_CACHE_DIR=.uv-cache uv run ...
```

If Postgres or Redis state looks stale:

```bash
make docker-down
make docker-up
make db-migrate
```

If first indexing is slow, check whether sentence-transformers is downloading embedding weights and whether the configured LLM provider is rate-limiting.
