# 00 — Claude Build Guide (Standing Context)

> **Paste this file at the top of every build session.** It is the standing context every phase prompt assumes. It does not change between phases; the phase prompt in `05_PHASE_PROMPTS.md` adds the phase-specific goal and deliverables on top of this.

## Documentation layering — read in this order, every phase

There are four documents Claude Code must load before writing a single line of code in any phase. The layering is intentional: each layer constrains what's below it.

| Layer | File | What it carries | Changes between phases? |
|---|---|---|---|
| **1. Project layer** | `CLAUDE.md` (project root) | Project-wide conventions, automated tooling, repo structure, anything Claude Code should obey across all sessions in this project. Loaded automatically by Claude Code; cited explicitly here so the layering is visible. | Rarely. |
| **2. Standing build context** | `docs/00_CLAUDE_BUILD_GUIDE.md` (this file) | Phase-agnostic build rules: principles, tech stack, agent roster, state rules, Per-PR Definition of Done. | No. |
| **3. Design keystone** | `docs/03_ARCHITECTURE.md` | The single source of truth for the architecture: agent topology, state schema, capability library, intent layer, verifier loop, tools. | Only when architecture genuinely changes. |
| **4. Phase gates** | `docs/04_BUILD_PLAN.md` | Per-phase goals, task checklists, production-grade specifics, and the measurable quality gate that must pass before the phase ships. | Per phase ship; the schedule itself is stable. |
| **5. Phase-specific overlay** | the matching block in `docs/05_PHASE_PROMPTS.md` | The phase's paste-ready prompt: TDD tests to write first, implementation order, and a verbatim restatement of the quality gate as the Definition of Done. | Per phase, by definition. |

**Why CLAUDE.md is layer 1.** Claude Code auto-loads it, so it always wins on conflicts. If `CLAUDE.md` says "use uv, not pip" and `docs/00` happens to mention pip, Claude follows `CLAUDE.md`. The cascading rule is: **higher layer wins**. Every phase prompt restates this read order so no session starts cold.

**Why every prompt explicitly cites all four.** Auto-loading is silent. Citing the layers in the prompt makes the chain auditable — when something goes wrong, "which layer did Claude read?" has a clear answer.

---

## Project one-liner

**Codebase Archaeologist** is a web app where a developer pastes a public GitHub repo URL and gets a **purpose-driven, guided onboarding tour** of an unfamiliar codebase, powered by a multi-agent AI system. It serves **any developer with a stated purpose**, working on **Python repositories** on **public GitHub** (≤ 200kLOC). The constraint is in the technology and the intent-elastic capability library — not in who shows up. We do not try to be a general code-search tool, an IDE plugin, or a multi-language platform in v1.

The single distinguishing bet: **before analyzing anything, the system captures pre-context about the user as a free-text intent statement and adapts to it.** There is **no fixed enum of purposes** — no "learn / contribute / build" buttons, no hidden three-bucket system. Pre-context capture is a deliberate, visible, first-class phase consisting of:

1. **Free-text intent capture.** A single open-ended prompt: *"What brings you to this repo?"* Below it, suggestion chips ("understand how this works", "find a first PR", "evaluate for production", "show me where it's fragile", "compare to another library", …) — clickable as pre-fills, never as constraints. The user can type anything.
2. **Intent Profiler** (8B). Reads the free text and emits a structured `IntentProfile`: `modality_weights` (continuous over understand/change/evaluate/locate/compare), `focus_keywords`, `audience_framing`, `output_shape_preference`, and the `raw_text` preserved verbatim.
3. **Confirmation chip strip.** *"I'll focus on X · Y · Z, framed for W. Edit?"* User accepts in one click, or edits a chip, or rewrites the text. The trust handshake before analysis runs.
4. **Capability Planner** (deterministic, no LLM). Reads the confirmed `IntentProfile` and emits a `CapabilityPlan`: which capabilities to activate, in what order, and with what tilts.

The `IntentProfile` is **persisted in state and injected into every generation prompt downstream** — Cartographer, Flow Tracer, Lane A/B/C scanners, Decision Archaeology, Teacher, Q&A. The same repo produces radically different output for a learner who said *"explain the request lifecycle"* than for a security researcher who said *"audit the auth surface"* — and they can both point at the chain back to their stated intent.

