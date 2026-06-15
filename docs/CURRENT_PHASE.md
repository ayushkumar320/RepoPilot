# Current Build Phase

> **Active phase:** **Phase 1 — Ingestion** (not yet started)
> **Last verified gate:** Phase 0 — `make ci` green; LLMProvider forced-429 storm test passes (Groq+Cerebras 429ing indefinitely → Ollama answers, well under the 30s budget).
> **Last updated:** 2026-06-15

This document is the **always-correct pointer** at where the build is. Anyone (human or agent) starting a session reads this first to find the active phase and what's left on its gate.

## Phase ladder

| Phase | Status | Spec | Gate |
|---|---|---|---|
| 0 — Foundation | 🟢 **done** | [docs/04 §Phase 0](04_BUILD_PLAN.md) · [docs/05 §Phase 0 prompt](05_PHASE_PROMPTS.md) | ✅ `make ci` green · ✅ forced-429 → Ollama under 30s · ⚠️ `docker compose up -d ≤90s` needs verification on host with Docker |
| 1 — Ingestion | 🟡 **active** | [docs/04 §Phase 1](04_BUILD_PLAN.md) · [docs/05 §Phase 1 prompt](05_PHASE_PROMPTS.md) | Indexing httpx ≤90s · 20-chunk content-equality · known call-chain path · idempotent re-run · revisit-staleness returns `stale` |
| 2 — Hybrid Retrieval + Q&A (the spine) | ⚪ pending | [docs/04 §Phase 2](04_BUILD_PLAN.md) · [docs/05 §Phase 2 prompt](05_PHASE_PROMPTS.md) | Grounding ≥90% · multi-hop test · forced-hallucination test |
| 3 — Orchestration + Learn | ⚪ pending | [docs/04 §Phase 3](04_BUILD_PLAN.md) · [docs/05 §Phase 3 prompt](05_PHASE_PROMPTS.md) | Profiler ≥90%/field · Planner F1 ≥90% · two-intent divergence ≥50% on flask · CI grep "no purpose enum" |
| 4 — Experience | ⚪ pending | [docs/04 §Phase 4](04_BUILD_PLAN.md) · [docs/05 §Phase 4 prompt](05_PHASE_PROMPTS.md) | Cold-start demo · time-to-first-output ≤12s · Lighthouse a11y ≥90 |
| 5 — Contribute (Iteration 1) | ⚪ pending | [docs/04 §Phase 5](04_BUILD_PLAN.md) · [docs/05 §Phase 5 prompt](05_PHASE_PROMPTS.md) | Top-3 approachability ≥70% · file-mapping ≥80% · suspicion legitimacy ≥75% · banned-vocab regex |
| 6 — Harden and ship | ⚪ pending | [docs/04 §Phase 6](04_BUILD_PLAN.md) · [docs/05 §Phase 6 prompt](05_PHASE_PROMPTS.md) | Full eval matrix green · gitleaks + audits clean · clean-VM quickstart ≤5min · `v0.1.0` tagged |

Legend: 🟢 done · 🟡 active · ⚪ pending · 🔴 blocked.

## Phase 0 — what landed

- [x] Monorepo layout (`apps/`, `packages/`, root `pyproject.toml` with uv workspace)
- [x] Tooling: ruff, mypy `--strict`, pytest + pytest-asyncio + pytest-cov
- [x] `.pre-commit-config.yaml` (ruff, mypy on touched files, gitleaks, EOF/whitespace)
- [x] `.github/workflows/ci.yml` (install → lint → format-check → typecheck → test → coverage 80% → gitleaks → eval stub job)
- [x] `docker-compose.yml` for Postgres 16 + pgvector, Redis 7, Ollama (with `infra/ollama/entrypoint.sh` preloading `qwen2.5-coder:7b` and `nomic-embed-text`)
- [x] `packages/core/llm/models.py` — `ModelId` enum + per-model `RESOLUTION` chain across Groq → Cerebras → Ollama
- [x] `packages/core/llm/provider.py` — `LLMProvider` (SQLite cache, 429 backoff w/ jitter, fallback chain, per-`ModelId` `tokens_used` counter)
- [x] `packages/core/logging.py` — structlog setup (JSON in prod/CI, dev renderer in tests); chunk-content stripping processor
- [x] `packages/core/settings.py` — pydantic-settings + `.env.example`
- [x] All **5 TDD tests** from `docs/05_PHASE_PROMPTS.md § Phase 0`:
    1. ✅ `test_llm_cache_hit_avoids_api_call`
    2. ✅ `test_llm_429_backoff_retries` (+ `test_backoff_delay_is_bounded`)
    3. ✅ `test_llm_forced_429_storm_falls_back_to_ollama` (+ `test_real_httpx_429_path` end-to-end via respx)
    4. ✅ `test_llm_token_counter_increments`
    5. ✅ `test_settings_loads_from_env_example`
- [x] `make ci` green locally: **13 passed, coverage 91.37%** on `packages/core` (gate: 80%).

### Pending Phase 0 verifications (host-bound, do these on your machine)

- [ ] `docker compose up -d` on a fresh checkout reaches the `healthy` state in ≤ 90 s. The Ollama service performs an initial model pull on first run; subsequent runs reuse the named volume and meet the budget.
- [ ] GitHub Actions CI run on first push must be green end-to-end (it mirrors `make ci` plus gitleaks).
- [ ] `uv run pre-commit run --all-files` clean (mypy hook may bootstrap stubs on first run).

When those three are confirmed, mark the docker line on the Phase 0 row as ✅ here — and move on.

## Phase 1 — kickoff checklist

The active phase. Read [`docs/05_PHASE_PROMPTS.md` § Phase 1 prompt](05_PHASE_PROMPTS.md) and ship in this order:

1. Postgres migrations (alembic) — `repos`, `chunks`, `chunk_embeddings`, `graph_adjacency` + `vector(768)` columns and `ivfflat` index.
2. `packages/ingestion/clone.py` (GitPython, tempdir, cleanup).
3. `packages/ingestion/parse.py` (tree-sitter-python ParsedFile with exact spans) + `chunk.py` (structural chunker, no mid-statement boundaries).
4. `packages/ingestion/graph.py` (NetworkX with `calls` / `imports` / `inherits` edges; log unresolved dynamic patterns, never invent).
5. `packages/ingestion/summary.py` (8B summaries through the LLMProvider, cached, semaphore-bounded).
6. `packages/ingestion/embed.py` (Ollama `nomic-embed-text`, batched, async).
7. `packages/ingestion/persist.py` (writes everything; idempotent on `(repo_url, head_sha)`; Postgres advisory lock per docs/06 S12).
8. `apps/api/jobs/index_repo.py` (arq job orchestration).
9. Revisit staleness endpoint (`git ls-remote` HEAD compared against `repos.head_sha` → `{status: "stale", ...}`).
10. TDD tests 1–5 from the Phase 1 prompt + `test_concurrent_indexing_same_repo_does_not_duplicate` (M / S items from the applied future-improvements review).

## How to advance the phase

1. Pick the next unchecked item on the active phase's checklist and write the test first.
2. When all of the active phase's gate items pass on the machine (not just in mocks), flip the phase to 🟢, flip the next to 🟡, and update **Last verified gate**.
3. Paste the next phase's prompt from `docs/05_PHASE_PROMPTS.md` into a fresh session.

> If a phase fails its gate, it stays 🟡 — never silently advance. Either fix the failure or write down explicitly why the gate was relaxed (and update `docs/04_BUILD_PLAN.md` if the relaxation is permanent).
