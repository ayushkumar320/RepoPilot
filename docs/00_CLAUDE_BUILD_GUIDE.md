# 00 — Claude Build Guide (Standing Context)

> **Paste this file at the top of every build session.** It is the standing context every phase prompt assumes. It does not change between phases; the phase prompt in `05_PHASE_PROMPTS.md` adds the phase-specific goal and deliverables on top of this.

---

## Project one-liner

**Codebase Archaeologist** is a web app where a developer pastes a public GitHub repo URL and gets a **purpose-driven, guided onboarding tour** of an unfamiliar codebase, powered by a multi-agent AI system. The beachhead is **junior developers and first-time OSS contributors** working on **Python repositories** on **public GitHub**. We do not try to be a general code-search tool, an IDE plugin, or a multi-language platform in v1.

The single distinguishing bet: **before analyzing anything, the system captures pre-context about the user and adapts to it.** Pre-context capture is a deliberate, visible, first-class phase — not a hidden inference. It happens in two layers:

1. **Purpose** (the why) — "why are you here?" Two purposes are supported:
   - **LEARN** — build a mental model of the system (system map → traced flow → narrative).
   - **CONTRIBUTE** — find a realistic first PR (ranked opportunity list → briefing).
2. **Focus** (the lens) — once the purpose is known, ONE follow-up elicitation:
   - LEARN → "what part interests you most? (overall structure / a specific feature / the data model)"
   - CONTRIBUTE → "what kind of contribution? (fix an issue / improve quality / hunt problems / show all)"

These two answers are the **user's pre-context**. They are persisted in state as `purpose`, `focus_hint`, and `contribution_intent`, and **every subsequent generation prompt — Cartographer, Flow Tracer, Teacher, scanners, Q&A — receives them as goal anchors**. The same repo produces meaningfully different output for a learner who said "data model" than for an OSS contributor who said "hunt problems".

A third, always-on path is the **Q&A escape hatch**: at any point the user can ask a direct question and get a grounded, citation-backed answer — still answered through the lens of their captured pre-context.

### Why pre-context is the first step (not inferred mid-flight)

Existing tools either skip this question (Sourcegraph, GitHub search) or fake it with a generic chat box (Cursor, ChatGPT) and infer purpose from the user's phrasing. We do not. Inferring "this user wants to contribute" from a passing phrase produces a tour that drifts. **A deliberate two-question elicitation costs the user ~10 seconds and earns the system the right to be opinionated about what to surface.** Every "why am I being shown this?" reduces to "you told us X, so we're showing you Y" — and that traceability is itself a trust property.

### Pre-context capture runs IN PARALLEL with indexing — never after it

A naive flow is: paste URL → wait 90s for indexing → answer elicitation → tour. That makes the user stare at a progress bar before they can engage. We do not ship that flow. The correct sequence:

1. User pastes URL → indexing job enqueued immediately (background).
2. **Same screen, no waiting**: Intent Router elicitation appears.
3. **Next screen, while indexing still running**: branch-specific elicitation (focus_hint / contribution_intent).
4. By the time both elicitations are answered (~15–25s of human time), indexing is usually finished. If it isn't, the tour view shows a slim progress bar at the top and starts generating once `repo.status == ready`.
5. **At the 10-second mark** of indexing, an 8B "first impression" paragraph (repo language mix, top hubs, last-commit recency, primary entry point) streams in below the elicitation. This makes the wait productive and demonstrates the system is alive.

Time-to-first-useful-output, not time-to-indexing-complete, is the metric.

### The four trust surfaces — make every moat visible

Every architectural moat we have over competitors must be **visible in the UI**, or the user cannot tell us apart from a fluent chatbot. These four surfaces are non-negotiable:

| Moat | UI surface |
|---|---|
| **Verified grounding** | Every Claim shows a small "✓ grounded" badge when `status == "verified"`. Hover reveals the verifier's confirmation and the chunk it grounded against. Claims with `status == "flagged"` render with a distinct warning treatment — never silently dropped. |
| **Hybrid retrieval (vector + graph)** | Every Claim and every Q&A answer shows its retrieval path on hover: e.g., `vector_search(k=8) → graph_traverse(2 hops)`. Competitors using pure vector search cannot show this — that's the point. |
| **Purpose traceability** | A persistent "You said:" chip at the top of the tour shows the captured pre-context. Every Opportunity card carries an "intent match" chip ("matches: hunt problems"). Lane A surfaces a "considered and rejected" trail for the top-3 ranked-down issues so the user sees the triage thinking, not just the verdict. |
| **Action over narrative** | Every section ends in a button or copyable next step. Contribute briefings end with "Open files on GitHub" and "Copy first step" buttons per opportunity — never in prose alone. |

---

## The five principles

These are non-negotiable and govern every prompt, every agent, every UI choice.