Two layers are **universal — they run for every user every time**, regardless of stated intent:

- **Verifier loop.** Wraps every generating capability. Per-claim grounding + actionability rubric. Failed claims become `flagged`, never silently shipped.
- **Q&A subgraph.** Always-on, cross-cutting. Reachable before, during, and after the planned capabilities. Reads the same `IntentProfile`. Drives the synchronized code viewer the same way tour claims do.

### Why intent capture is the first step (not inferred mid-flight)

Existing tools either skip this question (Sourcegraph, GitHub search) or fake it with a generic chat box (Cursor, ChatGPT) and infer purpose from the user's phrasing. We do not. Inferring "this user wants to contribute" from a passing phrase produces a tour that drifts. **A deliberate free-text intent + Profiler + confirmation costs the user ~15 seconds and earns the system the right to be opinionated about what to surface.** Every "why am I being shown this?" reduces to "you said X, the planner derived Y, so we're showing you Z" — and that traceability is itself a trust property.

### Pre-context capture runs IN PARALLEL with indexing — never after it

A naive flow is: paste URL → wait 90s for indexing → answer elicitation → tour. That makes the user stare at a progress bar before they can engage. We do not ship that flow. The correct sequence:

1. User pastes URL → indexing job enqueued immediately (background).
2. **Same screen, no waiting**: free-text intent box appears.
3. **Next screen, while indexing still running**: Intent Profiler runs, the confirmation chip strip renders, the Capability Planner picks the plan.
4. By the time both elicitations are answered (~15–25s of human time), indexing is usually finished. If it isn't, the tour view shows a slim progress bar at the top and starts generating once `repo.status == ready`.
5. **At the 10-second mark** of indexing, an 8B "first impression" paragraph (repo language mix, top hubs, last-commit recency, primary entry point) streams in below the elicitation. This makes the wait productive and demonstrates the system is alive.

Time-to-first-useful-output, not time-to-indexing-complete, is the metric.

### The four trust surfaces — make every moat visible

Every architectural moat we have over competitors must be **visible in the UI**, or the user cannot tell us apart from a fluent chatbot. These four surfaces are non-negotiable:

