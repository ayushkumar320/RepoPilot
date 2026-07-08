"""Top-level RAG-phase bench runner.

Usage::

    uv run python -m repopilot_evals.bench --phase 0 --repo httpx
    uv run python -m repopilot_evals.bench --phase 0 --repo flask
    uv run python -m repopilot_evals.bench --phase 0 --repo fastapi
    uv run python -m repopilot_evals.bench --phase 0 --aggregate

Per-repo runs write ``evals/results/rag_phase{N}/{repo}_baseline.json``;
``--aggregate`` merges them into ``baseline.json`` (the committed source of
truth). ``--skip-llm`` runs only the retrieval + latency-free metrics for a
quota-free smoke pass.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from repopilot_agents.qa import graph as qa_graph
from repopilot_agents.tools.vector_search import NON_SOURCE_PATH_PREFIXES
from repopilot_evals.runners.grounding import run_grounding_eval
from repopilot_evals.runners.latency import run_latency_eval
from repopilot_evals.runners.retrieval import run_retrieval_eval
from repopilot_evals.runners.significance import paired_bootstrap
from repopilot_evals.runners.verifier import run_verifier_eval

REPO_DATASETS = {
    "httpx": "httpx_qa_v1.jsonl",
    "flask": "flask_qa_v1.jsonl",
    "fastapi": "fastapi_qa_v1.jsonl",
}


def results_dir(phase: int) -> Path:
    root = Path(__file__).resolve().parents[4]
    return root / "evals" / "results" / f"rag_phase{phase}"


async def bench_repo(
    repo: str, *, phase: int, skip_llm: bool, sample: int | None
) -> dict[str, object]:
    dataset = REPO_DATASETS[repo]
    print(f"[bench] phase {phase} · repo {repo} · dataset {dataset}")

    # One retrieval policy drives all three LLM-path evals so the arms are
    # comparable under a single verifier. Phase 0 = pre-Phase-1 policy (k-only
    # pool, no path filter); phase ≥ 1 = the Phase 1 policy (wide source-only
    # pool). This is what makes the grounding/latency guardrails honest: both
    # _before (phase 0) and _after (phase 1) are measured with the same,
    # fixed verifier — only the retrieval policy differs.
    policy_kwargs: dict[str, object]
    if phase >= 1:
        policy_kwargs = {
            "recall_k": qa_graph.RECALL_K,
            "exclude_path_prefixes": NON_SOURCE_PATH_PREFIXES,
        }
    else:
        policy_kwargs = {"recall_k": None, "exclude_path_prefixes": ()}

    print("[bench] retrieval metrics (no LLM cost beyond embeddings)…")
    retrieval = await run_retrieval_eval(
        dataset_name=dataset,
        repo_slug=repo,
        sample_limit=sample,
        **policy_kwargs,  # type: ignore[arg-type]
    )
    metrics: dict[str, object] = dict(retrieval.as_dict())
    metrics["per_question"] = {
        "recall@10": [c.recall[10] for c in retrieval.cases],
        "ndcg@5": [c.ndcg[5] for c in retrieval.cases],
        "mrr": [c.mrr for c in retrieval.cases],
    }

    if not skip_llm:
        print("[bench] grounding + hallucination (full answer_question path)…")
        grounding = await run_grounding_eval(
            dataset_name=dataset,
            repo_slug=repo,
            sample_limit=sample,
            **policy_kwargs,  # type: ignore[arg-type]
        )
        metrics["grounding_accuracy"] = grounding.grounding_accuracy
        metrics["claim_grounding_rate"] = grounding.claim_grounding_rate
        metrics["hallucination_rate"] = grounding.hallucination_rate
        metrics["keyword_accuracy"] = grounding.keyword_accuracy
        metrics["grounding_cases"] = [asdict(c) for c in grounding.cases]

        if repo == "httpx":
            # verifier_quality_v1 refs point at httpx chunks; only meaningful there
            print("[bench] verifier accuracy (verifier_quality_v1)…")
            verifier = await run_verifier_eval(repo_slug=repo, sample_limit=sample)
            metrics["verifier_accuracy"] = verifier.accuracy

        print("[bench] latency p50/p95…")
        latency = await run_latency_eval(
            dataset_name=dataset,
            repo_slug=repo,
            sample_limit=sample,
            **policy_kwargs,  # type: ignore[arg-type]
        )
        metrics.update(latency.as_dict())
        metrics.pop("total", None)
        metrics["total"] = retrieval.total

    metrics["repo"] = repo
    metrics["dataset"] = dataset
    metrics["phase"] = phase
    metrics["generated_at"] = datetime.now(UTC).isoformat()
    return metrics


def write_repo_result(phase: int, repo: str, metrics: dict[str, object]) -> Path:
    out_dir = results_dir(phase)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{repo}_baseline.json"
    path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return path


def aggregate(phase: int) -> tuple[Path, Path]:
    out_dir = results_dir(phase)
    per_repo: dict[str, dict[str, object]] = {}
    for repo in REPO_DATASETS:
        path = out_dir / f"{repo}_baseline.json"
        if path.exists():
            per_repo[repo] = json.loads(path.read_text(encoding="utf-8"))
    if not per_repo:
        raise SystemExit(f"no per-repo results in {out_dir}; run --repo first")

    index = {
        "phase": phase,
        "generated_at": datetime.now(UTC).isoformat(),
        "repos": per_repo,
    }
    json_path = out_dir / "baseline.json"
    json_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

    scalar_keys = sorted(
        {
            k
            for m in per_repo.values()
            for k, v in m.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        }
    )
    csv_path = out_dir / "baseline.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["repo", *scalar_keys])
        for repo, m in per_repo.items():
            writer.writerow([repo, *[m.get(k, "") for k in scalar_keys]])

    if phase >= 1:
        after_path = out_dir / "_after.json"
        after_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        write_delta(phase, index)
    return json_path, csv_path


LATENCY_P95_BUDGET = 1.5


def write_delta(phase: int, after: dict[str, object]) -> None:
    """Compare ``_after`` to ``_before`` per repo; fail on guardrail breaches.

    Guardrail (RAG_PLAN + rag/01 §5): ``latency_p95_ms`` may not regress
    beyond 1.5× the before-number. The recall/grounding gates need human
    judgment + the significance runner, so they are printed, not asserted.
    """
    out_dir = results_dir(phase)
    before_path = out_dir / "_before.json"
    if not before_path.exists():
        raise SystemExit(f"{before_path} missing — copy the previous phase's _after.json first")
    before = json.loads(before_path.read_text(encoding="utf-8"))

    tracked = (
        "recall@5",
        "recall@10",
        "recall@20",
        "ndcg@5",
        "mrr",
        "grounding_accuracy",
        "hallucination_rate",
        "latency_p95_ms",
    )
    delta: dict[str, dict[str, dict[str, float]]] = {}
    breaches: list[str] = []
    before_repos = before.get("repos", {})
    after_repos_obj = after.get("repos")
    after_repos: dict[str, dict[str, object]] = (
        after_repos_obj if isinstance(after_repos_obj, dict) else {}
    )
    for repo, m_after in after_repos.items():
        m_before = before_repos.get(repo, {})
        repo_delta: dict[str, dict[str, float]] = {}
        for key in tracked:
            b, a = m_before.get(key), m_after.get(key)
            if isinstance(b, (int, float)) and isinstance(a, (int, float)):
                repo_delta[key] = {"before": float(b), "after": float(a), "delta": float(a - b)}
        delta[repo] = repo_delta
        lat = repo_delta.get("latency_p95_ms")
        if lat and lat["before"] > 0 and lat["after"] > lat["before"] * LATENCY_P95_BUDGET:
            breaches.append(
                f"{repo}: latency_p95_ms {lat['before']:.0f} → {lat['after']:.0f} "
                f"(> {LATENCY_P95_BUDGET}× budget)"
            )

    delta_path = out_dir / "delta.json"
    delta_path.write_text(json.dumps(delta, indent=2) + "\n", encoding="utf-8")
    print(f"[bench] wrote {delta_path}")
    for repo, repo_delta in delta.items():
        for key in ("recall@10", "ndcg@5", "grounding_accuracy", "latency_p95_ms"):
            if key in repo_delta:
                d = repo_delta[key]
                print(
                    f"  {repo:<8} {key:<20} {d['before']:.4f} → {d['after']:.4f} "
                    f"(Δ {d['delta']:+.4f})"
                )
    if breaches:
        raise SystemExit("[bench] latency guardrail breached: " + "; ".join(breaches))


def self_test_significance(phase: int) -> None:
    """Gate sanity check: baseline vs itself must be 'not significant'."""
    path = results_dir(phase) / "baseline.json"
    index = json.loads(path.read_text(encoding="utf-8"))
    for repo, m in index["repos"].items():
        per_q = m.get("per_question", {})
        scores = per_q.get("recall@10")
        if not scores:
            continue
        result = paired_bootstrap(scores, scores)
        assert not result.significant, f"{repo}: self-comparison reported significant"
        print(f"[bench] significance self-test on {repo}: {result.verdict} ✓")


def main() -> int:
    parser = argparse.ArgumentParser(prog="repopilot_evals.bench", description=__doc__)
    parser.add_argument("--phase", type=int, required=True)
    parser.add_argument("--repo", choices=sorted(REPO_DATASETS))
    parser.add_argument("--aggregate", action="store_true")
    parser.add_argument("--skip-llm", action="store_true", help="retrieval metrics only")
    parser.add_argument("--sample", type=int, default=None, help="limit to first N rows")
    args = parser.parse_args()

    if args.aggregate:
        json_path, csv_path = aggregate(args.phase)
        print(f"[bench] wrote {json_path}\n[bench] wrote {csv_path}")
        self_test_significance(args.phase)
        return 0

    if not args.repo:
        parser.error("--repo or --aggregate is required")

    metrics = asyncio.run(
        bench_repo(args.repo, phase=args.phase, skip_llm=args.skip_llm, sample=args.sample)
    )
    path = write_repo_result(args.phase, args.repo, metrics)
    print(f"[bench] wrote {path}")
    for key in (
        "recall@5",
        "recall@10",
        "recall@20",
        "ndcg@5",
        "ndcg@10",
        "mrr",
        "grounding_accuracy",
        "claim_grounding_rate",
        "keyword_accuracy",
        "hallucination_rate",
        "verifier_accuracy",
        "latency_p50_ms",
        "latency_p95_ms",
    ):
        if key in metrics:
            print(
                f"  {key:<22} {metrics[key]:.4f}"
                if isinstance(metrics[key], float)
                else f"  {key:<22} {metrics[key]}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
