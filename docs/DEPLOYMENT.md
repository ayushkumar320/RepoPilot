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

### Optional: GitHub sign-in (web service)

Set these on the **web** service only, alongside the same
`REPOPILOT_SESSION_SECRET` the API uses:

```bash
AUTH_SECRET=<openssl-rand-hex-32>
AUTH_GITHUB_ID=<oauth app client id>
AUTH_GITHUB_SECRET=<oauth app client secret>
NEXTAUTH_URL=https://your-domain.example
REPOPILOT_SESSION_SECRET=<same value as the API>
REPOPILOT_SESSION_COOKIE_SECURE=true
```

OAuth callback URL: `https://your-domain.example/api/auth/callback/github`.

The web app signs a stable, GitHub-derived session id with
`REPOPILOT_SESSION_SECRET` and writes it to the same `repopilot_session`
cookie the API already verifies — there is no second token format and no
bearer plumbing. The two values must match byte for byte; a mismatch degrades
silently to anonymous sessions rather than erroring. Leaving `AUTH_GITHUB_ID`
unset disables sign-in and the product behaves exactly as it did before.

### Managed Postgres (Aiven)

Any Postgres with `pgvector` works. For Aiven:

1. Create a Postgres service (a Hobbyist/Startup plan is enough).
2. Enable the extension: `CREATE EXTENSION IF NOT EXISTS vector;`
3. Copy the *service URI* into `POSTGRES_DSN` unchanged, keeping
   `sslmode=require`. `make_engine` rewrites `postgresql://` to
   `postgresql+psycopg://`, so no edit is needed.
4. Run the migration job (`alembic upgrade head`) against it.

## Release sequence

1. GitHub Actions runs Python lint, formatting, strict MyPy, tests, secret scanning, frontend typechecking, and the production Next.js build.
2. Build the API and web images from the Dockerfiles.
3. Run the migration job once against the target Postgres database.
4. Deploy the API and worker.
5. Verify `GET /health`, Postgres connectivity, and Redis connectivity.
6. Deploy the web image with `API_PROXY_TARGET` pointing at the API.
7. Smoke test one repository, five free questions, the key gate, and SSE streaming.

Do not expose the API and web on unrelated sites while using cookie sessions. Prefer `app.example.com` and `api.example.com`, or proxy `/api` through the Next.js service as configured here.