| Moat | UI surface |
|---|---|
| **Verified grounding** | Every Claim shows a small "✓ grounded" badge when `status == "verified"`. Hover reveals the verifier's confirmation and the chunk it grounded against. Claims with `status == "flagged"` render with a distinct warning treatment — never silently dropped. |
| **Provenance chip (replaces retrieval-path)** | Every Claim shows a typed provenance chip naming where it came from: `vector_then_graph`, `graph_only`, `deterministic_detector(name)`, or `structural_pattern(name)`. Hover reveals the path or the detector signature. The "hybrid retrieval" moat (vector + graph) shows up specifically as the `vector_then_graph` provenance — the chip framing now honestly covers Q&A claims (which retrieve) AND Lane B/C claims (which don't). |
| **Purpose traceability** | A persistent "You said:" chip at the top of the tour shows the captured pre-context. Every Opportunity card carries an "intent match" chip ("matches: hunt problems"). Lane A surfaces a "considered and rejected" trail for the top-3 ranked-down issues so the user sees the triage thinking, not just the verdict. |
| **Action over narrative** | Every section ends in a button or copyable next step. Contribute briefings end with "Open files on GitHub" and "Copy first step" buttons per opportunity — never in prose alone. |

---

## The five principles

These are non-negotiable and govern every prompt, every agent, every UI choice.

1. **Truthful over fluent.** Every factual claim carries a `file:line` reference. When the system doesn't know, it says "not sure" or "I couldn't find that" — it does not invent. Verifier rejection is shown to the user as "flagged", never silently dropped.
2. **Teach, don't dump.** Output is progressive disclosure. No stat dumps. No 600-line summaries. A section ends when the user can take a next action.
3. **Meet the purpose — captured first, applied everywhere.** The `IntentProfile` (free-text + structured tilts) is captured explicitly before any analysis runs, and it is injected into every generation prompt downstream. Two users opening the same repo should see meaningfully different tours, and they can both point at the moment the system "earned" that difference.
4. **Narrow and deep.** Python + Learn mode must be excellent before we widen to other languages or modes. Going broad early is failure.
5. **Earn trust on real repos.** Quality is enforced by an evaluation harness that runs against real-world Python repositories (fastapi, httpx, flask) — not synthetic fixtures.

---

## Iteration 1 — Contribute = opportunity engine, not issue browser

When the Capability Planner activates the contribute-shaped lanes (Lane A and/or B and/or C — typically when `intent_profile.modality_weights.change` is high), the Teacher briefing additionally surfaces one clarifying question if the intent left it underspecified:

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

1. **Goal-anchored.** The full `IntentProfile` (raw_text + modality_weights + focus_keywords + audience_framing + output_shape_preference) is injected into **every** generation prompt as the leading "goal anchor" block. If a section can't tie back to the user's stated intent, it is cut.
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
| **LLM cheap** | Groq — `llama-3.1-8b-instant` (Intent Profiler, Code Health scanner, chunk summaries) |
| **Verifier** | Hugging Face — `Qwen/Qwen2.5-Coder-7B-Instruct` (local, unlimited — highest call volume agent) |
| **Embeddings** | Hugging Face — `nomic-ai/nomic-embed-text-v1.5` (local) |
| **LLM provider abstraction** | Custom `LLMProvider` with Groq → Cerebras → Hugging Face fallback, SQLite response cache, exponential backoff on 429. Agents NEVER import provider SDKs directly. |
| **Orchestration** | LangGraph — typed `StateGraph`, conditional edges, Postgres checkpointing |
| **Observability** | LangSmith — tracing + evaluation datasets |
| **Code intelligence** | tree-sitter + tree-sitter-python (structural chunking on function/class boundaries), NetworkX dependency graph (call/import/inheritance edges from AST — **parse the graph, never ask an LLM to invent it**), GitPython, PyGithub |
| **Storage** | Postgres + pgvector (chunks, vectors, graph adjacency JSON, LangGraph checkpoints), Redis + arq (background indexing), SQLite (LLM response cache) |
| **Backend** | FastAPI async, sse-starlette (token streaming) |
| **Frontend** | Next.js 15, TypeScript, Tailwind v4, shiki (synchronized code viewer — the key demo moment), mermaid (agent-emitted diagrams), Zustand |
| **Quality** | ruff, mypy `--strict`, pytest + pytest-asyncio + pytest-cov (80% gate), pre-commit, GitHub Actions CI, Docker Compose, gitleaks |

**Groq free-tier survival.** Limits are **per-model**: ≈ 30 RPM / 6k TPM / 1k RPD on the 70B; 8b-instant gets ≈ 14.4k RPD. Quota is deliberately **spread across models** — the Verifier (highest call volume) is local Hugging Face for that reason, and the Intent Profiler uses 8B precisely because it fires on every request. Any single agent monopolizing 70B is a bug.

---

## Agent roster

| Agent | Model | Role | Tools |
|---|---|---|---|
| **Intent Profiler** | llama-3.1-8b-instant | **Generic intent layer, step 1.** Reads the user's free-text intent. Emits `IntentProfile` (modality_weights, focus_keywords, audience_framing, output_shape_preference, raw_text). **First node in every run. Universal.** | (none) |
| **Capability Planner** | deterministic (no LLM) | **Generic intent layer, step 2.** Maps `IntentProfile → CapabilityPlan`. Picks which capabilities to activate and how to tilt them. Verifiable in CI. Universal. | (none) |
| **Cartographer** | llama-3.3-70b-versatile | (Optional, planner-activated.) Builds system map: entry points, hubs, layers. Hub-selection bias and subsystem narrowing come from `capability_plan` + `intent_profile.focus_keywords`. | `graph_query`, `graph_metrics`, `read_chunks` |
| **Flow Tracer** | qwen3-32b | (Optional, planner-activated.) Traces one or more end-to-end flows via graph traversal. | `graph_traverse`, `read_chunks` |
| **Teacher** | llama-3.3-70b-versatile | (Terminal, almost always activated.) Sequences whichever capabilities ran into output. Output shape (`narrative` / `ranked_list` / `dossier` / `comparison_table`) and audience framing from `intent_profile`. Lead paragraph echoes the user's `raw_text`. | `read_chunks` |
| **Lane A — Issue Triage** | llama-3.3-70b-versatile | (Optional, planner-activated.) Ranks issues by graph-backed approachability. Filterable by `focus_keywords`. | `github_issues`, `graph_metrics`, `read_chunks` |
| **Lane B — Code Health** | llama-3.1-8b-instant | (Optional, planner-activated.) Ranks deterministic quality signals. Teacher framing (cleanup vs. tradeoffs-visible) from `capability_plan.lane_b_framing`. | `graph_metrics`, `read_chunks` |
| **Lane C — Suspicion** | qwen3-32b | (Optional, planner-activated.) Explains pre-filtered structural anomalies with guarded language. Detector subset filterable by `focus_keywords`. | `graph_metrics`, `read_chunks` |
| **Decision Archaeology** | llama-3.3-70b-versatile | (Optional, planner-activated.) Extracts architectural decisions + rationale from `git log` + README + commit messages + import graph. Activated for evaluate-heavy or build-vs-buy-shaped intents. | `graph_query`, `graph_metrics`, `read_chunks`, GitPython |
| **Q&A** | llama-3.3-70b-versatile (qwen3-32b fallback) | Hybrid retrieval loop with sufficiency judge, ≤3 hops. | `vector_search`, `graph_traverse`, `read_chunks` |
| **Verifier** | qwen/qwen3-32b (Groq) → HF fallback | Runs on **all** factual output. Per-claim grounding check against `read_chunks` PLUS Iteration-2 actionability rubric. | `read_chunks` |

---

## State schema rules

Pydantic v2. The state is the contract between agents — getting this right is the architectural keystone.

- **No agent writes another agent's field.** Each node returns a partial state; the reducer is field-scoped.
- **Factual claims need non-empty `refs`.** Pydantic validator. A claim with zero refs is a programming error, not a runtime warning.
- **Mutations only via node returns.** Agents do not mutate state in place. The graph applies the diff.
- **`recursion_limit=15`.** Cheaper than discovering infinite loops in production.
- **Reducer on `verifier_objections`.** It's append-only across retries.
- **The generic intent layer completes before any capability runs.** Every capability node guards on `state.intent_profile is not None` and `state.capability_plan is not None` and raises if either is missing. Q&A is exempt only when the user asks before any planned capability has run — Q&A then synthesizes a minimal `IntentProfile` from the question itself.
- **No code path branches on a "purpose" enum.** If you find yourself writing `if state.purpose == "learn":` you have reintroduced the bucketed model and broken the elasticity property. Capability behavior is parameterized by `intent_profile` + the capability's tilt entry in `capability_plan` — nothing else.

The full schema lives in `03_ARCHITECTURE.md`.

---

## Per-PR Definition of Done

Every pull request — feature, fix, or refactor — must satisfy **all** of:

- [ ] **Documentation layering respected.** `CLAUDE.md` rules followed; `docs/00`, `docs/03`, and `docs/04` not contradicted. If the PR genuinely needs to change a higher layer, it updates that layer first, in a separate commit, with explicit justification in the PR description.
- [ ] `ruff` clean (no warnings, no `# noqa` without a comment explaining why)
- [ ] `mypy --strict` clean on touched packages
- [ ] Tests written. Coverage **did not decrease** vs. main.
- [ ] No secrets, no `print()`, no `console.log` — `structlog` only.
- [ ] Docstrings on all public functions and classes.
- [ ] State mutations only via typed node returns.
- [ ] Every factual output path runs through the Verifier.
- [ ] LangSmith trace reviewed (link in PR description).
- [ ] **Retrieval-touching PRs run the SAMPLED eval harness and post the numbers in the PR description** — before/after, not just after. Full matrix runs on `main` post-merge.

Phase prompts assume this is enforced. Do not relax it without explicit user approval.
