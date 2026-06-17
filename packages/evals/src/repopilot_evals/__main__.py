"""CLI entrypoint for RepoPilot evals.

Subcommands::

    uv run python -m repopilot_evals list          # every registered eval
    uv run python -m repopilot_evals status        # which gates are dataset-ready / measured / unmeasured
    uv run python -m repopilot_evals run grounding [--sample N] [--report]
    uv run python -m repopilot_evals run verifier  [--sample N] [--report]

The ``run`` subcommand invokes the real ``answer_question`` / ``verify_claim``
paths (no monkeypatches) and prints the actual gate numbers. Exit code is
0 on pass, 1 on fail. With ``--report``, writes JSON + Markdown under
``eval-reports/`` so results outlive the terminal session.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import asdict

from repopilot_evals.datasets import load_jsonl_rows
from repopilot_evals.registry import REGISTRY, EvalSpec, get_spec
from repopilot_evals.reports import find_latest_report, write_report
from repopilot_evals.runners.grounding import GroundingEvalMetrics, run_grounding_eval
from repopilot_evals.runners.verifier import VerifierEvalMetrics, run_verifier_eval

# ── reporting helpers ──────────────────────────────────────────────────────


def _grounding_markdown(metrics: GroundingEvalMetrics, spec: EvalSpec) -> str:
    lines = [
        f"- Total rows: {metrics.total}",
        f"- Grounding accuracy: **{metrics.grounding_accuracy:.1%}** (gate ≥ {spec.gate:.0%})",
        f"- Keyword accuracy: {metrics.keyword_accuracy:.1%}",
        f"- Ref recall: {metrics.ref_recall:.1%}",
        f"- Hallucination rate: {metrics.hallucination_rate:.1%}",
    ]
    if metrics.multi_hop_questions:
        lines.append(
            f"- Multi-hop accuracy: {metrics.multi_hop_accuracy:.1%} "
            f"({metrics.multi_hop_correct}/{metrics.multi_hop_questions})"
        )
    failures = [c for c in metrics.cases if not (c.grounded and c.hallucination_pass)]
    if failures:
        lines.append("\n## Failing rows\n")
        for case in failures:
            flags = ", ".join(
                flag
                for cond, flag in [
                    (not case.grounded, "ungrounded"),
                    (not case.keyword_match, "keyword-miss"),
                    (not case.ref_match, "ref-miss"),
                    (not case.hallucination_pass, "hallucinated"),
                ]
                if cond
            )
            lines.append(f"- **[{flags}]** {case.question}")
    return "\n".join(lines) + "\n"


def _verifier_markdown(metrics: VerifierEvalMetrics, spec: EvalSpec) -> str:
    lines = [
        f"- Total rows: {metrics.total}",
        f"- Accuracy: **{metrics.accuracy:.1%}** (gate ≥ {spec.gate:.0%})",
    ]
    failures = [c for c in metrics.cases if not c.correct]
    if failures:
        lines.append("\n## Failing rows\n")
        for case in failures:
            lines.append(
                f"- expected=`{case.expected_verdict}` actual=`{case.actual_verdict}` — {case.claim}"
            )
    return "\n".join(lines) + "\n"


def _print_grounding(metrics: GroundingEvalMetrics, spec: EvalSpec) -> bool:
    print(f"grounding eval — {metrics.total} rows")
    print(f"  grounding accuracy:  {metrics.grounding_accuracy:.1%} (gate ≥ {spec.gate:.0%})")
    print(f"  keyword accuracy:    {metrics.keyword_accuracy:.1%}")
    print(f"  ref recall:          {metrics.ref_recall:.1%}")
    print(f"  hallucination rate:  {metrics.hallucination_rate:.1%}")
    if metrics.multi_hop_questions:
        print(
            f"  multi-hop accuracy:  {metrics.multi_hop_accuracy:.1%} "
            f"({metrics.multi_hop_correct}/{metrics.multi_hop_questions})"
        )
    failures = [c for c in metrics.cases if not (c.grounded and c.hallucination_pass)]
    if failures:
        print(f"\n  {len(failures)} failing row(s):")
        for case in failures:
            flags = []
            if not case.grounded:
                flags.append("ungrounded")
            if not case.keyword_match:
                flags.append("keyword-miss")
            if not case.ref_match:
                flags.append("ref-miss")
            if not case.hallucination_pass:
                flags.append("hallucinated")
            print(f"    - [{', '.join(flags)}] {case.question}")
    return metrics.grounding_accuracy >= spec.gate


def _print_verifier(metrics: VerifierEvalMetrics, spec: EvalSpec) -> bool:
    print(f"verifier eval — {metrics.total} rows")
    print(f"  accuracy:  {metrics.accuracy:.1%} (gate ≥ {spec.gate:.0%})")
    failures = [c for c in metrics.cases if not c.correct]
    if failures:
        print(f"\n  {len(failures)} failing row(s):")
        for case in failures:
            print(
                f"    - expected={case.expected_verdict} actual={case.actual_verdict}: {case.claim}"
            )
    return metrics.accuracy >= spec.gate


# ── runners dispatched by eval name ────────────────────────────────────────


async def _run_one(spec: EvalSpec, args: argparse.Namespace) -> int:
    passed: bool
    headline: float
    payload: dict[str, object]
    markdown: str
    if spec.name == "grounding":
        g_metrics = await run_grounding_eval(
            dataset_name=spec.dataset,
            repo_slug=args.repo_slug,
            sample_limit=args.sample,
        )
        passed = _print_grounding(g_metrics, spec)
        headline = g_metrics.grounding_accuracy
        payload = asdict(g_metrics)
        markdown = _grounding_markdown(g_metrics, spec)
    elif spec.name == "verifier":
        v_metrics = await run_verifier_eval(
            dataset_name=spec.dataset,
            repo_slug=args.repo_slug,
            sample_limit=args.sample,
        )
        passed = _print_verifier(v_metrics, spec)
        headline = v_metrics.accuracy
        payload = asdict(v_metrics)
        markdown = _verifier_markdown(v_metrics, spec)
    else:
        print(
            f"error: eval {spec.name!r} is registered but its runner is not "
            f"wired into the CLI yet (phase {spec.phase} work).",
            file=sys.stderr,
        )
        return 2

    if args.report:
        json_path, md_path = write_report(
            eval_name=spec.name,
            dataset=spec.dataset,
            gate=spec.gate,
            headline_metric=headline,
            passed=passed,
            payload=payload,
            markdown_body=markdown,
        )
        print(f"\nreport written:\n  {json_path}\n  {md_path}")
    return 0 if passed else 1


# ── list / status ──────────────────────────────────────────────────────────


def _cmd_list(_: argparse.Namespace) -> int:
    print(f"{'NAME':<18} {'PHASE':<6} {'GATE':<6} {'DATASET'}")
    for spec in REGISTRY:
        print(f"{spec.name:<18} {spec.phase:<6} {spec.gate:<6.0%} {spec.dataset}")
    return 0


def _cmd_status(_: argparse.Namespace) -> int:
    print(f"{'NAME':<18} {'PHASE':<6} {'DATASET':<10} {'LAST RESULT':<26} {'BLOCKERS'}")
    for spec in REGISTRY:
        if spec.dataset_present:
            try:
                row_count = len(load_jsonl_rows(spec.dataset_path))
            except Exception:
                row_count = -1
            dataset = f"yes ({row_count})"
        else:
            dataset = "missing"

        last = find_latest_report(spec.name)
        if last:
            verdict = "PASS" if last["passed"] else "FAIL"
            last_text = f"{last['headline_metric']:.1%} {verdict} @ {last['timestamp_utc']}"
        else:
            last_text = "unmeasured"

        blockers = []
        if not spec.dataset_present:
            blockers.append("dataset")
        if spec.needs_llm:
            blockers.append("llm-credits")
        if spec.needs_indexed_repo:
            blockers.append("indexed-repo")
        blockers_text = ", ".join(blockers) if blockers else "none"

        print(f"{spec.name:<18} {spec.phase:<6} {dataset:<10} {last_text:<26} {blockers_text}")
    return 0


# ── entrypoint ─────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(prog="repopilot_evals", description=__doc__)
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    subparsers.add_parser("list", help="Print the registry").set_defaults(fn=_cmd_list)
    subparsers.add_parser("status", help="Show dataset / last-result status").set_defaults(
        fn=_cmd_status
    )

    run = subparsers.add_parser("run", help="Run a registered eval against the real LLM")
    run.add_argument("eval_name", help="One of: " + ", ".join(s.name for s in REGISTRY))
    run.add_argument("--repo-slug", default="httpx")
    run.add_argument("--sample", type=int, default=None, help="Limit to first N rows")
    run.add_argument("--report", action="store_true", help="Persist a JSON+Markdown report")

    args = parser.parse_args()

    if args.cmd in {"list", "status"}:
        result: int = args.fn(args)
        return result

    try:
        spec = get_spec(args.eval_name)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not spec.dataset_present:
        print(
            f"error: dataset {spec.dataset!r} not found at {spec.dataset_path}. "
            "Label it before running.",
            file=sys.stderr,
        )
        return 2

    return asyncio.run(_run_one(spec, args))


if __name__ == "__main__":
    sys.exit(main())
