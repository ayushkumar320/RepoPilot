# RAG Plan — Risks, Disadvantages & Concrete Fixes

> Companion to [`../RAG_PLAN.md`](../RAG_PLAN.md). The plan describes what we will build and the gates each phase must pass. **This doc is the adversarial read**: where the plan is weak, where a gate can be gamed or can't fire, and what to change before the weakness costs a wrong conclusion.
>
> Rule of engagement (from [`../../CLAUDE.md`](../../CLAUDE.md) §6): *truthful over fluent*. This doc applies that rule to the plan itself. If a number the plan promises cannot be delivered by the eval it specifies, that is a risk, not a detail.

---

## TL;DR

The plan's **discipline is excellent** (measure-before-claim, revert-on-no-gain, verifier-sees-raw-truth). Its disadvantages nearly all flow from **one root cause: the eval sets are too small and too subjective to reliably detect the 3–5 pp effects the entire gate structure depends on.** The other risks — inconsistent latency budgets, an unvalidated verifier, lenient multiple-comparison gates — compound from there.

If you fix one thing, fix the eval sets (R1).

---

## R1 — The eval foundation is too thin for the effects being measured (ROOT RISK)

**Severity: high. Blocks trustworthy conclusions in every phase.**

- Datasets are 16–20 rows (`httpx_qa_v1`, `flask_qa_v1`, `fastapi_qa_v1`), plus 10–12 row special sets (`multi_hop_v1`, `rare_symbol_v1`). On 16–20 rows a **5 pp lift ≈ one question flipping**.
- Phase 0 already concedes the bootstrap CI "will frequently say `inconclusive`." But every phase gate is defined around a **5 pp** (or 3 pp / NDCG 0.05) lift. So the plan's own significance machinery will **rarely fire cleanly** — forcing a choice between lowering rigor or stalling.
- **Single-labeler subjectivity.** `expected_refs` is defined as "the minimal set of chunks the answer truly depends on." For multi-hop / architectural questions there is often no single true minimal set. Recall@k then measures the labeler's opinion as much as the retriever. No inter-annotator agreement is collected, so labeling noise is indistinguishable from real regression.
- The LLM-proposes-then-human-reviews shortcut (1.5 h) reintroduces exactly the bias the double-check protocol was meant to remove.

**Fix F1:**
- Grow primary sets to **≥ 50 rows/repo** (httpx, flask, fastapi), keeping the single/multi/not-in-repo mix.
- **Two independent labelers** on at least one repo; report Cohen's κ on `expected_refs` overlap. Require κ ≥ 0.6 before any recall number is treated as dispositive.
- For questions where "minimal set" is genuinely ambiguous, label a **graded** relevance (primary / supporting / irrelevant) and switch those rows to NDCG/graded-recall rather than binary recall.
- If sizes can't grow, **downgrade the plan's language** from "measured improvement" to "directional signal" everywhere. Don't claim statistical rigor the n can't support.

---

## R2 — Per-phase latency budgets are mathematically inconsistent with the global gate

**Severity: high. The plan can pass every phase and still violate its own Definition of Done.**

Each phase permits an independent latency regression:

| Phase | Allowed p95 regression (per phase doc) |
|---|---|
| 1 | ≤ 1.5× baseline |
| 2 | ≤ 1.3× Phase 1 |
| 3 | ≤ 1.2× Phase 2 |
| 4 | ≤ 2× Phase 0 baseline |
| 5 | ≤ 1.2× Phase 4 |
| 6 | index-time only |