1. **Truthful over fluent.** Every factual claim carries a `file:line` reference. When the system doesn't know, it says "not sure" or "I couldn't find that" — it does not invent. Verifier rejection is shown to the user as "flagged", never silently dropped.
2. **Teach, don't dump.** Output is progressive disclosure. No stat dumps. No 600-line summaries. A section ends when the user can take a next action.
3. **Meet the purpose — captured first, applied everywhere.** Pre-context (`purpose`, `focus_hint`, `contribution_intent`) is captured explicitly before any analysis runs, and it is injected into every generation prompt downstream. Two users opening the same repo should see meaningfully different tours, and they can both point at the moment the system "earned" that difference.
4. **Narrow and deep.** Python + Learn mode must be excellent before we widen to other languages or modes. Going broad early is failure.
5. **Earn trust on real repos.** Quality is enforced by an evaluation harness that runs against real-world Python repositories (fastapi, httpx, flask) — not synthetic fixtures.

---

## Iteration 1 — Contribute = opportunity engine, not issue browser

On `purpose=contribute`, the system asks one elicitation question:

> What kind of contribution are you looking for?
> (a) Fix a reported issue
> (b) Improve code quality (tests, docs, cleanup)
> (c) Hunt for likely problems
> (d) Show all, ranked

Three scanner lanes (plus a deferred lane D) feed **one ranked Opportunity List**:

| Lane | Source | Approach | Output ranked by |
|---|---|---|---|
| **A. Issue Triage** | PyGithub issues | Approachability scored via the **dependency graph** (blast radius / callers) — not GitHub labels. | Ease × usefulness × maintainer-acceptance odds |
| **B. Quality Scanner** | AST + git history | Deterministic signals only; LLM ranks and explains. Untested hot code (high fan-in ∩ no tests), missing docstrings on public API, dead code, AST duplication, churn × complexity hotspots, TODO/FIXME archaeology via `git blame`. | **Mergeability** — can a junior do it, would a maintainer accept the PR |
| **C. Suspicion Scanner** | Structural facts | Epistemically guarded. Language is restricted to "worth investigating" / "looks fragile because…". Banned vocabulary: "bug", "broken", "will crash". Every suspicion ends with a `to_confirm:` falsification step. Pre-filtered deterministically to top-N. | Strength of structural evidence |
| **D. Feature Suggestions** | Repo's stated intent | **Deferred post-MVP**, except suggestions grounded in the repo's own TODOs, CONTRIBUTING.md, or README "planned features". | n/a (post-MVP) |

All lanes emit the same `Opportunity` model so the ranker can compare them on equal terms.

---

## Iteration 2 — No stat dumps. Output contract, enforced four ways.

**The three laws of output:**

1. **Goal-anchored.** `purpose`, `focus_hint`, and `contribution_intent` are injected into **every** generation prompt. If a section can't tie back to the user's goal, it is cut.
2. **Numbers carry consequences or stay silent.** A metric never appears as a standalone statement. It only appears as the **evidence clause** of an actionable statement. "23 files import this module" is forbidden as a bullet; "this module is a hub — 23 files import it, so a signature change ripples broadly; if you're adding a feature, prefer extending vs. modifying it" is allowed.
3. **Every section ends in motion.** A file to open, a command to run, a next step to take. A section without a next action is incomplete.

**Enforced at four layers** (defense in depth — no single layer is trusted):

| Layer | Mechanism |
|---|---|
| **1. State design** | Raw metrics never reach the Teacher. They are transformed into `Insight` objects with `finding`, `because`, `so_what`, `refs`, `goal_link`. Empty `so_what` or `goal_link` fails Pydantic validation. |
| **2. Prompt contracts** | The three laws are restated in every generation prompt with contrastive ❌/✅ examples. |
| **3. Verifier 2nd rubric** | Beyond grounding, a binary actionability rubric: every claim goal-relevant? every section ends in action? Fail → objections → retry. |
| **4. Eval harness** | Actionability rate ≥80% on the eval set. A regex denylist test asserts raw-metric phrases ("X functions", "Y lines", "Z classes" as standalone statements) never appear in generated tours. |

**Caveat.** The three laws govern **unsolicited** output. Direct user questions about numbers ("how many tests are there?") get direct answers via the Q&A path. The "ask me anything" escape hatch is always available — it surfaces knowledge the laws would otherwise withhold.

---

## Tech stack (free / local only)

