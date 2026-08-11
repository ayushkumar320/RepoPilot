# Production deployment

RepoPilot deploys as a web service, an API service, a background worker, Postgres with pgvector, and Redis. Keep the API and worker in the same region as Postgres.

## Service topology

| Service | Build | Start command |
|---|---|---|
| Web | `apps/web/Dockerfile` with `apps/web` as build context | image default |
| API | `Dockerfile.api` with repository root as build context | image default |
| Worker | `Dockerfile.api` with repository root as build context | `arq repopilot_api.jobs.index_repo.WorkerSettings` |
| Migration job | `Dockerfile.api` | `cd packages/ingestion && alembic upgrade head` |

In production, platform-key indexing runs on the ARQ worker. BYOK indexing stays inside the API process because raw user keys are held in process memory and must never be copied into Redis. Keep one API replica while BYOK indexing is active; moving those jobs across replicas requires an encrypted credential-reference service.

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

`REPOPILOT_SESSION_SECRET` must be stable across API deployments. Changing it signs every browser out. It also keys the Fernet cipher for stored provider keys (`product_credentials`): rotating it invalidates every saved key, and users must reconnect them.

### Sign-in (web service)

Set these on the **web** service only, alongside the same
`REPOPILOT_SESSION_SECRET` the API uses:

```bash
AUTH_SECRET=<openssl-rand-hex-32>
AUTH_GOOGLE_ID=<oauth client id>
AUTH_GOOGLE_SECRET=<oauth client secret>
AUTH_GITHUB_ID=<oauth app client id>
AUTH_GITHUB_SECRET=<oauth app client secret>
NEXTAUTH_URL=https://your-domain.example
REPOPILOT_SESSION_SECRET=<same value as the API>
REPOPILOT_SESSION_COOKIE_SECURE=true
```

OAuth callback URLs: `https://your-domain.example/api/auth/callback/google`
and `.../callback/github`. Configure whichever providers you set ids for —
each one is wired only when its id is present.

The web app signs a stable, account-derived session id with
`REPOPILOT_SESSION_SECRET` and writes it to the same `repopilot_session`
cookie the API already verifies — there is no second token format and no
bearer plumbing. The two values must match byte for byte; a mismatch degrades
silently to anonymous sessions rather than erroring. With **both** provider
ids unset there is no gate and the product runs anonymously, exactly as
before; with either set, the landing page is a sign-in screen and the
repository step comes after sign-in.

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
7. Smoke test sign-in, one repository, a few questions, the key gate, and SSE streaming.

Do not expose the API and web on unrelated sites while using cookie sessions. Prefer `app.example.com` and `api.example.com`, or proxy `/api` through the Next.js service as configured here.

---

# Free-tier deployment plan

The topology above assumes paid managed services. This section is the concrete
plan for a zero-cost first deployment, and the constraints that shape it.

## What forces the shape

- Embeddings run **in-process** via `sentence-transformers`, which pulls in
  torch. The API image is roughly 2–3 GB and the process needs about 2 GB of
  RAM resident. That eliminates every free tier capped at 512 MB (Render free,
  Fly's smallest shared instance, Railway's trial after credits run out).
- Redis carries **only the ARQ job queue**. Nothing in it is durable; a restart
  loses in-flight index jobs, which can be re-run.
- Postgres needs `pgvector`.
- Web and API must be same-site for the `repopilot_session` cookie, and the
  web app signs that cookie itself with the shared `REPOPILOT_SESSION_SECRET`
  (see `apps/web/src/lib/identity.ts`).

## Target topology

| Piece | Where | Free tier |
|---|---|---|
| Web (Next.js) | Vercel | Hobby |
| API + ARQ worker + Redis | One Hugging Face Space (Docker SDK) | 2 vCPU / 16 GB RAM |
| Postgres + pgvector | Neon | free project |

Hugging Face Spaces is the recommendation because it is the only free tier
with enough RAM for torch. Redis runs as a third process **inside** the Space
container rather than as a managed service: Upstash's free tier is metered per
command, and ARQ polls its queue continuously, so a single idle worker burns
roughly 5 M commands a month against a 500 K cap. A local `redis-server` costs
nothing and loses nothing that matters.

The Space runs API and worker in one container. Note the BYOK constraint above
still holds — one API replica — and a single container satisfies it by
construction.

## Blocking prerequisites

`docs/STATUS.md` records that the accepted spend risks assume a private
deployment, and that the decision "expires the moment the API is reachable by
anyone who is not paying for it" — including an unlisted URL. A Space is
public. Close these two first:

- **Finding 3** — `reserve_question` passes `free_limit=None`, so questions are
  unmetered. Pass a limit from settings; the counting code already exists.
- **Finding 4** — `POST /intent` is an unauthenticated model call with no rate
  limit. Add a per-session sliding window as a FastAPI dependency.

**Finding 5** is worth closing at the same time here, for a reason unrelated to
abuse: the Space has ephemeral disk and a repository is cloned in full before
`ingestion_max_repo_loc` (200 000) applies. `clone_to_tempdir` already clones
shallow and single-branch; adding `--filter=blob:none`, or a GitHub API size
check before cloning, keeps one pasted monorepo from filling the container.

## Step 1 — Postgres on Neon

1. Create a Neon project in the region nearest the Space (`us-east` is a safe
   default).
