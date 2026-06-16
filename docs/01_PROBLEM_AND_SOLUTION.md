# 01 — Problem and Solution

## The problem

Opening an unfamiliar Python repository for the first time is an exercise in disorientation. The README explains *what* the project does at a marketing altitude. The file tree shows the shape but not the flow. The tests, if they exist, exercise behavior but rarely narrate it. A junior developer or first-time open-source contributor is left with a question that no single artifact in the repo answers: **"where do I look first, and why?"**

The shape of the pain is concrete:

- **The reading order is invisible.** A 50,000-line codebase has perhaps five files that anchor the mental model. Nothing tells you which five.
- **Issue trackers are not onboarding ramps.** Labels like `good first issue` are inconsistent across maintainers, often stale, and frequently mislabeled. An issue's true approachability depends on how isolated the affected code is — a fact the label cannot encode.
- **General LLM chat is fluent but fragile.** Asked "explain this repo," ChatGPT or Cursor will produce a plausible summary that confidently mixes real structure with invented modules. A junior developer cannot tell which sentences to trust.
- **Existing onboarding tools assume context you don't yet have.** Sourcegraph and GitHub code search reward someone who knows the symbol they're looking for. The whole point of onboarding is that you don't.

### Why existing tools fail this user

| Tool | What it's good at | Why it fails first-time contributors |
|---|---|---|
| **GitHub code search** | Finding a known symbol in a known repo. | You don't know the symbol yet. No purpose-awareness. No mental-model construction. |
| **Sourcegraph / OpenGrok** | Cross-repo navigation for engineers already fluent in the codebase. | Assumes you can navigate. Doesn't tell you what *matters*. Surface for symbols, not for stories. |
| **ChatGPT / Claude.ai chat with a repo URL** | Fluent natural-language answers about the repo's stated purpose. | Hallucinates structure. No citations to file:line. Cannot ground claims in the actual AST. No multi-step retrieval. |
| **Cursor / Copilot Chat in-IDE** | Helping you edit code you've already opened. | Assumes you already know which file to open. No onboarding narrative. No purpose elicitation. |
| **CodeSee, Sourcetrail, Sourcegraph Cody** | Visualizing call graphs and dependencies. | Output is a picture, not a path. A graph does not tell you which node to start at, and why this node, today, for *you*. |
| **CONTRIBUTING.md** (when present) | The maintainer's intended onboarding. | Written once, decays. Generic. Doesn't adapt to whether you came to learn or to ship a PR. |

### Who this is for

Anyone who has opened an unfamiliar **public Python** repository and can finish the sentence: *"I'm here because…"*. The product is purpose-driven, not role-driven — and **the purpose is whatever you say it is**, not a button you pick from a list of three.

The system supports any goal you can state in a sentence. As an indicative (not exhaustive) sample of what people show up with:

- *"I'm onboarding to this codebase at work; help me get oriented."*
- *"I want to understand how this library's async machinery works."*
- *"I'm looking for a realistic first PR I could open this weekend."*
- *"Show me where this codebase is fragile — I'd open issues, not PRs."*
- *"I'm evaluating this for our production stack; what would surprise us?"*
- *"I'm building a competitor; what design decisions did they lock themselves into?"*
- *"I'm a security researcher; show me the auth / permission surface."*
- *"I need to write internal docs on how this library handles X."*
- *"Compare how this project does pagination to how `[other library]` does it."*
- *"I'm prepping for a system-design interview that references this codebase."*
- *"I'm debugging why this dependency broke in our prod last week."*

These are not nine separate "modes" with nine different pipelines. They are nine different stated intents that the system parses, profiles, and translates into a **plan over a shared capability library** (Cartographer, Flow Tracer, Teacher, scanner lanes A/B/C, Decision Archaeology, Q&A, all described in `docs/03`). The capabilities are fixed; the plan is per-intent.

We do not gate by seniority, role, or affiliation. The constraint is in the *technology* (Python, public GitHub, ≤ 200kLOC) — not in who shows up or what they want.

Out of scope until the above is excellent: non-Python languages, private repos, "explain my own code" (the user already knows it), team-mode multi-user tours.

---

## The solution

A multi-agent web app that, given a public Python GitHub URL, produces a **purpose-driven guided tour** in which every factual claim is grounded in a `file:line` reference and every section ends with a next step the user can actually take.

### Key features (at a glance)

These are the features the rest of the doc set elaborates on. Each one is what makes any stated intent — *"onboard me to this codebase,"* *"find me a first PR,"* *"audit the auth surface,"* *"compare to library X"* — land on something usable instead of generic prose.

