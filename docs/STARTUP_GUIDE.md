# RepoPilot Startup Guide

This is the simple local runbook. In normal development you only need four commands.

## The Short Version

From the repo root:

```bash
make setup
cp .env.example .env
make services
make dev
```

Then open:

```text
http://127.0.0.1:3000
```

That is it. `make dev` runs both:

- Backend API: `http://127.0.0.1:8000`
- Frontend app: `http://127.0.0.1:3000`

For real tours, put at least one LLM provider key in `.env` before using the app.

## Prerequisites

- Python 3.12
- `uv`
- Node.js 20+
- npm
- Docker Desktop or Docker Engine
- Git

## Commands You Actually Use

| Command | What it does |
|---|---|
| `make setup` | Installs Python workspace deps and frontend npm deps. |
| `make services` | Starts Postgres/Redis and runs DB migrations. |
| `make backend` | Runs only the FastAPI backend. |
| `make frontend` | Runs only the Next.js frontend. |
| `make dev` | Runs backend and frontend together. |
| `make test` | Runs the fast Python test lane. |
| `make lint` | Runs Ruff lint and format checks. |

## 1. Install Dependencies

From the repository root:

```bash
make setup
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
make services
```

This starts:

- Postgres 16 + pgvector on `localhost:5432`
- Redis on `localhost:6379`

To stop and clear local service volumes:

```bash
make docker-down
```

## 4. Run The App

The easiest path is one command:

```bash
make dev
```

Open the app:

```text
http://127.0.0.1:3000
```

If you prefer separate terminals:

Terminal 1:

```bash
make backend
```

Terminal 2:

```bash
make frontend
```

API docs are available at:

```text
http://127.0.0.1:8000/docs
```

The local API indexes submitted repositories in-process through the runtime service layer. No separate worker process is required for the normal dev flow.

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
make setup
make services
make backend
make frontend
make dev
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

### "Internal Server Error" on submit (`POST /api/repos` returns 500)

**Dev only.** The web app talks to the backend through the same-origin Next.js proxy (`/api/*` → uvicorn, see `apps/web/next.config.mjs`). The Next dev server keeps a pool of keep-alive sockets to uvicorn. If uvicorn closes an idle socket (its default `--timeout-keep-alive` is 5s) while that socket still sits in the proxy's pool, the next request reuses the dead socket and the hop fails with `ECONNRESET` / `socket hang up`. The proxy turns that into a **500** and the UI shows "Internal Server Error"; the backend logs no error because the failure is on the proxy→uvicorn hop, not in FastAPI. It is intermittent (timing-dependent) and a plain page reload usually clears it.

This is fixed by running uvicorn with a keep-alive window wider than the proxy's socket reuse gap — `make backend` / `make dev` now pass `--timeout-keep-alive 75`. The web API client (`apps/web/src/lib/api/generated.ts`) also retries idempotent requests once on a transient 5xx. If you run uvicorn by hand, add the flag:

```bash
uv run uvicorn repopilot_api.app:app --app-dir apps/api/src --host 127.0.0.1 --port 8000 --timeout-keep-alive 75
```

This does not occur in production, which sits behind a real reverse proxy rather than the Next dev server.
