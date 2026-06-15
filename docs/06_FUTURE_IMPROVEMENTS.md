# 06 — Future Improvements (Pre-Build Review)
### Tags:
- M : Critical, must fix before Phase 0
- S : Important, should fix before the phase where it bites
- W : Worth doing, would polish v1 but can defer


> **Status:** identified 2026-06-14, before Phase 0 begins.
> **Purpose:** every item below is a doc-level fix that costs minutes now and saves days mid-phase. Work through the **Must** items before starting Phase 0. The **Should** items are best done in the same pass since the marginal editing cost is small. **Worth** items can be deferred to when you're naturally editing that section.

## How to use this document

- Each item names: **what's wrong**, **where in the docs**, **what to do**, **priority**, and a **status checkbox**.
- When you fix an item, check its box and add a one-line note (`- done in <commit-sha>`).
- A future build session should re-read this file at the start of Phase 0 and confirm all **Must** items are checked before any code is written.
- If you discover a new pre-build issue, append it here under the right priority — do not silently fix it in another doc without recording it.

The reading order for build sessions remains: `CLAUDE.md` → `docs/00` → `docs/03` → `docs/04` → matching `docs/05` phase block. This document sits **next to** that chain as a pre-build punch list, not in it.

---

## Critical — must fix before Phase 0

### M1. Verifier latency on local Ollama isn't quantified and will blow the Phase 3 gate

- [ ] **Status:** open

**What's wrong.** `qwen2.5-coder:7b` on Ollama runs ~10–15 tok/s on a typical M-series Mac. A 30-claim tour with ~500 tokens of context per verification call and ~30% retry rate is ~3 minutes of Verifier-only sequential latency. The Phase 3 gate (`Full Learn tour on flask < 4 minutes`) cannot pass without batching.