| # | Feature | What it gives the user | Where it's specified |
|---|---|---|---|
| 1 | **Free-text intent capture** | A single open-ended prompt: "What brings you to this repo?" No forced choice from a fixed list. Suggested example chips exist to unblock, not to constrain. | docs/00, docs/03 |
| 2 | **Intent Profiler** | An 8B model that reads the free text and extracts a structured `IntentProfile` (modality weights, focus keywords, audience framing, output-shape preference) — preserving the raw sentence too. Confirmable in one click before analysis runs. | docs/03 (Intent Profiler) |
| 3 | **Capability Planner** | Deterministic. Reads the `IntentProfile` and picks a subset of the shared capability library to invoke, with per-capability tilt parameters. Adding a new stated intent does not require code changes; the planner re-plans. | docs/03 (Capability Planner) |
| 4 | **Shared capability library** | Eight independently-testable building blocks: Cartographer, Flow Tracer, Teacher, Lane A (Issue Triage), Lane B (Code Health), Lane C (Suspicion), Decision Archaeology, Q&A. Composed per-intent. Extending the library = adding a ninth block + a planner heuristic, not restructuring the pipeline. | docs/03 (Capability library) |
| 5 | **Parallel-with-indexing flow** | The intent capture + Intent Profiler run **while** indexing happens in the background. A "first impression" paragraph streams in at ~10s. You never stare at a dead progress bar. | docs/00, docs/04 (Phase 4) |
| 6 | **Verified grounding with visible badges** | Every factual claim is checked by a *separate* model against the actual source chunk. Verified claims wear a `✓ grounded` badge; failed ones render as `flagged` and never as fact. The trust floor is universal across every plan the planner produces. | docs/03 (Verifier loop) |
| 7 | **Hybrid retrieval (vector + graph)** | Vector search finds candidate code; the dependency graph traverses callers/callees to *complete the context*. Every claim shows its retrieval path on hover (`vector_search → graph_traverse · 2 hops`). | docs/03 (Hybrid retrieval) |
| 8 | **Epistemically guarded suspicion language** | Lane C never says "bug" or "broken". It says "worth investigating because…" and every suspicion ends with a `to_confirm:` falsification step you can run yourself. | docs/03 (Lane C) |
| 9 | **Actionability contract (no stat dumps)** | Numbers only appear as evidence for actionable statements; every section ends in motion (a file to open, a command to run, a button to click). Enforced at four layers — state, prompt, verifier, eval. Universal across all output shapes. | docs/00, docs/03 (Iteration 2) |
| 10 | **Synchronized code viewer** | Click a claim → the right-hand viewer scrolls to the exact lines. Q&A answers drive the viewer too. Clicking a decision in Decision-Archaeology output opens both the source lines and the originating commit. | docs/04 (Phase 4) |
| 11 | **Q&A escape hatch, intent-aware** | At any point, ask anything. Answers are grounded with refs and framed through your captured `IntentProfile` — so "what does this function do?" gets a different framing depending on whether you said you're onboarding, contributing, evaluating, or auditing. | docs/03 (Q&A subgraph) |
| 12 | **Trust surfaces** | "You said:" chip at the top of every tour (the raw intent + the parsed profile). Verified-grounded badges. Retrieval-path chips. Intent-match chips on every card. Considered-and-rejected trails when scanner lanes are active. You can always point at *why* the system is showing you this. | docs/00, docs/03 (Trust surfaces) |
| 13 | **CTA-ended briefings** | When the output shape is `ranked_list` or `dossier`, every card ends in buttons appropriate to the audience framing: "Open files on GitHub", "Copy first step", "Copy probe script", "Open commit", "Copy comparison snippet". The product never trails off in prose. | docs/04 (Phase 4/5) |
| 14 | **Free-tier survivable** | Whole stack runs on Groq free tier + local Hugging Face + Docker Compose. No paid APIs anywhere on the critical path. | docs/02 |

### How the flow handles "hard-to-context-map" responses

The hardest questions in an unfamiliar codebase are the ones that **don't have an answer at one location** — you can't just open one file and read it. Examples:

- *"What happens when a request comes in?"* — touches routing, middleware, the handler, the response serializer.
- *"Is this function safe to change?"* — depends on every caller, all the way up.
- *"Where should I add this feature?"* — requires knowing the layer decomposition and the conventions.
- *"Why does this codebase do X this way?"* — needs structural reasoning, not a single chunk.

These are exactly the questions a generic chatbot fakes an answer to. Our flow turns them into traceable, grounded answers via three composing properties:

1. **Pre-context narrows the search space.** The same question gets answered differently depending on the captured `(purpose, lens)`:
   - A **learner** asking *"is this safe to change?"* gets: the function's behavior + where it sits in the system map + which layer's invariants it participates in.
   - A **contributor** with `hunt_problems` intent gets: the function's behavior + **blast radius** (graph fan-in, hub status, has-nearby-tests) + a `to_confirm:` step.
   - A **builder** with `architecture_tradeoffs` lens gets: the function's behavior + which architectural decision it embodies + the git history of that decision + whether changing it would shift the design.

   Same retrieval, three different framings. The framing is what makes the answer useful for *your* job.
2. **Hybrid retrieval composes context that vector search alone misses.** Vector search finds the function. The graph then walks its callers, callees, and inheritance chain. The Q&A judge expands up to 3 hops until it has enough to answer. This is why *"is this safe to change?"* gets a real answer — the model doesn't just see the function, it sees who depends on it.
3. **Verification refuses to fake it.** If the Verifier can't ground a claim, it's `flagged`, never shipped as fact. *"I couldn't find that in the repo"* is a valid, first-class answer. This is the property that lets you trust the flow at all, regardless of which purpose brought you here.

The promise: when you ask a question that's hard to map to one location, you get an answer that *traces the hops it took*, *cites the lines*, and *frames the response to what you said you're here for*. You can read the answer or you can pop open the retrieval-path chip and verify the reasoning yourself.

### Four concrete walkthroughs (out of infinitely many possible)

