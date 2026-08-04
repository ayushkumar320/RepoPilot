# Stateful RepoPilot — Login + Per-User Memory (Implementation Plan)

> Status: plan. Scope: add NextAuth OAuth login and per-user persistence so a
> returning user sees their past tours, questions, answers, and connected
> provider. Storage: managed Postgres (Aiven). **Evals are explicitly out of
> scope for this work — do not run or modify `packages/evals` or the eval
> workflows.**

---

## 0. The one idea this plan rests on

The backend is **already stateful per `session_id`**. Read
[`apps/api/src/repopilot_api/access.py`](../apps/api/src/repopilot_api/access.py)
and [`apps/api/src/repopilot_api/product_db.py`](../apps/api/src/repopilot_api/product_db.py):

- `product_accounts` and `usage_events` are Postgres tables keyed on `session_id`.
- `session_id` arrives as an **HMAC-signed cookie** (`repopilot_session`), minted
  in [`app.py`](../apps/api/src/repopilot_api/app.py) (`resolve_session`, signed
  with `repopilot_session_secret`).
- Today an anonymous visitor just gets a **random UUID** in that cookie.

So "stateful with login" is not a rewrite. It is:

1. **Make `session_id` stable and user-owned** instead of random — derive it
   deterministically from the OAuth identity and put it in the *same* signed
   cookie. Every existing per-session feature (free allowances, connected Groq
   key, and the tours we add below) becomes per-user **with zero API auth
   changes**.
2. **Persist tour content** (questions, answers, claims, intent profile) — you
   already had a `product_tours` table; migration
   [`0005_drop_product_tours.py`](../packages/ingestion/src/repopilot_ingestion/migrations/versions/0005_drop_product_tours.py)
   removed it. Reintroduce it plus a messages table.
3. **Point `POSTGRES_DSN` at Aiven.** That is the entire "Aiven" task — it is
   plain managed Postgres; no code cares which host serves it.

Everything below is the minimum to do those three things.

---

## 1. Architecture decisions (and what we deliberately skip)

| Decision | Choice | Why / what we skip |
|---|---|---|
| Auth library | **NextAuth / Auth.js v5** on the Next 15 app router | Native to the existing web app; no new backend. |
| OAuth provider | **GitHub** (single provider) | The product's input *is* a GitHub URL; the user already has a GitHub account. Skip Google/email — add later if asked. |
| Session strategy | **JWT** (no NextAuth DB adapter) | We do not need NextAuth's own user/account tables. Skip the adapter and its 4 tables entirely. Identity lives in the JWT; our own `product_accounts` row is the user record. |
| Web ↔ API trust | **Reuse the existing signed `repopilot_session` cookie** | The API already verifies this cookie. Web sets it after login with a user-derived `session_id`. No new token format, no JWKS, no bearer plumbing. |
| `session_id` for a user | `uuidv5(NAMESPACE, "github:" + providerAccountId)` | Deterministic and stable across logins/devices. Anonymous users keep their random UUID — fully backward compatible. |
| Tour storage | **Postgres**, reintroduce `product_tours` + add `product_tour_messages` | We already dropped/re-add a known schema. |
| Aiven | Set `POSTGRES_DSN` to the Aiven connection string | No code change; `make_engine` already rewrites the DSN scheme. |
| Migrations | **Alembic** (existing setup in `packages/ingestion`) | Reuse migration `0006`. |
| **Evals** | **Skipped entirely** | Do not touch `packages/evals`, do not run eval datasets or the slow lane. |

Ponytail notes on what we are NOT building: no separate auth microservice, no
NextAuth DB adapter, no second secret/JWKS exchange between web and API, no new
ORM models package, no soft-delete/versioning on tours, no realtime sync. Add
any of those only when a concrete need appears.

---

## 2. Data model

Reintroduce the dropped table and add a messages child table. New migration
`0006_product_tours_persist` in
`packages/ingestion/src/repopilot_ingestion/migrations/versions/`.

```
product_accounts                     -- EXISTS; add nullable identity columns
  session_id      uuid  PK
  created_at      timestamptz
  last_seen_at    timestamptz
  provider        text        NULL   -- NEW: "github"
  provider_account_id text    NULL   -- NEW
  display_name    text        NULL   -- NEW: for the UI header
  email           text        NULL   -- NEW
  avatar_url      text        NULL   -- NEW

product_tours                        -- REINTRODUCE (was dropped in 0005)
  tour_id         text  PK           -- app-generated, e.g. slug+short-uuid
  session_id      uuid  FK -> product_accounts.session_id  ON DELETE CASCADE
  repo_id         text  NOT NULL     -- the public repo URL/id the user pasted
  snapshot_repo_id text FK -> repos.id ON DELETE CASCADE
  intent_profile  jsonb NOT NULL     -- the IntentProfile captured up front
  title           text  NULL         -- derived label for the history list
  created_at      timestamptz
  updated_at      timestamptz
  INDEX (session_id, updated_at DESC)

product_tour_messages                -- NEW
  id              uuid  PK
  tour_id         text  FK -> product_tours.tour_id ON DELETE CASCADE
  ordinal         int   NOT NULL     -- 0-based, question order within the tour
  question        text  NOT NULL
  answer          text  NOT NULL
  claims          jsonb NOT NULL     -- ClaimPayload[] as returned by /ask
  persona_label   text  NOT NULL
  created_at      timestamptz
  UNIQUE (tour_id, ordinal)
```

