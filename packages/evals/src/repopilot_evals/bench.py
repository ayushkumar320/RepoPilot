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

    print("[bench] retrieval metrics (no LLM cost beyond embeddings)…")
    retrieval = await run_retrieval_eval(dataset_name=dataset, repo_slug=repo, sample_limit=sample)
    metrics: dict[str, object] = dict(retrieval.as_dict())
    metrics["per_question"] = {
        "recall@10": [c.recall[10] for c in retrieval.cases],
        "ndcg@5": [c.ndcg[5] for c in retrieval.cases],
        "mrr": [c.mrr for c in retrieval.cases],
    }

    if not skip_llm:
        print("[bench] grounding + hallucination (full answer_question path)…")
        grounding = await run_grounding_eval(
            dataset_name=dataset, repo_slug=repo, sample_limit=sample
        )
        metrics["grounding_accuracy"] = grounding.grounding_accuracy
        metrics["hallucination_rate"] = grounding.hallucination_rate
        metrics["keyword_accuracy"] = grounding.keyword_accuracy
        metrics["grounding_cases"] = [asdict(c) for c in grounding.cases]

        if repo == "httpx":
            # verifier_quality_v1 refs point at httpx chunks; only meaningful there
            print("[bench] verifier accuracy (verifier_quality_v1)…")
            verifier = await run_verifier_eval(repo_slug=repo, sample_limit=sample)
            metrics["verifier_accuracy"] = verifier.accuracy

        print("[bench] latency p50/p95…")
        latency = await run_latency_eval(dataset_name=dataset, repo_slug=repo, sample_limit=sample)
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
    return json_path, csv_path


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