Four end-to-end traces showing what different stated intents produce. The first three rhyme with the "learn / contribute / build" trio above so the connection is clear; the fourth deliberately steps outside any such trio — a security researcher with a domain-specific lens — to prove the design is genuinely open-ended, not a hidden three-bucket system. Every walkthrough below is ~30 seconds of human attention end-to-end.

---

#### Walkthrough A — Learner ramping on Django's request lifecycle

**Step 0 — Paste.** `https://github.com/django/django`. Indexing in the background.

**Step 1 — Intent statement.** User types: *"I'm onboarding to this codebase at work — help me understand how a request becomes a response."* Intent Profiler extracts: `modality_weights = {understand: 0.9, locate: 0.1}`, `focus_keywords = ["request", "response", "lifecycle"]`, `audience_framing = "for internal ramp-up"`, `output_shape_preference = "narrative"`. Confirmation chip strip: *"I'll trace the request lifecycle and narrate it. Edit?"* User clicks accept.

**Step 2 — First impression (≈10s).** *"Django is a 250k-LOC web framework (capped at 200k for v1 — switching to the smaller `flask` for the demo). The hot core is `django/core/handlers/` for request dispatch and `django/db/models/` for the ORM. ~91% test coverage."*

**Step 3 — Cartographer (tilted to feature lens).** Surfaces the layered structure that matters for a request: URL resolver → middleware chain → view → response. Skips peripheral layers (admin, management commands).

**Step 4 — Flow Tracer.** Picks the canonical path: `WSGIHandler.__call__` → `BaseHandler.get_response` → middleware iteration → URL resolution → view invocation → response post-processing. Six steps, each with file:line refs.

**Step 5 — Teacher narrative (streams).**
> You asked how a request becomes a response. Django's answer is a six-stage pipeline.
> **1. The WSGI entry point** (`django/core/handlers/wsgi.py:115`) wraps the raw WSGI environ into a `WSGIRequest`. ✓ grounded
> **2. `BaseHandler.get_response`** (`django/core/handlers/base.py:64`) is the orchestrator. It walks the middleware chain on the way in, calls the view, then walks it on the way out. ✓ grounded
> *(continues with mermaid diagram of the pipeline)*
> **Next step:** open `django/core/handlers/base.py` and follow `_get_response`. Or ask: *"what does a middleware actually look like?"*

**Step 6 — Drill in via Q&A.** User asks: *"What does a middleware actually look like?"* The hybrid retrieval finds the protocol class, `graph_traverse` walks an example (CSRF middleware), the viewer opens both side by side. Answer streams with refs.

**What the learner walks away with.** A mental model of Django's request lifecycle they can talk about in an interview. Six pinned files. No memorization required — they can come back any time and ask Q&A another question.

---

#### Walkthrough B — Contributor finding a real fix in httpx

**Step 0 — Paste.** `https://github.com/encode/httpx`. Indexing in background.

**Step 1 — Intent statement.** User types: *"Show me where this codebase might be fragile — I'd open issues, not PRs, but I want each finding to be falsifiable so I don't waste a maintainer's time."* Intent Profiler extracts: `modality_weights = {change: 0.5, evaluate: 0.5}`, `focus_keywords = ["fragility", "edge cases"]`, `audience_framing = "for a respectful issue report"`, `output_shape_preference = "ranked_list"`. Confirmation: *"I'll run suspicion + quality scans with guarded language, each ending in a check you can run. Edit?"* Accept.

**Step 2 — First impression (≈10s).** *"httpx is a 47k-LOC async HTTP client. Entry point `httpx.Client`; hot core in `_transports/`. ~88% test coverage. Active — last commit yesterday."*

**Step 3 — Scanners run in parallel (≈30s).** Lane A pulls open issues + scores by graph-backed approachability. Lane B runs deterministic quality detectors. Lane C pre-filters structural anomalies → guarded-language explanations.

**Step 4 — Ranker (deterministic).** Weighted by `hunt_problems` → Lane C heaviest, but B and A still surface their strongest items.

**Step 5 — Briefing (streams to UI).** Top 5 opportunity cards. The top one:

> **`_transports/default.py:142` — `HTTPTransport.handle_request` catches `httpx.ConnectError` without a logger call.**
> Matches: hunt problems · Difficulty: S · Blast radius: isolated
>
> **Why this matters:** the swallow-except hides connection-level failures from observability; a maintainer adding logging is a clean, accepted-by-default kind of PR.
> **Worth investigating because:** all other `except` branches in this file call `logger.warning(...)`; this one breaks the convention.
> **To confirm before opening a PR:** grep for other `except httpx.ConnectError` in the codebase — if the convention is intentional silence, this is a no-op; otherwise, add a `logger.warning(...)` and a regression test in `tests/_transports/test_default.py`.
>
> **Files to touch:** `httpx/_transports/default.py:142`
> **Nearest tests:** `tests/_transports/test_default.py`
> **[ Open files on GitHub ]   [ Copy first step ]**

Below the top-5: a **"Considered and rejected"** trail — *"#2890 — touches `_client.py:Client.send` (fan-in 41, central hub) — too hot for a first PR."*

**Step 6 — Audit the reasoning.** Every claim has a `✓ grounded` badge with the verifier note + chunk on hover, and a `vector_search → graph_traverse · 1 hop` retrieval-path chip. Audit the system before trusting it.

**Step 7 — Drill in via Q&A.** *"Why does this file log everything else but not ConnectError?"* → Q&A traces git blame: the branch was added in PR #1987 with no logging mentioned — likely an oversight.