2. `CREATE EXTENSION IF NOT EXISTS vector;` on the target database.
3. Take the pooled connection string. `make_engine` rewrites `postgresql://`
   to `postgresql+psycopg://`, so paste it unchanged and keep `sslmode=require`.
4. Run migrations from a laptop, once:

   ```bash
   POSTGRES_DSN='<neon-uri>' make db-migrate
   ```

## Step 2 — the Space image

The Space needs its own Dockerfile because it runs three processes and listens
on port 7860. Base it on `Dockerfile.api` and change only the tail:

```dockerfile
# Dockerfile.space — build context is the repository root
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY . .
RUN uv sync --frozen --no-dev --all-packages

FROM python:3.12-slim-bookworm AS runtime
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git libgomp1 redis-server \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app
COPY --from=build /app /app

# Bake the embedding weights into the image. Without this, every cold start
# downloads ~250 MB before the first request can be served.
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('nomic-ai/nomic-embed-text-v1.5', trust_remote_code=True)"

EXPOSE 7860
CMD ["sh", "-c", "redis-server --daemonize yes --save '' --appendonly no && \
     arq repopilot_api.jobs.index_repo.WorkerSettings & \
     exec uvicorn repopilot_api.app:app --app-dir apps/api/src \
       --host 0.0.0.0 --port ${PORT} --timeout-keep-alive 75"]
```

Two details that matter: `--save '' --appendonly no` keeps Redis in memory only
(the queue is disposable, and persistence would only add disk churn), and the
worker needs `--app-dir` semantics too — it resolves `repopilot_api` from the
installed workspace, so no extra path wiring is required.

The torch CPU index pin in the root `pyproject.toml` already keeps the Linux
build off the CUDA wheels, so the image stays near 2 GB rather than 6 GB.

## Step 3 — create the Space

1. New Space → SDK **Docker** → visibility **Public** (private Spaces do not
   get the free CPU tier).
2. The Space's `README.md` front matter must declare the port:

   ```yaml
   ---
   title: RepoPilot API
   sdk: docker
   app_port: 7860
   ---
   ```

3. Push the repository to the Space remote with `Dockerfile.space` renamed to
   `Dockerfile`, or keep a thin deploy branch. Expect a 10–20 minute first
   build.
4. Set these as **Secrets** (not Variables) in Space settings:

   ```bash
   REPOPILOT_ENV=production
   REPOPILOT_SESSION_SECRET=<openssl rand -hex 32>
   REPOPILOT_SESSION_COOKIE_SECURE=true
   REPOPILOT_WEB_ORIGINS=https://<project>.vercel.app
   POSTGRES_DSN=<neon uri>
   GROQ_API_KEY=<key>
   HUGGINGFACE_API_KEY=<key>
   ```

   Leave `REDIS_URL` unset — the default `redis://localhost:6379/0` is correct
   inside the container. `REPOPILOT_ENV=production` makes the settings
   validator reject a default session secret and a non-secure cookie, so both
   values above are mandatory, not advisory.

## Step 4 — the web app on Vercel

1. Import the repository, root directory `apps/web`.
2. Environment:

   ```bash
   API_PROXY_TARGET=https://<user>-<space>.hf.space
   NEXT_PUBLIC_API_BASE_URL=/api
   REPOPILOT_SESSION_SECRET=<byte-for-byte the same value as the Space>
   REPOPILOT_SESSION_COOKIE_SECURE=true
   ```

3. Sign-in is optional. With both `AUTH_GOOGLE_ID` and `AUTH_GITHUB_ID` unset
   the product runs anonymously. If you set either, also set `AUTH_SECRET` and
   `NEXTAUTH_URL`, and register the callback URLs listed earlier in this file.

Keeping `NEXT_PUBLIC_API_BASE_URL=/api` routes the browser through the Next.js
rewrite, so everything is same-origin and the cookie needs no cross-site
exception. The alternative — pointing the browser straight at the Space — works
too, but then `REPOPILOT_WEB_ORIGINS` and the `SameSite=None` cookie path both
become load-bearing.

## Step 5 — verify

1. `GET https://<space>.hf.space/health` returns 200.
2. Space logs show `arq.startup` and no Redis connection error.
3. Load the Vercel URL, paste a small repository (`pallets/click` is a good
   size), and watch indexing complete — that exercises clone, parse, embed,
   Postgres write, and the ARQ round trip in one go.
4. Confirm the tour SSE stream renders progressively rather than arriving in
   one block. This is the most likely thing to break: Vercel proxies the
   rewrite through its edge, and a buffered or time-capped proxy shows up here
   first. If it does break, switch `NEXT_PUBLIC_API_BASE_URL` to the Space URL
   so the browser connects directly, and add that origin to
   `REPOPILOT_WEB_ORIGINS`.
5. Confirm the free-repository gate and the "connect your Groq key" 402 path.

## Known ceilings

- A free Space sleeps after about 48 hours idle, and waking it pulls a ~2 GB
  image, so the first request after a long quiet period is slow.
- Space storage is ephemeral. Clones and the LLM SQLite cache
  (`LLM_CACHE_PATH`) do not survive a restart; the index in Postgres does.
- One container means one API replica and one worker. Concurrent indexing of
  two large repositories will contend for CPU with request serving.
- Neon's free tier suspends an idle database, adding a cold-start delay to the
  first query.
- Rotating `REPOPILOT_SESSION_SECRET` signs everyone out **and** invalidates
  every stored provider key in `product_credentials`. Set it once.