**Where it lives.** [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) — Verifier loop section. [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 3 gate.

**What to do.**
1. Add a "Verifier batching and concurrency" sub-section to docs/03 specifying:
   - **Per-section batch verification** — all claims in a section verify in parallel via asyncio over Ollama (which supports concurrent requests).
   - **Streaming verification with optimistic display** — claims stream to UI as `unverified`, badge upgrades to `✓ grounded` when verification lands. Verification runs concurrently with the next section's generation.
   - **Hash-based verifier cache** — key = `sha256(claim_text + chunk_hashes)`. Same claim text + same chunks → cached verdict. Huge for re-runs and eval harness.
2. Update Phase 3 gate in docs/04 to require all three.
3. Add a test: `test_verifier_per_section_concurrent` — verifies that the Verifier serves N concurrent requests against Ollama and total wall-clock ≤ ~1.5× a single-request baseline.

---

### M2. Eval dataset labeling is ~30 hours of skilled manual work and isn't on any timeline

- [ ] **Status:** open

**What's wrong.** Across phases:
- `intent_profiling_v1` — 50 labeled intents (Phase 3)
- `planner_correctness_v1` — 50 labeled plans (Phase 3)
- `actionability_v1` — 20 sections (Phase 3)
- `httpx_qa_v1` — 15 Q&A pairs (Phase 2)
- `opportunity_quality_v1` — ~30 × 3 repos (Phase 5)
- `file_mapping_v1` — 20 opportunities (Phase 5)

~155 items, each 5–15 min to label well = **15–35 hours of dedicated labeling**. Currently invisible in phase budgets.

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 2, 3, 5 task checklists.

**What to do.**
1. Add 1–2 days of explicit **"eval-labeling time"** to each of Phase 2 (Q&A), Phase 3 (intent + planner + actionability), Phase 5 (opportunity + file mapping).
2. Optionally: introduce a "Phase 0.5 — Eval Bootstrap" milestone where the contributor labels the Phase 2 dataset first, so Phase 2's gate is verifiable from day one.
3. Update the "sized 3–7 days solo" line in [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) intro to "sized 3–14 days solo, including eval-labeling time."

---

### M3. Capability "independence" claim is false; the Planner needs a dependency DAG

- [ ] **Status:** open

**What's wrong.** Docs claim every capability runs standalone with a synthetic `IntentProfile`. In reality:
- **Flow Tracer** needs a starting symbol (from Cartographer or `focus_keywords`).
- **Decision Archaeology** needs candidate hubs (from Cartographer).
- **Teacher** needs at least one upstream capability's output.

`CapabilityPlan.active` is a **DAG**, not a flat list. The `test_capability_library_independence` gate as written would either fail honestly or pass dishonestly.

**Where it lives.** [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) — `CapabilityPlan` schema, Capability Planner section. [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) + [docs/05_PHASE_PROMPTS.md](05_PHASE_PROMPTS.md) — Phase 3 gates.

**What to do.**
1. Add `dependencies: dict[CapabilityName, list[CapabilityName]]` to `CapabilityPlan` in docs/03's state schema.
2. Update the Capability Planner sketch to emit dependencies (e.g., Flow Tracer depends on Cartographer unless `focus_keywords` provides a starting symbol).
3. Reframe the Phase 3 gate: rename `test_capability_library_independence` → `test_capability_library_dependencies_satisfied`. The test asserts: any active capability can run *given its declared dependencies are satisfied*, never in isolation if it declared a dependency.
4. Note: LangGraph natively supports topological ordering — wire `capability_plan.dependencies` into the graph compilation.

---

### M4. Phase 4 (Experience) is undersized; realistic budget is 10–14 days

- [ ] **Status:** open

**What's wrong.** Phase 4 builds: FastAPI with 5 endpoints + SSE protocol + chunk endpoint; Next.js 15 RSC app with URL input + indexing progress + intent capture screen with chip strip + first-impression panel + tour split-pane + streamed claims with verified-badge + retrieval-path chip + mermaid renderer + shiki synchronized code viewer + Q&A box + re-plan flow + considered-and-rejected disclosure (added in Phase 5) + per-opportunity CTAs; plus Playwright e2e + Lighthouse + SSE stability test.

The "3–7 day solo" budget is wildly optimistic. Realistic is **10–14 days**.

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 4 intro line and the phase-overview paragraph at the top of the file.

**What to do.**
1. Update [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) intro: "sized 3–14 days solo" (already noted in M2 above; merge edits).
2. Add a callout at the top of Phase 4: **"This is the longest phase. Honest budget: 10–14 days. The synchronized code viewer + the streaming protocol + the intent-edit re-plan flow are each their own subproject."**

---

### M5. Inconsistent beachhead language between docs/00 and docs/01

- [ ] **Status:** open

**What's wrong.** [docs/00_CLAUDE_BUILD_GUIDE.md](00_CLAUDE_BUILD_GUIDE.md) line 9 still reads *"The beachhead is **junior developers and first-time OSS contributors**."* [docs/01_PROBLEM_AND_SOLUTION.md](01_PROBLEM_AND_SOLUTION.md) has widened to "anyone with a stated purpose." Every phase prompt reads docs/00, so the bucketed framing will leak back into implementation.

**Where it lives.** [docs/00_CLAUDE_BUILD_GUIDE.md](00_CLAUDE_BUILD_GUIDE.md) project one-liner.

**What to do.** Two-line edit. Replace *"The beachhead is junior developers and first-time OSS contributors working on Python repositories on public GitHub"* with *"It serves any developer with a stated purpose, working on Python repositories on public GitHub. The constraint is in the technology (Python, public GitHub, ≤ 200kLOC) and the intent-elastic capability library, not in who shows up."*

---

## Important — fix before the phase where it bites

### S1. Mermaid generation is unverifiable and can lie confidently

- [ ] **Status:** open

**What's wrong.** The Teacher emits mermaid diagrams. The Verifier checks claims (text + refs) but **does not** check mermaid structural correctness. A wrong diagram (`A → B → C` when graph is `A → B → D`) is a confident visual lie. Violates principle 1 (truthful over fluent).

**Where it lives.** [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) — Teacher description. [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 3 + Phase 4.

**What to do.** Mermaid is **emitted deterministically from graph queries, not LLM-generated**. The Teacher names the diagram type ("call chain for `flask.Flask.dispatch_request`") and a Python helper builds the mermaid string by walking the graph. Alternatively, skip mermaid in v1 — the synchronized code viewer is the diagram. Pick one; document it; add a Phase 3 test that fails if any mermaid contains an edge not present in the graph adjacency.

---

### S2. Per-tour Groq token budget hasn't been calculated; launch concurrency will stall

- [ ] **Status:** open

**What's wrong.** A typical Learn tour: Cartographer ~2k tokens out + Flow Tracer ~3k + Teacher ~4k + Verifier retries ~2k = ~11k+ tokens per tour on the 70B for one user. Groq's 6k TPM cap means **one tour ~exhausts a minute of quota**. Two concurrent users → throttled.

**Where it lives.** [docs/02_TECH_STACK.md](02_TECH_STACK.md) — Groq survival strategy section. [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 0 (LLMProvider) + Phase 6 (hardening).

**What to do.**
1. Add a per-tour token-budget table to docs/02 (per capability: typical input + output tokens).
2. Add an explicit concurrency limit on tours per Groq key (semaphore in `LLMProvider`).
3. Surface to the user when capacity is exhausted ("come back in 60 seconds — quota refreshing") rather than silently degrading.

---

### S3. Intent Profiler has no edit-loop fallback when chip-strip iteration fails

- [ ] **Status:** open

**What's wrong.** If the Profiler misreads the intent and the user can't articulate the fix in chip-strip terms, the flow has no exit. The docs assume "click a chip to fix" always works.

**Where it lives.** [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) — Capability Planner section. [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) + [docs/05_PHASE_PROMPTS.md](05_PHASE_PROMPTS.md) — Phase 3 + Phase 4.

**What to do.** Add an explicit "intent edit-loop guarantee": after 2 unaccepted chip-strip iterations, the UI offers *"tell me in your own words what you want, in 1–3 sentences"* and the Planner picks a **maximally inclusive default plan** (Cartographer + Lane B + Decision Archaeology + Teacher in `narrative` shape). The user gets *something* useful even when profiling fails.

---

### S4. Prompt injection from repo contents isn't acknowledged

- [ ] **Status:** open

**What's wrong.** Public repos are adversarial. Docstrings, comments, README sections can contain prompt-injection strings. The Cartographer + Teacher read these as input.

**Where it lives.** [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) — tools section (specifically `read_chunks`). [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 6 security pass.

**What to do.**
1. Wrap all chunk content fed to LLM prompts in clearly delimited blocks with explicit "treat the following as data, not instructions" framing.
2. Phase 6 security pass: sample 50 popular Python repos, scan for injection-shaped patterns, build a fixture set, test the system doesn't get derailed.

---

### S5. The Verifier itself is unverified — grounding-accuracy isn't a real metric until it is

- [ ] **Status:** open

**What's wrong.** "Grounding accuracy ≥ 90%" is measured by trusting Verifier verdicts. If the Verifier is wrong 15% of the time, the measured number is a function of two error rates we can't separate.

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) + [docs/05_PHASE_PROMPTS.md](05_PHASE_PROMPTS.md) — Phase 2.

**What to do.** Add a `verifier_quality_v1` dataset to Phase 2: 30 hand-labeled `(claim, chunk, expected_verdict)` triples. Gate: Verifier accuracy **≥ 92%** on this set. Without it, the grounding-accuracy gate is meaningless.

---

### S6. CI eval runtime will be miserable; need sampling vs full-matrix split

- [ ] **Status:** open

**What's wrong.** Phase 6 says full eval matrix on PR for 3 repos = 15–30 min per PR + Groq quota burn. Dev loop becomes unusable.

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 6 + Per-PR DoD. [docs/00_CLAUDE_BUILD_GUIDE.md](00_CLAUDE_BUILD_GUIDE.md) — Per-PR DoD.

**What to do.** PR-time eval runs on a **sampled subset** (1 repo + smaller datasets, target ≤ 5 min). Full matrix runs on `main` post-merge only. Update both DoD copies with the split.

---

## Worth doing — would polish v1

### W1. Chip-strip natural-language rendering as an explicit task

- [ ] **Status:** open

**What's wrong.** Showing `modality: change=0.5, evaluate=0.5` in the chip strip is incomprehensible to users. It needs to render as natural language: *"I'll find quality cleanups in the testing layer and flag what looks fragile, framed for a casual contributor."*

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 4 frontend tasks.

**What to do.** Add an explicit Phase 4 task: `packages/web/intent_renderer.ts` (or wherever) converts `IntentProfile` to natural-language sentences for the chip strip. Snapshot tests pin sample renderings.

---

### W2. Lane A "rejected reason" is its own LLM task and needs eval coverage

- [ ] **Status:** open

**What's wrong.** Lane A says "we looked at #234 but it touches a hub of fan-in 47" — a generation task with its own failure modes. Currently not in `opportunity_quality_v1`.

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 5 eval datasets.

**What to do.** Extend `opportunity_quality_v1` labels with a `rejected_reasons_honest: bool` field for the considered-and-rejected trail. Phase 5 gate: ≥ 80% honest on hand review.

---

### W3. Session non-persistence is undefined; should be explicit

- [ ] **Status:** open

**What's wrong.** Closing the tab loses the tour. Re-opening starts fresh. This is fine for v1 but the doc set is silent.

**Where it lives.** [docs/01_PROBLEM_AND_SOLUTION.md](01_PROBLEM_AND_SOLUTION.md) — scope fence. [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — post-v0.1 backlog.

**What to do.** Add to scope fence: *"No session persistence in v1 — tours are ephemeral. Re-opening the app starts fresh. Shareable tour URLs are post-v0.1."* Add "session persistence + shareable URLs" to the backlog table.

---

### W4. Default plan should include Lane B for generic intents

- [ ] **Status:** open

**What's wrong.** Many real users will paste a URL and write "explain this repo" — generic. The default plan (`cartographer + teacher + narrative`) is non-empty but doesn't show the system's strongest moves. Adding lightweight Lane B (untested-hot-code + missing docstrings only) surfaces the obvious quality signals even on a generic intent.

**Where it lives.** [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) — Capability Planner sketch.

**What to do.** Update the planner's default-fallthrough plan to `["cartographer", "lane_b_code_health", "teacher"]` with a lightweight Lane B tilt. Add `test_default_plan_includes_lane_b` to Phase 3.

---

---

## Second-pass review additions (2026-06-14)

A deeper audit after the first pass surfaced 11 more gaps. Same severity scheme.

### M6. Failure modes catalog is thin; the architecture is hand-wavy on partial failures

- [ ] **Status:** open

**What's wrong.** [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) has a "Failure modes and cost design" table that covers 8 scenarios. The real-world surface is much wider and several common ones aren't covered:

- **Repo has no Python files** (or only `__init__.py`). What does the system do? Currently undefined.
- **Repo has Python 2 only syntax.** tree-sitter-python parses both, but type assumptions break.
- **Tree-sitter unresolved dynamic calls** (decorator-rewritten signatures, `getattr`, metaclass magic). Currently logged as warnings — but the graph is now structurally incomplete and Lane C's "no error handling on this call" claim may be wrong.
- **Postgres is down mid-indexing.** Indexing job retries? Fails the user request?
- **Ollama service crashes mid-tour.** Verifier is gone — does the tour fail, or do we degrade to "all claims unverified"?
- **pgvector returns zero results** for a Q&A query. Currently undefined behavior in Q&A.
- **The user's repo URL is invalid / private / redirected / 404.** Currently undefined error UX.
- **A chunk's source content has been deleted** (git rebase, force-push) between indexing and tour generation. `read_chunks` would fail; behavior undefined.
- **Indexing pipeline partial failure** — chunks succeeded but graph builder errored. Currently undefined.

**Where it lives.** [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) — failure modes table. [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 1 + Phase 4.

**What to do.**
1. Extend the failure modes table in docs/03 with the 9 scenarios above. Each gets a detection mechanism and a mitigation.
2. Add a Phase 1 test: `test_repo_without_python_files_rejected_with_useful_message`.
3. Add a Phase 4 test: `test_indexing_failure_renders_actionable_error_ux`.
4. Define a typed `ArchaeologistError` enum and require every fail-edge in the graph to emit one.

---

### M7. Decision Archaeology was added as a capability but Phase 3 doesn't include building it

- [ ] **Status:** open

**What's wrong.** The elastic-intent refactor added Decision Archaeology to the capability library and the agent table in [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md). But [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) Phase 3 task list does not include building it — Phase 3 still describes "Cartographer → Flow Tracer → Teacher". Phase 5 doesn't include it either. So as written, Decision Archaeology is in the schema but never gets built.

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) + [docs/05_PHASE_PROMPTS.md](05_PHASE_PROMPTS.md) — Phase 3 and Phase 5.

**What to do.** Pick one:
1. **Defer Decision Archaeology to v0.2.** Update docs/03 to mark it as "post-MVP, schema reserved" and remove it from the planner's active rules in v1. Cleanest path.
2. **Include it in Phase 3.** Add task `packages/agents/build/decision_archaeology.py` with git-log + README + commit-message extraction. Add ~2 days to Phase 3 budget. Add eval set for decision fidelity.
3. **Include it in Phase 5.** Move it out of "Learn" mental model and into the contribute-shaped phase. Add ~2 days to Phase 5.

Recommendation: option 1 (defer to v0.2). The architecture stays elastic; the implementation surface stays narrow. Update docs/03's capability library description to flag Decision Archaeology as "schema-reserved, post-v0.1."

---

### S7. Auth, rate-limiting, and GitHub API token sourcing is undefined — Lane A breaks on day one

- [ ] **Status:** open

**What's wrong.** Lane A uses PyGithub to fetch open issues. Unauthenticated GitHub API requests are capped at **60 per hour per IP**. The first 60 users in an hour on launch day all share that quota. Authenticated requests get 5,000/hour but require a token. The docs are silent on:

- Where the GitHub token comes from (server-shared PAT vs. user-supplied vs. OAuth).
- Per-IP rate limiting on the FastAPI endpoints (mentioned briefly in Phase 6 but no spec).
- How quota exhaustion surfaces to the user.

**Where it lives.** [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) — `github_issues` tool. [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 2 + Phase 6.

**What to do.**
1. v1 default: **a server-side PAT in `.env`** (read-only scope: `public_repo`). Document that this is a shared resource and rate-limited. Cache aggressively — same repo + same hour = same cached issues.
2. Specify a per-IP rate limit on `POST /tours` (e.g., 5 tours/IP/hour) using `slowapi`.
3. When quota approaches exhaustion, Lane A degrades to a clear message ("we couldn't fetch issues — Lane A is paused for the next N minutes") rather than failing silently.
4. Future: "bring your own PAT" — but for v1, server-side PAT is enough.

---

### S8. The "retrieval-path chip on every claim" claim is too broad

- [ ] **Status:** open

**What's wrong.** [docs/00_CLAUDE_BUILD_GUIDE.md](00_CLAUDE_BUILD_GUIDE.md) and [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) say every claim shows a retrieval path (`vector_search → graph_traverse · 2 hops`). But:

- **Lane B claims** come from deterministic detectors (no retrieval). Their "path" is more like `lane_b:detector=untested_hot_code`.
- **Lane C claims** come from pre-filtered structural patterns (no retrieval). Their "path" is `lane_c:pattern=swallow_except`.
- **Cartographer claims** come from graph queries, not vector + graph traversal. Their "path" is `cartographer:hub_query`.

The current "retrieval-path chip" framing only fits Q&A and (some) Flow Tracer claims.

**Where it lives.** [docs/00_CLAUDE_BUILD_GUIDE.md](00_CLAUDE_BUILD_GUIDE.md) Trust surfaces, [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) Trust surfaces, [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) Phase 4.

**What to do.** Rename to **"provenance chip"**. Every claim carries a `provenance` field on the SSE `claim` event with a typed source descriptor — one of `vector_then_graph`, `graph_only`, `deterministic_detector(name)`, `structural_pattern(name)`. The chip renders whichever applies. Update docs/03's `claim` event schema and the Phase 4 deliverables list. Trust is preserved; honesty is too.

---

### S9. No user-feedback mechanism in v1 — we'll learn nothing outside the eval set

- [ ] **Status:** open

**What's wrong.** The eval set is hand-labeled in `evals/`. After launch, real users will encounter cases that aren't in any eval set. With no feedback mechanism, we can't tell which sections worked vs didn't, which Q&A answers were trusted, which opportunities were acted on. Eval-set quality plateaus quickly without real signal.

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 4 + Phase 6.

**What to do.** Add a Phase 4 task: a tiny feedback affordance on every section — a quiet "did this help? 👍 / 👎 / explain" inline. Anonymous, opt-in, written to a `feedback` table with `(section_text, claim_ids, intent_profile_id, signal, freeform)`. No accounts. Surface aggregated counts to a maintainer-only debug page in Phase 6. Don't try to do anything clever with the data in v1 — just collect it.

---

### S10. Indexing edge cases (Python 2, `.pyi`, `.ipynb`, vendored deps, generated code) are unspecified

- [ ] **Status:** open

**What's wrong.** Real Python repos contain more than `.py` files written in Python 3:

- **`.pyi` type stub files** — should we index them? Useful for understanding public surface; not executable.
- **`.ipynb` Jupyter notebooks** — large repos like fastai have many. Currently undefined.
- **Vendored dependencies** (`vendor/`, `third_party/`, `_vendor/`) — including them inflates the graph and pollutes Lane B with code the maintainers don't own.
- **Generated code** (proto-generated, openapi-generated, alembic migrations) — high churn but not meaningful to a contributor.
- **Python 2 syntax** (still in some older repos and CI compat shims) — tree-sitter parses it, but our type assumptions may break.

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 1 ingestion.

**What to do.** Add a Phase 1 sub-task: a default skip-list (configurable). `.pyi` indexed but tagged separately. `.ipynb` skipped in v1, noted in scope fence. `vendor/`, `third_party/`, `_vendor/` skipped by default. Generated-code detection via marker comments (e.g., `# Generated by`) skipped. Python 2 syntax detected (look for `print` statement, `except X, e:`) and warned; index anyway but tag.

---

### S11. Embedding model versioning + migration story is missing

- [ ] **Status:** open

**What's wrong.** Embeddings are stored in pgvector for every chunk. If Ollama bumps `nomic-embed-text` (or we switch models for a v0.2 quality boost), the stored embeddings are silently incompatible — new queries get embedded with one model, existing vectors are from another, retrieval quality silently degrades.

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 1 persistence schema.

**What to do.** Store the embedding model name + version on each row in `chunk_embeddings`. Indexing job records the current embedding model in the `repos` table. On Q&A, the query embedding is generated with the model that matches the stored vectors. A re-index trigger fires automatically when the configured model differs from the stored one.

---

### S12. Concurrent indexing of the same repo is a race condition

- [ ] **Status:** open

**What's wrong.** Two users paste the same repo URL within 90 seconds. The arq worker picks up both jobs. Both clone, both parse, both write to Postgres. Without a uniqueness constraint and a row-level lock, you get duplicate chunks, duplicate embeddings, an inconsistent graph adjacency, and possibly a deadlock.

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 1 idempotency + arq job design.

**What to do.** The arq job acquires a Postgres advisory lock keyed on `(repo_url, head_sha)` before doing any work. A second concurrent job for the same key short-circuits to "wait for existing indexing", polls the `repos.status` field, and returns the cached `repo_id` when the first one completes. Add `test_concurrent_indexing_same_repo_does_not_duplicate`.

---

### W5. Repo update detection on revisit is undefined

- [ ] **Status:** open

**What's wrong.** A user came to repo `X` last week; the system indexed `X` at SHA `abc123`. This week, `X` is at SHA `def456` (active project, 50 new commits). The user pastes the URL again. Do we re-index automatically, warn them about staleness, or silently use the old index?

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 1 idempotency, Phase 4 UX.

**What to do.** On a repo revisit, the API does a lightweight `git ls-remote` (no clone) to get current HEAD. If it differs from `repos.head_sha`, the UI shows a small banner: *"This repo has new commits since we last indexed it. Re-index? (~90s)"* Re-indexing is opt-in. The "first impression" panel can stream from the cached index immediately while the user decides.

---

### W6. Production deployment story missing — Docker Compose is dev-only

- [ ] **Status:** open

**What's wrong.** [docs/02_TECH_STACK.md](02_TECH_STACK.md) and the build plan describe `docker compose up` for local dev. No story for hosting the v1 demo: Vercel/Railway/fly.io? Where does Postgres run? Where does Ollama run? Ollama notably **cannot easily run on serverless** because of the model weights.

**Where it lives.** [docs/04_BUILD_PLAN.md](04_BUILD_PLAN.md) — Phase 6 ship.

**What to do.** Add a Phase 6 task: explicit deployment topology doc. v0.1 baseline:
- **Frontend** → Vercel (Next.js native; free tier).
- **API + arq worker** → fly.io or Railway (small VM, ~$5/mo).
- **Postgres + pgvector** → Neon or Supabase (free tier).
- **Ollama (Verifier + Embeddings)** → on the same fly.io VM (need ≥ 4GB RAM for qwen2.5-coder:7b q4) OR a separate small VM.
- **Redis** → Upstash (free tier).

Total monthly cost estimate at idle: $5–15. Document this so reviewers know the demo is hostable, not just local.

---

### W7. Q&A conversation thread / multi-turn — currently each question is independent

- [ ] **Status:** open

**What's wrong.** The Q&A subgraph as designed treats each question as standalone. A user asking *"how does middleware work?"* then *"how does my middleware get registered?"* loses context — the second question's "my" can't refer to the first answer's content. Real users will ask sequential, building questions.

**Where it lives.** [docs/03_ARCHITECTURE.md](03_ARCHITECTURE.md) — Q&A subgraph.

**What to do.** Add a `qa_history: list[QAExchange]` field to `ArchaeologistState`. The Q&A prompt includes the last 3 exchanges (capped). The `IntentProfile` plus history plus the current question form the Q&A input. This is a small change but a real UX upgrade. Not v1-blocking, but worth doing post-Phase-4.

---

## Application order

Recommended order if applying in one pass:

1. **M5** (beachhead) — trivial, blocks everything else
2. **M7** (Decision Archaeology defer-or-build) — affects schema + Phase 3 budget; resolve early
3. **M3** (capability dependencies) — architectural; touches state schema
4. **M6** (failure modes catalog) — architectural; touches docs/03 failure table + Phase 1/4
5. **M1** (Verifier batching) — architectural; touches Verifier loop design
6. **M2** (eval labeling time) + **M4** (Phase 4 budget) — schedule realism, can edit together
7. **S7** (auth/rate-limit/GH token) — Phase 0 LLMProvider + Phase 6; affects Phase 0 scope
8. **S8** (provenance chip rename) — touches SSE schema and UI claims everywhere
9. **S11** (embedding versioning) + **S12** (concurrent indexing) — both touch Phase 1 persistence; edit together
10. **S1–S6, S9, S10** in any order — local edits
11. **W1–W7** in any order — local edits

Total estimated editing time: **90–120 minutes** for Must + Should (now 13 items); another 45 minutes for Worth (now 7 items).

## Sign-off checklist (do not start Phase 0 until all checked)

- [ ] All **M** items (M1–M7) checked and committed
- [ ] All **S** items (S1–S12) either checked or explicitly deferred with a written reason
- [ ] All eval datasets that block Phase 2/3/5 gates have been scoped (even if not yet labeled)
- [ ] Per-tour token budget calculated and concurrency limit chosen (S2)
- [ ] GitHub token sourcing decided and `.env.example` updated (S7)
- [ ] Embedding-model version column added to `chunk_embeddings` schema (S11)
- [ ] Concurrent-indexing lock strategy decided (S12)
- [ ] Failure modes table extended with the 9 new scenarios (M6)
- [ ] Decision Archaeology status decided: built-in-v1 or deferred-to-v0.2 (M7)
- [ ] CLAUDE.md updated if any of the above introduced new project-wide conventions
- [ ] This document committed and pushed before Phase 0 PR is opened