**Step 8 — Act.** Click **Open files on GitHub** → file opens at line 142. Click **Copy first step** → clipboard has the grep. Run it, write the fix, open the PR.

**The hard-to-context-map property:** at no point did the contributor have to know *"is this a real bug or intentional silence?"* before opening files. The system mapped that question to the right graph traversal, the right `git blame`, and the right framing for their `hunt_problems` intent — and handed them a falsifiable next step instead of a confident assertion.

---

#### Walkthrough C — Builder evaluating FastAPI to ship a competitor

**Step 0 — Paste.** `https://github.com/tiangolo/fastapi`. Indexing in background.

**Step 1 — Intent statement.** User types: *"I'm planning a competitor to this framework — what architectural choices did they lock themselves into, and where are the differentiation opportunities?"* Intent Profiler extracts: `modality_weights = {evaluate: 0.8, understand: 0.2}`, `focus_keywords = ["architecture", "dependencies", "extensibility"]`, `audience_framing = "for a build-vs-buy memo"`, `output_shape_preference = "dossier"`. Confirmation: *"I'll archaeology the design decisions and surface tradeoffs + differentiation. Edit?"* Accept.

**Step 2 — First impression (≈10s).** *"FastAPI is a 30k-LOC async web framework built on Starlette and Pydantic. Pure Python, async-first, heavy use of type hints for dependency injection. ~95% test coverage. Strong velocity — 200+ contributors in the last year."*

**Step 3 — Build pipeline in parallel.**
- **Cartographer (tilted to tradeoffs).** Privileges decision-shaped hubs: the dependency injection module (`fastapi/dependencies/`), the routing model (`fastapi/routing.py`), the OpenAPI generation pipeline (`fastapi/openapi/`).
- **Decision Archaeology.** Reads `git log` for the top hubs + README + commit messages + ADRs (none present, noted). Extracts: *"Starlette chosen as base in initial commit `a52cc4e` (Dec 2018)"*, *"Pydantic v1 → v2 migration spread across 2023, see PR #9434"*, *"Dependency injection via type hints introduced in `0c7d6c1`, retained throughout."*
- **Lane B framed as tradeoffs.** Runs the same deterministic quality scanners but the Teacher reframes them: *"high churn × complexity in `fastapi/dependencies/utils.py` — this is where the type-hint-as-DI design has paid ongoing cost."*

**Step 4 — Teacher briefing — the "decision dossier" (streams to UI).** Sections:

> **What FastAPI inherited.** Built on Starlette (ASGI) + Pydantic (validation). Both are first-class dependencies, not soft. Implication for your competitor: matching async ergonomics likely means picking comparable layers, not reinventing.
> ✓ grounded (`fastapi/applications.py:14-22`, commit `a52cc4e`)
>
> **The pivotal architecture decision: DI via type hints.** Function parameter type hints double as dependency declarations. Powerful but ties API design to runtime introspection. Tradeoff: ergonomic for users, friction for the framework itself — visible as the high-churn `dependencies/utils.py` (32 commits last year, cyclomatic complexity p95).
> ✓ grounded (`fastapi/dependencies/utils.py`, churn signal Lane B)
>
> **Friction points in their design** (where you could differentiate).
> - The Pydantic v1→v2 migration left compat shims in 4 files. A from-scratch competitor could pick v2 cleanly.
> - OpenAPI generation is tightly coupled to routing — `fastapi/openapi/utils.py` imports from `routing.py` and vice versa. A decoupled design would be easier to swap.
> - No first-class background task queue — they hand off to Starlette's basic one and recommend Celery in docs.
> ✓ grounded per claim
>
> **Differentiation opportunities your team should consider.**
> 1. First-class background tasks (their stated gap, README links out to Celery).
> 2. Decoupled OpenAPI generation that doesn't import routing internals.
> 3. Pydantic v2-only design, no v1 compat surface.

**Step 5 — Drill in via Q&A.** *"Why did they couple OpenAPI to routing this way?"* → Q&A traces git history of `openapi/utils.py`, finds the original design discussion in PR #234's description, surfaces the rationale: *"the OpenAPI schema needs to know the dependency tree to render correctly, and the routing module owns that tree."* Now the builder understands not just *what* but *why* — and can decide whether to accept the same constraint.

**What the builder walks away with.** A one-page decision dossier with line-and-commit-cited evidence for every claim. Concrete differentiation opportunities. The kind of artifact you could paste into a build-vs.-buy doc, a competitive-positioning memo, or an engineering team kickoff.

---

#### Walkthrough D — Security researcher auditing Flask's session handling

This one deliberately sits outside any "learn / contribute / build" trio. It is a worked example proving the design is not a hidden three-bucket system.

**Step 0 — Paste.** `https://github.com/pallets/flask`. Indexing in background.

**Step 1 — Intent statement.** User types: *"I'm a security researcher; show me Flask's session handling surface — where sessions are minted, signed, verified, and where any of that could go wrong. Frame findings for a responsible disclosure."* Intent Profiler extracts: `modality_weights = {locate: 0.5, evaluate: 0.4, change: 0.1}`, `focus_keywords = ["sessions", "signing", "cookies", "secret_key", "csrf"]`, `audience_framing = "for a responsible disclosure"`, `output_shape_preference = "dossier"`. Confirmation chip strip: *"I'll map the session surface, trace the sign/verify path, flag suspicion-shaped patterns in that surface only, and frame for a security report. Edit?"* Accept.

