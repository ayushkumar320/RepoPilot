# Docker Hub Overview

Text for the Docker Hub repository descriptions. Paste the matching section into
the "Overview" tab of each repository. Keep it in sync with the Dockerfiles.

---

## ayushkumar320/repopilot-api

**RepoPilot backend — the FastAPI service that indexes a public GitHub repo and
answers questions about it with `file:line` citations.**

Paste a public GitHub URL, say why you are here, and RepoPilot returns a guided
tour of the codebase where every factual claim is tied to real source lines. The
call graph is built by an AST, retrieval is hybrid vector + keyword + graph, and
a verifier re-reads the cited source before an answer is returned. Unsupported
claims are flagged, never silently dropped.

This image runs the API only. It needs Postgres with the `pgvector` extension,
Redis, and at least one chat provider key.

### Run

```bash
docker run -p 8000:8000 \
  -e POSTGRES_DSN='postgresql+psycopg://user:pass@host:5432/repopilot' \
  -e REDIS_URL='redis://host:6379/0' \
  -e REPOPILOT_SESSION_SECRET="$(openssl rand -hex 32)" \
  -e GROQ_API_KEY=... \
  ayushkumar320/repopilot-api:latest
```

Health check: `GET /health`. Interactive API docs: `/docs`.

### Environment

| Variable | Required | Purpose |
|---|---|---|
| `POSTGRES_DSN` | yes | Postgres with `pgvector`. Keep the `+psycopg` driver tag. Defaults to localhost, which is wrong inside a container. |
| `REDIS_URL` | yes | Job queue backend. Defaults to localhost. |
| `REPOPILOT_SESSION_SECRET` | yes | Signs session cookies. 32 random bytes. There is a development default — do not ship it. |
| `GROQ_API_KEY` | one of | Primary chat provider. |
| `CEREBRAS_API_KEY` | one of | Fallback chat provider. |
| `HUGGINGFACE_API_KEY` | one of | Last-resort chat provider. |
| `REPOPILOT_WEB_ORIGINS` | no | Comma-separated CORS origins for the frontend. |
| `REPOPILOT_SESSION_COOKIE_SECURE` | no | Set `true` behind HTTPS. |
| `REPOPILOT_ENV` | no | Environment label. |
| `REPOPILOT_LOG_LEVEL` | no | Defaults to `INFO`. |
| `PORT` | no | Listen port. Defaults to `8000`. |

Embeddings run in-process via sentence-transformers, so the first indexing job
after a cold start downloads ~250MB of model weights into the `huggingface_hub`
cache. Mount a volume at `/root/.cache/huggingface` (or set `HF_HOME`) if you
want that to survive restarts.

### Tags

- `latest` — current build from `main`, `linux/amd64`.

Source and full docs: https://github.com/ayushkumar320/RepoPilot

---

## ayushkumar320/repopilot-web

**RepoPilot frontend — the Next.js app you actually look at.**

Serves the tour UI: intent capture, streamed answers over SSE, per-claim
verification badges, expandable citations that open to the exact cited source,
and a related-code panel walked from the AST graph. Sign-in with Google or
GitHub keeps saved tours across devices.

This image is the UI only. It needs a running `repopilot-api`.

### Run

```bash
docker run -p 3000:3000 \
  -e API_PROXY_TARGET='http://api:8000' \
  -e REPOPILOT_SESSION_SECRET="$(openssl rand -hex 32)" \
  ayushkumar320/repopilot-web:latest
```

Then open http://127.0.0.1:3000.

### Environment

| Variable | Required | Purpose |
|---|---|---|
| `API_PROXY_TARGET` | yes | Where the app proxies API calls. Baked at build time as a default; override at run time. |
| `REPOPILOT_SESSION_SECRET` | yes | Must match the value the API uses. |
| `NEXT_PUBLIC_API_BASE_URL` | no | Browser-visible API base, when the API is not proxied. |
| `AUTH_SECRET` | no | Required only if sign-in is enabled. |
| `AUTH_GITHUB_ID` / `AUTH_GITHUB_SECRET` | no | GitHub sign-in. Callback: `<web-url>/api/auth/callback/github`. |
| `AUTH_GOOGLE_ID` / `AUTH_GOOGLE_SECRET` | no | Google sign-in. Callback: `<web-url>/api/auth/callback/google`. |
| `REPOPILOT_SESSION_COOKIE_SECURE` | no | Set `true` behind HTTPS. |
| `PORT` | no | Listen port. Defaults to `3000`. |

### Tags

- `latest` — current build from `main`, `linux/amd64`.

Source and full docs: https://github.com/ayushkumar320/RepoPilot
