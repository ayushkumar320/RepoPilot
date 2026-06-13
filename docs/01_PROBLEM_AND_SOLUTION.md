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

### The beachhead user

We are not trying to serve every developer. Concretely, v1 is built for:

- **Junior developers** (0–3 years of experience) or **first-time open-source contributors** of any seniority.
- Coming to a **public GitHub repository** they did not write.
- Working on **Python** code (no other languages in v1).
- With one of two purposes in mind: *I want to learn how this works* or *I want to make my first PR*.

Everything else — TypeScript repos, private repos, "explain my own code," team-mode multi-user tours — is explicitly out of scope until the beachhead is excellent.

---

## The solution

A multi-agent web app that, given a public Python GitHub URL, produces a **purpose-driven guided tour** in which every factual claim is grounded in a `file:line` reference and every section ends with a next step the user can actually take.

### The core bet

Before doing any analysis, the system **captures pre-context about the user** with two short, deliberate questions:

1. **"Why are you here?"** → `purpose` ∈ {`learn`, `contribute`}
2. **One follow-up** to narrow the lens:
   - If learning: "Are you here for the overall structure, a specific feature, or the data model?" → `focus_hint`
   - If contributing: "Are you looking to fix an issue, improve quality, hunt for likely problems, or see all of these ranked?" → `contribution_intent`

This sounds trivial. It is not. Every existing tool treats codebase exploration as a navigation problem — *give me a map and let me walk*. We treat it as a **purpose-fulfillment** problem — *given that you want X, here is the shortest sequence of files and ideas that gets you to X*.

The captured pre-context is **persisted in state and injected into every downstream generation prompt** — Cartographer, Flow Tracer, Teacher, the contribute scanners, Q&A. The same repository produces a meaningfully different tour for:

| User says | What surfaces |
|---|---|
| Learning / overall structure | Entry points, top hubs, layer decomposition. Narrative emphasizes "what is this codebase shaped like." |
| Learning / specific feature | One traced end-to-end flow that includes that feature. Narrative emphasizes "how does this thing happen step by step." |
| Learning / data model | Schema-shaped classes, ORM/dataclass boundaries, where data is mutated. Narrative emphasizes "what does the system know about." |
| OSS contributor / fix an issue | Ranked GitHub issues, scored by **graph-backed approachability** (isolated functions, near tests). |
| OSS contributor / improve quality | Untested hot code, missing docstrings on public API, dead code, churn × complexity, year-old TODOs. |
| OSS contributor / hunt problems | Lane C suspicions in epistemically guarded language, each ending in a falsification step. |
| OSS contributor / show all ranked | All three lanes merged and ranked by mergeability. |

The user can always change their mind — re-running the tour with a different pre-context is one click. But the deliberate up-front question is what earns the system the right to be opinionated about what to surface, and gives the user a clean traceability path: *I see this because I told it I'm here to hunt problems.*

### Learn vs. Contribute — what each tour delivers

| Aspect | LEARN mode | CONTRIBUTE mode |
|---|---|---|
| **Pre-context question (required)** | "What part interests you most? (overall structure / a specific feature / the data model)" → stored as `focus_hint` | "What kind of contribution? (fix an issue / improve quality / hunt problems / show all)" → stored as `contribution_intent` |
| **What the pre-context shapes** | Cartographer privileges relevant hubs; Flow Tracer picks a flow matching the focus; Teacher narrative leads with what the user said matters. | Which scanner lanes contribute to the Opportunity List, and how the Ranker weights them. |
| **Pipeline** | Intent Router → Learn Elicitation → Cartographer → Flow Tracer → Teacher | Intent Router → Contribute Elicitation → Lane A/B/C scanners in parallel → Opportunity ranker → Teacher briefing |
| **Output shape** | System map (entry points / hubs / layers) → one traced end-to-end flow → narrative with mermaid diagrams | Ranked opportunity list, each with evidence refs, blast radius, difficulty (S/M/L), suggested first step, files to touch, nearest tests |
| **Success criterion** | The user can answer "what is this codebase, and how does a request flow through it?" without re-reading the docs. | The user can pick **one** opportunity from the list and start work on it the same day. |
| **Time on screen** | ≤ 4 minutes (target) | ≤ 5 minutes including elicitation |
| **Demo moment** | Click a claim → the synchronized code viewer highlights the exact source lines. | Click an opportunity → see the diff-shaped "files to touch" and "nearest tests" lift out of the codebase. |

### The five principles (the contract this product lives or dies by)

1. **Truthful over fluent.** Every factual claim ships with a `file:line` reference, verified by a separate model against the actual chunks. Claims the Verifier cannot ground are rendered as `flagged` — visible to the user, never silently shipped as fact. "I'm not sure" is a first-class answer.
2. **Teach, don't dump.** Progressive disclosure. No stat dumps. No 600-line summaries. The Iteration-2 output contract makes this enforceable, not aspirational.
3. **Meet the purpose.** `purpose`, `focus_hint`, and `contribution_intent` are injected into every generation prompt. A section that doesn't tie back to the user's goal is cut.
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
| **Contribute mode honesty** | % of top-3 opportunities that are genuinely approachable (manual review) | ≥ 70% on the eval repos |
| **Suspicion legitimacy** | % of Lane C suspicions that hold up under human review | ≥ 75% on 20 hand-labeled cases |

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
- **No paid-tier dependencies.** Groq free tier + Ollama local + free hosting. The whole stack is free-tier survivable.
- **No "feature suggestions" lane in Contribute.** Lane D is deferred — except for suggestions explicitly grounded in the repo's own stated intent (TODOs, CONTRIBUTING.md, README planned-features).
- **No HITL (human-in-the-loop) interrupts in v1.** Tours run to completion or error. Pause/edit/resume is a post-v0.1 enhancement.

This fence exists because every successful narrow product was tempted to widen and held the line. We hold the line.