**Step 2 — First impression (≈10s).** *"Flask is a 25k-LOC web micro-framework. Session handling lives in `flask/sessions.py` (470 LOC); cookie signing uses `itsdangerous`. Session config flags live in `flask/app.py:Flask.config`. The `secret_key` is the root of trust for the default `SecureCookieSession`."*

**Step 3 — Capability Planner picks a custom mix.** Based on the profile:
- **Cartographer** narrowed to `sessions` + `signing` + `cookies` keywords → returns the session class hierarchy, the cookie-set/read entry points, and the secret-key consumption sites.
- **Flow Tracer** runs *twice* — once on the "session mint" path (request without cookie → session created → set-cookie header), once on the "session verify" path (request with cookie → cookie parsed → signature verified → session loaded).
- **Lane C (Suspicion)** runs but is filtered to only the files Cartographer marked as in-surface (`sessions.py`, `app.py`, and their direct callers). Detectors include: timing-comparison patterns, missing `compare_digest` use, fallback paths on signature failure, `secret_key` source-of-truth checks.
- **Lane A and Decision Archaeology** are *not* activated — the user didn't ask for issues or rationale.
- **Teacher** runs with `audience_framing = "responsible disclosure"` prompt — measured language, full repro steps, no hyperbole, every finding ending with the exact lines and the version where the behavior was introduced.

**Step 4 — Dossier streams.**
> **Session surface.** Flask sessions are minted in `flask/sessions.py:SecureCookieSessionInterface.save_session` (lines 220–248), verified in `open_session` (lines 192–217). The cryptographic floor is `itsdangerous.URLSafeTimedSerializer`, instantiated with `app.secret_key`.
> ✓ grounded
>
> **Worth investigating: secret-key fallback behavior.** When `app.secret_key` is unset and `app.testing` is True, sessions fall back to a fixed string (`flask/app.py:298`). The fallback is gated, but if a test config leaks into a production deploy, sessions become forgeable. **To confirm before reporting:** check whether `app.testing` can be set via environment variable; if so, this is reportable; if not, it's a defense-in-depth note.
> ✓ grounded · ⚠ suspicion-flagged · `to_confirm:` provided
>
> **Worth investigating: signature failure path.** `open_session` catches `BadSignature` and returns a fresh empty session (lines 209–211) rather than raising. This is correct UX behavior but means an attacker probing for valid signatures gets no observable feedback. **To confirm:** check whether timing of the catch-and-return is constant relative to the catch-and-return path for a session that simply doesn't exist; if there's a measurable delta, that's a timing oracle.
> ✓ grounded · ⚠ suspicion-flagged · `to_confirm:` provided

The dossier ends with: *"I did not run dynamic checks. The two `to_confirm:` items are the actions you'd run before sending a disclosure email — both are short scripts you can copy from the buttons below."* Two CTA buttons: **Copy environment-variable probe** and **Copy timing-oracle probe**.

**What the security researcher walks away with.** A scoped audit dossier framed for disclosure, with falsifiable items rather than confident-sounding accusations — exactly the format a responsible reporter would want to send a maintainer.

---

### What these four have in common — and why it matters

Each walkthrough above is the same architecture (typed state, hybrid retrieval, verifier loop, four-layer enforcement) producing radically different output because **the Intent Profiler captures a free-text intent, the Capability Planner picks a subset of the capability library, and every active capability reads the profile**. The learner gets a narrative. The contributor gets a ranked list with CTAs. The builder gets a decision dossier with git history. The security researcher gets a scoped audit framed for disclosure. None of these are persona-specific code paths; they are different *plans over a shared capability library*, with a shared trust spine (verifier + grounded badges + retrieval-path chips + actionability contract) running underneath each one.

The "hard-to-context-map" property is the headline benefit, and it applies regardless of what intent you state. The questions hardest to answer in the abstract — *"how does this thing work end to end?"*, *"is this safe to change?"*, *"why did they make this choice?"*, *"where could this go wrong?"* — get answered with retrieval that traces multiple hops, citations to specific lines and commits, framing matched to your stated goal, and a verifier that refuses to fake an answer. Generic LLM chatbots cannot do this because they have no graph and no verifier; tools with graphs (Sourcegraph, CodeSee) cannot do this because they have no intent profiling and no narrative. We do it by composing all three over an open-ended capability library that any future stated intent can recombine.

### Fine-grained mapping: example stated intents → what the Capability Planner picks

This is not a closed taxonomy. It is a worked sample showing how the Capability Planner translates a free-text intent into a plan over the capability library. Read it as "here are 12 plausible things a user might say, and here is the plan each one produces" — not "here are the 12 supported modes."