| Layer | Choice |
|---|---|
| **LLM judgment** | Groq — `llama-3.3-70b-versatile` (Cartographer, Issue Triage, Teacher, Q&A primary) |
| **LLM tracing** | Groq — `qwen3-32b` (Flow Tracer, Q&A fallback) |
| **LLM cheap** | Groq — `llama-3.1-8b-instant` (Intent Router, Code Health scanner, chunk summaries) |
| **Verifier** | Ollama — `qwen2.5-coder:7b` (local, unlimited — highest call volume agent) |
| **Embeddings** | Ollama — `nomic-embed-text` (local) |
| **LLM provider abstraction** | Custom `LLMProvider` with Groq → Cerebras → Ollama fallback, SQLite response cache, exponential backoff on 429. Agents NEVER import `groq`/`ollama` directly. |
| **Orchestration** | LangGraph — typed `StateGraph`, conditional edges, Postgres checkpointing |
| **Observability** | LangSmith — tracing + evaluation datasets |
| **Code intelligence** | tree-sitter + tree-sitter-python (structural chunking on function/class boundaries), NetworkX dependency graph (call/import/inheritance edges from AST — **parse the graph, never ask an LLM to invent it**), GitPython, PyGithub |
| **Storage** | Postgres + pgvector (chunks, vectors, graph adjacency JSON, LangGraph checkpoints), Redis + arq (background indexing), SQLite (LLM response cache) |
| **Backend** | FastAPI async, sse-starlette (token streaming) |
| **Frontend** | Next.js 15, TypeScript, Tailwind v4, shiki (synchronized code viewer — the key demo moment), mermaid (agent-emitted diagrams), Zustand |
| **Quality** | ruff, mypy `--strict`, pytest + pytest-asyncio + pytest-cov (80% gate), pre-commit, GitHub Actions CI, Docker Compose, gitleaks |

**Groq free-tier survival.** Limits are **per-model**: ≈ 30 RPM / 6k TPM / 1k RPD on the 70B; 8b-instant gets ≈ 14.4k RPD. Quota is deliberately **spread across models** — the Verifier (highest call volume) is local Ollama for that reason, and the Intent Router uses 8B precisely because it fires on every request. Any single agent monopolizing 70B is a bug.

---

## Agent roster

| Agent | Model | Role | Tools |
|---|---|---|---|
| **Intent Router** | llama-3.1-8b-instant | Captures `purpose`. Branches `learn` / `contribute` / `question` from the user's first turn. **First node in every run.** | (none) |
| **Learn Elicitation** | llama-3.1-8b-instant | (Learn branch.) Asks the focus question and captures `focus_hint` ∈ {`overall_structure`, `specific_feature`, `data_model`}. Runs **before** any analysis. | (none) |
| **Contribute Elicitation** | llama-3.1-8b-instant | (Contribute branch.) Asks the 4-way intent question and captures `contribution_intent` ∈ {`fix_issue`, `improve_quality`, `hunt_problems`, `show_all`}. Runs **before** any analysis. | (none) |
| **Cartographer** | llama-3.3-70b-versatile | Builds system map: entry points, hubs, layers — using graph metrics. Reads `purpose` and `focus_hint` from state and tailors the map (e.g., `data_model` → privileges data-shaped hubs). | `graph_query`, `graph_metrics`, `read_chunks` |
| **Flow Tracer** | qwen3-32b | Traces ONE end-to-end flow via graph traversal. | `graph_traverse`, `read_chunks` |
| **Teacher** | llama-3.3-70b-versatile | Sequenced narrative with mermaid diagrams. Reads `Insight` objects, never raw metrics. | `read_chunks` |
| **Issue Triage (Lane A)** | llama-3.3-70b-versatile | Ranks issues by graph-backed approachability. | `github_issues`, `graph_metrics`, `read_chunks` |
| **Code Health (Lane B)** | llama-3.1-8b-instant | Ranks deterministic quality signals by mergeability. | `graph_metrics`, `read_chunks` |
| **Suspicion (Lane C)** | qwen3-32b | Explains pre-filtered structural anomalies with guarded language. | `graph_metrics`, `read_chunks` |
| **Q&A** | llama-3.3-70b-versatile (qwen3-32b fallback) | Hybrid retrieval loop with sufficiency judge, ≤3 hops. | `vector_search`, `graph_traverse`, `read_chunks` |
| **Verifier** | qwen2.5-coder:7b (local Ollama) | Runs on **all** factual output. Per-claim grounding check against `read_chunks` PLUS Iteration-2 actionability rubric. | `read_chunks` |

---

## State schema rules

Pydantic v2. The state is the contract between agents — getting this right is the architectural keystone.

- **No agent writes another agent's field.** Each node returns a partial state; the reducer is field-scoped.
- **Factual claims need non-empty `refs`.** Pydantic validator. A claim with zero refs is a programming error, not a runtime warning.
- **Mutations only via node returns.** Agents do not mutate state in place. The graph applies the diff.
- **`recursion_limit=15`.** Cheaper than discovering infinite loops in production.
- **Reducer on `verifier_objections`.** It's append-only across retries.

The full schema lives in `03_ARCHITECTURE.md`.

---

## Per-PR Definition of Done

Every pull request — feature, fix, or refactor — must satisfy **all** of:

- [ ] `ruff` clean (no warnings, no `# noqa` without a comment explaining why)
- [ ] `mypy --strict` clean on touched packages
- [ ] Tests written. Coverage **did not decrease** vs. main.
- [ ] No secrets, no `print()`, no `console.log` — `structlog` only.
- [ ] Docstrings on all public functions and classes.
- [ ] State mutations only via typed node returns.
- [ ] Every factual output path runs through the Verifier.
- [ ] LangSmith trace reviewed (link in PR description).
- [ ] **Retrieval-touching PRs run the eval harness and post the numbers in the PR description** — before/after, not just after.

Phase prompts assume this is enforced. Do not relax it without explicit user approval.