Multiplied through (1.5 × 1.3 × 1.2 × … with Phase 4's 2× as a floor), the stack can reach **~3–5.6× baseline**. The global Definition of Done in [`../RAG_PLAN.md`](../RAG_PLAN.md) demands **p95 ≤ 1.5× baseline**. Nothing reconciles the two. You could land all 6 phases, each "passing," and blow the global gate by 3×.

**Fix F2 — one reconciled, absolute budget.** Replace per-phase *relative* budgets with a single **absolute p95 ceiling measured against the Phase 0 baseline**, and give each phase a slice of it:

| Stage | p95 budget (absolute, vs Phase 0 baseline) |
|---|---|
| Phase 0 baseline | 1.00× (reference) |
| + Recall pool (P1) | ≤ 1.15× |
| + Query understanding (P2) | ≤ 1.30× |
| + BM25 fusion (P3) | ≤ 1.35× |
| + Rerank (P4) | ≤ 1.50× ← **global ceiling reached here** |
| + Compression (P5) | ≤ 1.50× (must net-neutral or claw back) |
| + Enrichment (P6) | ≤ 1.50× (index-time only; query path unchanged) |

Any phase that would push cumulative p95 past 1.50× **does not land** until it claws latency back (caching, pool truncation, parallelism). This makes Phase 4 (the reranker) the explicit place where the budget is spent, which matches reality.

---

## R3 — "Significant on at least one of three datasets" inflates false positives

**Severity: medium-high. Gates can pass on noise.**

Phases 1 and 4 ship if the lift is significant on **at least one** of three datasets at α = 0.05. With three independent tests, the family-wise false-positive rate is ~14%, not 5% — the multiple-comparisons problem is never addressed. Worse, the **stop condition contradicts the pass gate**: Phase 1 ships on "significant on httpx + one other" but is rolled back if "≤ 0.02 pp on both others." On 16-row sets both can be simultaneously true.

**Fix F3:**
- Pre-register the **primary dataset per phase** (the one the phase is designed to lift: `multi_hop_v1` for P2, `rare_symbol_v1` for P3, etc.). The gate is significance **on the primary set**; the others are guardrails-against-regression, not pass criteria.
- Apply **Holm–Bonferroni** correction when more than one dataset is used as a pass criterion.
- Resolve the P1 contradiction: pass = significant lift on primary + **no regression** elsewhere. Delete the "≤ 0.02 on both others = overfit" clause (it's subsumed and conflicting).

---

## R4 — The verifier is load-bearing but unvalidated

**Severity: high. Undermines the product's core truth claim.**

"Grounded, not guessed" — the thesis and the public-facing promise — rests on `verifier_accuracy ≥ 88%`, a number that **has never been measured**. If the verifier is itself wrong 15–20% of the time (plausible for an LLM judge), then every grounding-accuracy gate in Phases 1–6 is two error rates multiplied, and the phases can't be told apart from verifier noise. The 88% threshold is asserted, not derived.

**Fix F4:**
- Make verifier calibration a **hard Phase 0 exit gate** (it already is partially): no Phase 1+ number is published until `verifier_accuracy` is measured on `verifier_quality_v1` **under the real LLM**, with the confusion matrix committed.
- Justify the 88% floor: state the target grounding precision and back-derive the verifier accuracy needed for the grounding number to have a usable signal-to-noise ratio. If the data says 88% is too low, raise it.
- Grow `verifier_quality_v1` (30 rows) toward 60+ so the accuracy estimate has a tolerable CI.

---

## R5 — Phases optimize around a fixed, non-code-specialized embedding model

**Severity: medium. Caps the achievable ceiling; creates a chicken-and-egg constraint.**

Recall is bottlenecked by `nomic-embed-text` (768d, general-purpose). Phases 1–6 tune *around* it, and the plan forbids changing it without a 3-repo A/B — but you can't run that A/B meaningfully until the eval harness exists (Phase 0) and is trustworthy (R1). The gates assume headroom the embedder may not have.

**Fix F5:**
- Add an **embedding-model A/B as an optional Phase 0.5** (harness already built, no pipeline change): swap in one code-specialized embedder (e.g. a code-tuned model) behind a flag and measure recall on the same sets. Cheap, and it tells you whether Phases 1–6 are chasing a ceiling that a better embedder would raise for free.
- If the A/B shows a large gap, re-sequence: the embedder swap may dominate several downstream phases.

---

## R6 — Phases are measured pairwise, but the effects interact

**Severity: medium. A late phase can silently cancel an early one.**

Each phase compares only to the phase before it. The docs already flag interactions: MMR (P4) × compression (P5) can fight; multi-query (P2) × BM25 (P3) fusion can hide bad rewrites. With only pairwise deltas, a late regression that undoes an early gain is invisible — you'd see "Phase 5 passed" without noticing it erased Phase 1's lift end-to-end.

**Fix F6:**
- After Phase 4 and again after Phase 6, run a **full ablation** (each component on/off) against the **Phase 0** baseline, not just the previous phase. Commit an `ablation.json`.
- Track one **end-to-end north-star metric** (grounding accuracy on the union of all sets) across every phase, so a cancellation shows up as a flat or falling north star even when the pairwise delta "passed."

---

## R7 — Synthetic-content safety rests on a single test

**Severity: medium. One routing bug silently grounds false claims.**

Phases 5 (compressed views) and 6 (`enriched_text`) both create content the answerer/verifier must treat differently from raw source. The invariant "verifier reads raw `content`" is correct by design but protected by **one integration test each**. A future refactor that routes the compressed/enriched view to the verifier breaks the truth guarantee silently — no gate would catch it because grounding accuracy could even *improve* on a wrong-but-self-consistent view.

**Fix F7:**
- Promote the invariant to a **property test + a runtime assertion**: the verifier's input hash must equal the raw-chunk hash; assert in code, not only in a test.
- Add an **adversarial eval row**: a chunk whose docstring/enriched line *contradicts* its body. Correct behavior = verifier rejects a claim grounded only in the synthetic line. Make this a permanent regression row.

---

## R8 — Small-model dependence makes two phases possibly-no-op

**Severity: low-medium. Wasted cost, not wrong conclusions.**

Phase 2's `QuerySpec` extraction + intent classification, and Phase 5's line-selection, all lean on the 8B model. The docs concede intent classification "may do nothing" on terse questions. Risk is a phase that lands as a no-op while still paying 3× embedding cost (P2) or an LLM-call-per-chunk (P5).

**Fix F8:**
- Gate each small-model feature behind its **own measured contribution**, not the phase's aggregate. If intent routing's marginal recall lift is < 1 pp, ship multi-query without it (the plan already allows this — make it the default decision rule, with a number attached).

---

## R9 — Phase 0 is a single point of failure on external access

**Severity: medium (operational, not methodological).**

Nothing downstream can produce a trustworthy number until paid Groq quota + LangSmith key + human labeling time are all in hand ([../CURRENT_PHASE.md](../CURRENT_PHASE.md) entry checklist). All three are currently unchecked. The Ollama-only fallback doubles latency, which then interacts with R2 (baseline measured on one latency regime, phases shipped on another).

**Fix F9:**
- Decide the **baseline LLM regime once** and measure the baseline on the *same* regime the phases will ship on. Don't baseline on Groq and develop on Ollama if the published numbers must be comparable.
- If quota is uncertain, run the **full plan on Ollama-only** end-to-end and label the numbers as such — internally consistent beats externally impressive-but-incomparable.

---

## Priority order for acting on this doc

1. **R1 / F1** — grow + de-bias eval sets (or downgrade claims). Everything else is downstream of this.
2. **R4 / F4** — validate the verifier before publishing any grounding number.
3. **R2 / F2** — adopt the single absolute latency budget table.
4. **R3 / F3** — fix the significance protocol and the P1 self-contradiction.
5. **R5 / F5** — run the embedding A/B so Phases 1–6 aren't chasing a low ceiling.
6. **R6–R9** — ablations, synthetic-content hardening, small-model gating, regime consistency.

None of these change the *shape* of the plan. They change whether its numbers can be believed.