| Stated intent (sample) | Active capabilities | Tilts / framing | Output shape |
|---|---|---|---|
| *"Help me onboard at work — explain how a request becomes a response."* | Cartographer, Flow Tracer, Teacher, Q&A | focus = request lifecycle; audience = ramp-up; narrative voice | `narrative` |
| *"I want to understand this library's async machinery."* | Cartographer, Flow Tracer, Teacher, Q&A | focus = async/await/event loop; Cartographer narrows to coroutine-heavy modules | `narrative` |
| *"Find me a realistic first PR."* | Lane A, Lane B (med), Teacher briefing, Q&A | weights favor mergeable issues; considered-and-rejected trail surfaced | `ranked_list` with CTAs |
| *"Show me where this codebase is fragile — issues, not PRs."* | Lane C (heavy), Lane B (med), Teacher, Q&A | guarded language; every finding ends in `to_confirm:`; framing for issue reports | `ranked_list` with CTAs |
| *"Improve doc coverage — what's missing docstrings?"* | Lane B (heavy, filtered to docstring detector), Teacher, Q&A | Lane A/C skipped; surface only public-API misses | `ranked_list` with CTAs |
| *"Evaluate this for our production stack — what would surprise us?"* | Cartographer (balanced), Lane B (perf detectors), Decision Archaeology (rationale), Teacher | framing = ops-readiness; surface tech debt + perf-shaped patterns + known limitations | `dossier` |
| *"I'm building a competitor — design decisions and differentiation."* | Cartographer (decision hubs), Decision Archaeology (heavy), Lane B (as tradeoffs), Teacher | framing = build-vs-buy memo; emphasize friction (high churn × complexity) | `dossier` |
| *"Security audit of the session-handling surface."* | Cartographer (narrowed to session keywords), Flow Tracer (mint + verify paths), Lane C (filtered to suspicion in surface only), Teacher | framing = responsible disclosure; constant-time-comparison detectors | `dossier` |
| *"Document this library for our internal wiki — focus on the public API."* | Cartographer (public symbols only), Flow Tracer (across each top-level entry), Teacher | framing = neutral documentation prose; one section per public surface | `narrative` |
| *"Compare this project's pagination to `[other-repo]`'s."* | Cartographer (narrowed to pagination call sites), Flow Tracer (pagination read paths), Decision Archaeology (rationale), Teacher | framing = side-by-side; output references both repos when available | `comparison_table` |
| *"Why did this dependency break in our prod last week?"* | Q&A only (deep mode, 3 hops max), Cartographer (only if Q&A needs map context) | tour suppressed; conversational mode; viewer follows answers | `narrative` (Q&A-shaped) |
| *"I'm prepping for an interview that uses this codebase."* | Cartographer (overall + a "likely-to-be-asked" flow), Teacher, Q&A | framing = study guide; ends with self-test questions | `narrative` |

The principle, in one line: **there are no per-persona code paths. There is a library of capabilities and a planner that picks from it based on what you said.** The same machinery powers every row in the table above and every row not in it. The proof is the phase-gate tests:

- `test_intent_profiler_extracts_correctly` (Phase 3) — on a labeled set of stated intents, the profiler produces the expected `modality_weights`, `focus_keywords`, `audience_framing`, `output_shape_preference`.
- `test_planner_picks_correct_capabilities` (Phase 3) — given a profile, the planner activates the right capability subset (e.g., "audit auth surface" must activate Lane C with focus_keyword filtering, must skip Lane A unless asked).
- `test_pre_context_shapes_output` (Phase 3) — running two different stated intents on the same repo produces materially different outputs (≥ 50% delta on a structural-similarity metric).
- `test_capability_library_independence` (Phase 3) — every capability is invocable standalone with a synthetic profile, without the rest of the pipeline. The library is composable, not entangled.

Without those tests passing, "purpose-elastic architecture" is a claim, not a property.

### The core bet

Before doing any analysis, the system **captures pre-context about the user** — but as a free-text *intent statement*, not a forced choice from a list. The flow:

1. **A single open-ended prompt: "What brings you to this repo?"** A text box. Below it, 4–6 example chips ("understand how this works", "find a first PR", "evaluate for production", "show me where it's fragile", "compare to another library", …) — click one to pre-fill, or just type your own. The chips exist to *unblock* the user, not to constrain them.
2. **An Intent Profiler agent** (8B model) reads the free text and extracts a structured `IntentProfile`:
   - `modality_weights`: continuous weights on `understand / change / evaluate / locate / compare` — not a hard category. *"I'm looking for a first PR and trying to understand the testing conventions"* lands at `change: 0.7, understand: 0.3`.
   - `focus_keywords`: extracted topics (`auth`, `async`, `ORM`, `pagination`, `performance`, `error handling`, …).
   - `audience_framing`: how to frame output (`for a PR`, `for internal docs`, `for a paper`, `for a brownbag`, `for a security report`, `unspecified`).
   - `output_shape_preference`: `narrative` / `ranked_list` / `dossier` / `comparison_table` / `unspecified`.
   - `raw_text`: preserved verbatim — every downstream prompt sees the original sentence too.
3. **A confirmation chip strip** appears once the profile is extracted: *"I'll focus on: auth surface · suspicion-flag fragile spots · frame for a security report. Edit?"* The user can correct or accept in one click. This is the trust handshake before analysis runs.
4. **A Capability Planner** (deterministic, no LLM) reads the `IntentProfile` and picks which agents to run from the shared capability library: Cartographer, Flow Tracer, Lane A/B/C scanners, Decision Archaeology, plus per-capability tilt parameters. The same eight or so capabilities compose into whatever the user asked for.

This sounds trivial. It is not. Every existing tool treats codebase exploration as a navigation problem — *give me a map and let me walk*. We treat it as a **purpose-fulfillment** problem — *given that you want X, here is the shortest sequence of files and ideas that gets you to X*.