This mirrors the client-side `SessionState` in
[`apps/web/src/lib/session-store.ts`](../apps/web/src/lib/session-store.ts)
(`exchanges`, `claimsById`, `firstImpression`, intent profile) so persistence is
a straight save/load of what the UI already holds — no reshaping.

---

## 3. API surface (additions only)

All routes reuse `resolve_session` (the existing signed-cookie dependency), so
they are automatically scoped to the caller — anonymous or logged-in.

```
POST   /tours                      -> {tour_id}          create a tour (repo_id + intent_profile)
GET    /tours                      -> Tour[]             list current session's tours (newest first)
GET    /tours/{tour_id}            -> TourDetail         tour + ordered messages (404 if not owner)
POST   /tours/{tour_id}/messages   -> {ordinal}          append one Q/A exchange
DELETE /tours/{tour_id}            -> 204                 owner-only delete (hard delete, cascade)
GET    /me                         -> {display_name,...} echo identity from product_accounts row
```

Ownership rule: every `/tours/*` query filters on the resolved `session_id`. A
tour that does not belong to the caller returns 404 (not 403 — do not confirm
existence). This is the only authz needed.

Add a thin `TourService` alongside `ProductAccessService` in `access.py` (or a
new `tours.py`) using the same `AsyncEngine`. Follow the existing SQLAlchemy Core
style in `access.py` — no ORM.

---

## 4. Web changes

1. **Auth wiring** (`apps/web`):
   - Add `next-auth@beta` (v5). Create `src/auth.ts` with the GitHub provider and
     `session: { strategy: "jwt" }`.
   - Route handler `src/app/api/auth/[...nextauth]/route.ts`.
   - In the `jwt`/`session` callbacks, compute the stable `session_id =
     uuidv5("github:" + account.providerAccountId)` and stash it on the token.
2. **Bridge login -> signed cookie**: after sign-in, set the `repopilot_session`
   cookie to the HMAC-signed stable `session_id` (same algorithm and secret as
   `app.py::signed_session`). Do this in a server action / middleware so web and
   API agree on identity. Anonymous users are untouched (API still mints a random
   one on first call).
   - `REPOPILOT_SESSION_SECRET` must be **identical** in web and API env.
3. **History UI**: a signed-in header (avatar + name from `/me`), a "Your tours"
   list (`GET /tours`), and resume (`GET /tours/{id}` -> hydrate `SessionState`).
4. **Persist on the fly**: on tour create call `POST /tours`; after each answered
   question in `repopilot-app.tsx`, `POST /tours/{id}/messages`. Keep the current
   in-memory `SessionState` as the live copy; the API calls are write-through.

Client `SessionState` shape does not change — you are serialising the same object.

---

## 5. Config / secrets

Add to `.env` (and document in [`docs/STARTUP_GUIDE.md`](STARTUP_GUIDE.md) and
[`docs/DEPLOYMENT.md`](DEPLOYMENT.md)):

```
# --- Aiven Postgres (replaces local dev DSN in prod) ---
POSTGRES_DSN=postgresql://<user>:<pass>@<name>.aivencloud.com:<port>/defaultdb?sslmode=require

# --- shared identity secret (MUST match between web and api) ---
REPOPILOT_SESSION_SECRET=<random 32+ bytes>

# --- NextAuth / GitHub OAuth (web only) ---
AUTH_SECRET=<random>
AUTH_GITHUB_ID=<oauth app client id>
AUTH_GITHUB_SECRET=<oauth app client secret>
NEXTAUTH_URL=https://<web-host>
```

Aiven specifics: create a **Postgres** service (a Hobbyist/Startup plan is plenty
— "not many people will use this"), enable the **pgvector** extension (the
ingestion schema needs `vector`), copy the *service URI*, keep `sslmode=require`.
`make_engine` in `persist.py` already rewrites `postgresql://` -> `postgresql+psycopg://`,
so paste the raw URI unchanged.

---

## 6. Phased build + copy-paste prompts

Each phase is independently shippable. Run these prompts in order. **None of them
touch evals; if a prompt makes you consider running evals, stop — that is out of
scope.**

### Phase A — Database schema

