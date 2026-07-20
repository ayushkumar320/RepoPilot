# Production deployment

RepoPilot deploys as a web service, an API service, a background worker, Postgres with pgvector, and Redis. Keep the API and worker in the same region as Postgres.

## Service topology

| Service | Build | Start command |
|---|---|---|
| Web | `apps/web/Dockerfile` with `apps/web` as build context | image default |
| API | `Dockerfile.api` with repository root as build context | image default |
| Worker | `Dockerfile.api` with repository root as build context | `arq repopilot_api.jobs.index_repo.WorkerSettings` |
| Migration job | `Dockerfile.api` | `cd packages/ingestion && alembic upgrade head` |

In production, platform-key indexing runs on the ARQ worker. BYOK indexing stays inside the API process because raw user keys are session-only and must never be copied into Redis. Keep one API replica while BYOK indexing is active; moving those jobs across replicas requires an encrypted credential-reference service.

## Required production environment

```bash
REPOPILOT_ENV=production
REPOPILOT_WEB_ORIGINS=https://your-domain.example
REPOPILOT_SESSION_SECRET=<openssl-rand-hex-32>
REPOPILOT_SESSION_COOKIE_SECURE=true
POSTGRES_DSN=<managed-postgres-with-pgvector>
REDIS_URL=<managed-redis-tls-url>
GROQ_API_KEY=<platform-free-tier-key>
API_PROXY_TARGET=https://api.your-domain.example
NEXT_PUBLIC_API_BASE_URL=/api
```

`REPOPILOT_SESSION_SECRET` must be stable across API deployments. Changing it signs every browser out. User provider keys are deliberately session-only and users must reconnect them after an API restart.

## Release sequence

1. GitHub Actions runs Python lint, formatting, strict MyPy, tests, secret scanning, frontend typechecking, and the production Next.js build.
2. Build the API and web images from the Dockerfiles.
3. Run the migration job once against the target Postgres database.
4. Deploy the API and worker.
5. Verify `GET /health`, Postgres connectivity, and Redis connectivity.
6. Deploy the web image with `API_PROXY_TARGET` pointing at the API.
7. Smoke test one repository, five free questions, the key gate, and SSE streaming.

Do not expose the API and web on unrelated sites while using cookie sessions. Prefer `app.example.com` and `api.example.com`, or proxy `/api` through the Next.js service as configured here.