The captured `IntentProfile` is **persisted in state and injected into every downstream generation prompt** — alongside the user's raw sentence, so the model sees both the structured profile and the original framing. The Capability Planner uses the profile to choose which capabilities to invoke and how to tilt them.

The capability library — eight building blocks, fixed and well-tested. The planner composes them per-intent:

| Capability | What it does | Common tilts |
|---|---|---|
| **Cartographer** | Builds the system map (entry points, hubs, layers) from the dependency graph. | Subsystem narrowing by `focus_keywords`. Hub selection bias: import-graph hubs, data-shaped hubs, hot-path hubs, decision-shaped hubs. |
| **Flow Tracer** | Traces one end-to-end flow via graph traversal. | Which flow to pick: canonical entry path, a feature path matching `focus_keywords`, a "read path" through the ORM, the auth flow, etc. |
| **Lane A — Issue Triage** | Pulls open GitHub issues; scores by graph-backed approachability. | Activated when `modality_weights.change` is high. Filterable by `focus_keywords`. |
| **Lane B — Code Health** | Deterministic detectors: untested hot code, missing docstrings, AST dup, churn × complexity, year-old TODOs, dead code. | Activated for both `change` and `evaluate` modalities. Framing differs — "cleanup opportunities" (change) vs "tradeoffs visible in the code" (evaluate). |
| **Lane C — Suspicion** | Structural anomalies in guarded language; every item ends with a `to_confirm:` step. | Filterable by `focus_keywords` (e.g., auth-related, async-related, IO-related). |
| **Decision Archaeology** | Reads `git log`, README, commit messages, and the import graph to extract architectural decisions and their rationale. | Activated when `modality_weights.evaluate` is high or when `audience_framing` is build-vs-buy / paper / competitive. |
| **Teacher** | Generates the user-facing narrative, sequencing whichever capabilities ran into a coherent output. | Output shape: `narrative` / `ranked_list` / `dossier` / `comparison_table`. Audience framing always reads the profile. |
| **Q&A** | Always-on. Hybrid retrieval (vector → graph) with the same `IntentProfile` injected so answers stay goal-anchored. | Available throughout the tour, not just at the end. |

**The same repository produces radically different output for different stated intents** because the planner activates different capabilities and tilts them differently — *not* because there are separate "modes". An intent like *"I'm a security researcher; show me the auth surface"* activates Cartographer (narrowed to `auth`+`permission` keywords) + Lane C (with auth-relevant detectors) + Lane B (missing tests near auth) + Teacher (framed for a security report). An intent like *"comparing pagination strategies across libraries"* activates Cartographer (narrowed to pagination call sites) + Flow Tracer (on the pagination read path) + Decision Archaeology (for the rationale) + Teacher (in `comparison_table` shape). Same eight capabilities; planner picks the subset.

The user can revise their intent at any time — the chip strip is always editable, and re-planning is one click. Re-indexing is not required.

### What every tour delivers (universal) — and what shifts per intent (variable)

Every tour, regardless of stated intent, has the same trust spine:

| Universal property | Why it's always true |
|---|---|
| **Pre-context capture before analysis** | The Intent Profiler always runs first. No capability fires until the `IntentProfile` is confirmed. |
| **Verified grounding** | Every factual claim goes through the Verifier and renders with `✓ grounded` or `flagged`. This is the trust floor. |
| **Hybrid retrieval (vector + graph)** | Every claim shows its retrieval path. The graph is always available; the planner just chooses what to traverse. |
| **Synchronized code viewer** | Click any claim → the exact lines load. Q&A drives the viewer too. |
| **Q&A escape hatch** | Always reachable. Reads the same `IntentProfile`, so answers stay goal-anchored. |
| **Actionability contract** | No stat dumps. Every section ends in motion. Enforced at four layers (state, prompt, verifier, eval) — the same enforcement runs for any intent. |
| **Trust surfaces** | Verified badges, retrieval-path chips, intent-match chips, considered-and-rejected trails (when scanner lanes are active). |

What **shifts** per intent — driven entirely by the `IntentProfile` and the Capability Planner's choices:

| Shifts | How it varies |
|---|---|
| **Which capabilities run** | The planner activates a subset of `{Cartographer, Flow Tracer, Lane A, Lane B, Lane C, Decision Archaeology, Q&A}` based on `modality_weights`. Q&A is always on. |
| **How each capability is tilted** | Cartographer hub selection bias, Flow Tracer flow choice, Lane filtering by `focus_keywords`, Decision Archaeology pass scope. |
| **Output shape** | `narrative` (long-form prose) / `ranked_list` (cards with CTAs) / `dossier` (sectioned with evidence per claim) / `comparison_table` (when an external referent is given). |
| **Audience framing** | Teacher prompt template varies — "for a PR description" / "for an internal wiki" / "for a security report" / "for a build-vs-buy memo" / unspecified default. |
| **Success criterion** | What "I got what I came for" means depends on the intent. The Intent Profiler suggests a measurable success criterion as part of the confirmation chip strip, e.g. *"You'll know this worked if you can name two design decisions worth pushing back on."* |
| **Time on screen** | Typical 3–6 minutes; the planner can choose lighter capability sets for "tell me one thing" intents and heavier sets for "give me a dossier" intents. |