> Add Alembic migration `0006_product_tours_persist` in
> `packages/ingestion/src/repopilot_ingestion/migrations/versions/`, revises
> `0005_drop_product_tours`. Upgrade: (1) add nullable columns `provider`,
> `provider_account_id`, `display_name`, `email`, `avatar_url` to
> `product_accounts`; (2) recreate `product_tours` exactly as in the `downgrade`
> of `0005_drop_product_tours.py` but also add `title text NULL`, `updated_at
> timestamptz not null default now()`, and index `(session_id, updated_at
> desc)`; (3) create `product_tour_messages` (id uuid pk, tour_id fk ->
> product_tours cascade, ordinal int, question text, answer text, claims jsonb,
> persona_label text, created_at timestamptz default now(), unique(tour_id,
> ordinal)). Write a matching `downgrade`. Then mirror the new tables/columns in
> `apps/api/src/repopilot_api/product_db.py` as SQLAlchemy Core `Table` objects.
> Do not touch evals.

### Phase B — Tour service + API routes

> In `apps/api`, add a `TourService` (new module `tours.py`, or extend
> `access.py`) using the existing `AsyncEngine` and SQLAlchemy Core style from
> `access.py`. Implement: `create_tour(session_id, repo_id, snapshot_repo_id,
> intent_profile, title) -> tour_id`; `list_tours(session_id)`;
> `get_tour(session_id, tour_id)` returning the tour plus ordered messages, or
> None if not owned; `append_message(session_id, tour_id, question, answer,
> claims, persona_label) -> ordinal` (computes next ordinal, bumps
> `updated_at`); `delete_tour(session_id, tour_id)`. Then add the routes in
> `app.py`: `POST/GET /tours`, `GET/DELETE /tours/{tour_id}`, `POST
> /tours/{tour_id}/messages`, and `GET /me`, each depending on the existing
> `resolve_session`. Non-owned tours return 404. Add Pydantic response models in
> `models.py`. Add contract tests using `InMemoryAccessService`-style fakes only
> if a fake is needed; do not run or modify evals.

### Phase C — NextAuth login + shared cookie

> In `apps/web`, add `next-auth@beta`. Create `src/auth.ts` with a GitHub
> provider and `session.strategy = "jwt"`. Add
> `src/app/api/auth/[...nextauth]/route.ts`. In the callbacks compute a stable
> `session_id = uuidv5("github:" + account.providerAccountId, <fixed namespace
> uuid>)`. After sign-in, set the `repopilot_session` cookie to
> `${session_id}.${hmacSHA256(session_id, REPOPILOT_SESSION_SECRET)}` — matching
> `signed_session` in `apps/api/.../app.py` byte-for-byte (same secret, same
> hex/format) — via server-side code (middleware or a server action) so the API
> recognises the user. Leave anonymous visitors untouched. Add sign-in/sign-out
> UI and read identity from `GET /me`. Do not add a NextAuth DB adapter.

### Phase D — Persist + resume tours in the UI

> In `apps/web/src/components/repopilot-app.tsx`, wire persistence to the new
> API: on tour creation call `POST /tours` and keep the returned `tour_id`;
> after each answered question call `POST /tours/{tour_id}/messages` with the
> exchange (question, answer, claims, persona label). Add a "Your tours" list
> (from `GET /tours`) and resume: fetch `GET /tours/{tour_id}` and hydrate the
> existing `SessionState` (`firstImpression`, `exchanges`, `claimsById`) using
> the helpers in `session-store.ts`. Do not change the `SessionState` shape.

### Phase E — Aiven + config + docs

> Point `POSTGRES_DSN` at the Aiven Postgres service URI (keep `sslmode=require`).
> Run `alembic upgrade head` against Aiven (ensure the `vector` extension is
> enabled first). Set `REPOPILOT_SESSION_SECRET` identically in web and api, and
> the `AUTH_*` GitHub OAuth vars in web. Update `docs/STARTUP_GUIDE.md` and
> `docs/DEPLOYMENT.md` with the new env vars and the Aiven setup steps from
> §5. Do not run evals.

---

## 7. Definition of Done (per CLAUDE.md §4)

- [ ] Migration `0006` applies and reverts cleanly against Aiven; `vector`
      extension enabled.
- [ ] Logged-in user's tours, questions, answers, and connected provider persist
      across sessions and devices; anonymous flow still works unchanged.
- [ ] `session_id` is stable per GitHub identity; web and API share
      `REPOPILOT_SESSION_SECRET` and agree on the signed cookie.
- [ ] Non-owned tour access returns 404.
- [ ] `ruff`, `mypy --strict`, and the relevant `pytest` pass for touched code;
      web `typecheck` passes.
- [ ] `docs/STARTUP_GUIDE.md` and `docs/DEPLOYMENT.md` updated.
- [ ] **Evals untouched and not run.**
