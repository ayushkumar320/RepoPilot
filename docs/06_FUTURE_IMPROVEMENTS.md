# 06 — Future Improvements (Pre-Build Review)

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

## Application order

Recommended order if applying in one pass:

1. **M5** (beachhead) — trivial, blocks everything else
2. **M3** (capability dependencies) — architectural; touches state schema
3. **M1** (Verifier batching) — architectural; touches Verifier loop design
4. **M2** (eval labeling time) + **M4** (Phase 4 budget) — schedule realism, can edit together
5. **S1–S6** in any order — local edits
6. **W1–W4** in any order — local edits

Total estimated editing time: **60–90 minutes** for Must + Should; another 30 minutes for Worth.

## Sign-off checklist (do not start Phase 0 until all checked)

- [ ] All **M** items checked and committed
- [ ] All **S** items either checked or explicitly deferred with a written reason
- [ ] All eval datasets that block Phase 2/3 gates have been scoped (even if not yet labeled)
- [ ] Per-tour token budget calculated and concurrency limit chosen
- [ ] CLAUDE.md updated if any of the above introduced new project-wide conventions
- [ ] This document committed and pushed before Phase 0 PR is opened