**Implementation note on the capability library.** None of the eight capabilities are persona-specific code paths. Each is an independently testable agent or pass (specified in `docs/03`), invokable in any combination, taking the full `IntentProfile` as a prompt input. Adding a ninth capability later (a Security Scanner, a Documentation Generator, an API Surface Comparator) does not require restructuring the pipeline — it adds an item to the library, plus a heuristic in the Capability Planner for when to activate it. This is the architectural property that lets the product genuinely be purpose-elastic instead of pretending to be.

### The five principles (the contract this product lives or dies by)

1. **Truthful over fluent.** Every factual claim ships with a `file:line` reference, verified by a separate model against the actual chunks. Claims the Verifier cannot ground are rendered as `flagged` — visible to the user, never silently shipped as fact. "I'm not sure" is a first-class answer.
2. **Teach, don't dump.** Progressive disclosure. No stat dumps. No 600-line summaries. The Iteration-2 output contract makes this enforceable, not aspirational.
3. **Meet the purpose.** The full `IntentProfile` (raw text + structured tilts) is injected into every generation prompt. A section that doesn't tie back to the user's stated intent is cut.
4. **Narrow and deep.** Python + Learn must be excellent before TypeScript or anything else. Widening early is the failure mode that kills products like this.
5. **Earn trust on real repos.** Quality is evaluated on real public repos — fastapi, httpx, flask — via an eval harness in CI. Not synthetic fixtures.

### Why agentic beats a single prompt

A naive implementation is "stuff the whole repo in a long context and ask GPT to write a tour." This fails three ways at once:

1. **Grounding.** A single generation step cannot cite what it didn't retrieve. With nothing forcing the model to pull specific lines and reference them, it confabulates.
2. **Depth of reasoning.** Building a system map, tracing a flow, *and* narrating it in one prompt produces shallow output on all three. Specialization is what unlocks depth — Cartographer thinks in graph metrics, Flow Tracer thinks in paths, Teacher thinks in narrative.
3. **Verification.** No single-prompt system can check itself. The Verifier is a separate model with a separate prompt and a binary grounding rubric. It catches errors the generator cannot see in itself.

The agent architecture — typed state, specialized nodes, a verification loop with retry budget, deterministic tools that do not invent — is what makes principle 1 (truthful over fluent) actually true rather than aspirational.

---

## Success criteria

We measure success on three dimensions, each with a concrete bar:

| Dimension | Metric | Bar |
|---|---|---|
| **Truthfulness** | Verifier grounding accuracy on the eval set | ≥ 90% |
| **Actionability (Iteration 2)** | % of generated tour sections that pass the actionability rubric | ≥ 80% |
| **Time-to-first-question** | From paste-URL to first useful answer about the repo | ≤ 90 s for a 50 kLOC repo (cold-start indexing) |
| **Intent profiling accuracy** | On a labeled set of 50 stated intents (paraphrasing the 12 examples in the planner mapping above + 38 originals), the profiler extracts the expected `modality_weights` / `focus_keywords` / `audience_framing` / `output_shape_preference` | ≥ 90% per-field |
| **Planner correctness** | On the same labeled set, the Capability Planner activates the expected capability subset (precision + recall on the subset) | ≥ 90% F1 |
| **Lane A approachability honesty** | % of top-3 issues that are genuinely approachable (manual review) when Lane A is activated | ≥ 70% on the eval repos |
| **Lane C suspicion legitimacy** | % of Lane C suspicions that hold up under human review | ≥ 75% on 20 hand-labeled cases |
| **Decision-Archaeology fidelity** | % of decision-dossier claims that are confirmable from the cited code + commit (manual review) when Decision Archaeology is activated | ≥ 85% on 3 eval repos (fastapi, httpx, flask) |

If any of these falls below the bar, the gate fails and the phase does not ship. These are not aspirational targets — they are merge blockers.

---

## Hard scope fence — what v1 will NOT do

We will be tempted to add each of these. We will not.

- **No multi-language support.** Python only. tree-sitter grammars for other languages are not loaded.
- **No private repos.** Public GitHub only. No token-based access in v1.
- **No "explain my own code."** The product is built for stranger-codebase onboarding. Repos you wrote do not need a tour.
- **No IDE plugin.** Web app only. The synchronized code viewer is part of the demo, not a developer surface.
- **No team mode.** Single user, no accounts, no sharing tours. (Adding a shareable read-only URL post-v0.1 is fine.)
- **No real-time multi-user editing.** Tours are generated once and cached. Re-generation is explicit.
- **No code execution / sandboxing.** The system never runs the target repo's code. Static analysis only.
- **No fine-tuning.** All models are off-the-shelf. The Verifier may be fine-tuned post-v0.1 as a stretch goal — not in v1.
- **No paid-tier dependencies.** Groq free tier + Hugging Face local + free hosting. The whole stack is free-tier survivable.
- **No "feature suggestions" lane in Contribute.** Lane D is deferred — except for suggestions explicitly grounded in the repo's own stated intent (TODOs, CONTRIBUTING.md, README planned-features).
- **No HITL (human-in-the-loop) interrupts in v1.** Tours run to completion or error. Pause/edit/resume is a post-v0.1 enhancement.
- **No session persistence in v1.** Tours are ephemeral — closing the tab loses the tour, and re-opening the app starts fresh. Re-pasting the same repo URL reuses the cached *index* (so indexing doesn't repeat) but generates a new tour. Shareable tour URLs and resumable sessions are on the post-v0.1 backlog.

This fence exists because every successful narrow product was tempted to widen and held the line. We hold the line.
