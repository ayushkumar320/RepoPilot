"""Propose candidate labels for a QA eval dataset (Phase 0, Option A).

Mechanical candidate generation — NO LLM grades anything. For each question
in a plain-text questions file (one per line), run the current
``vector_search`` and emit the top hits as *candidate* ``expected_refs``.
A human then reviews every row in ``review_tui.py`` before the dataset is
trusted.

Usage::

    uv run python evals/tools/propose_labels.py \
        --repo flask --questions evals/tools/questions/flask.txt \
        --out evals/tools/candidates/flask_qa_v1.candidates.jsonl

Question-file syntax: lines starting with ``!`` mark not-in-repo rows
(hallucination probes); they get empty refs by design.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packages"))

from repopilot_agents.tools.vector_search import vector_search
from repopilot_evals.runners.common import build_eval_context, resolve_repo_id

CANDIDATE_K = 6
# Over-fetch so source files survive after dropping test/example/doc hits,
# which dominate raw vector search but are never valid gold labels.
FETCH_K = 150
NOISE_PREFIXES = ("tests/", "test/", "examples/", "docs/", "docs_src/", "scripts/")


def _is_noise(file_path: str) -> bool:
    return file_path.startswith(NOISE_PREFIXES)


def _load_questions(questions_path: Path) -> list[str]:
    lines = [ln.strip() for ln in questions_path.read_text(encoding="utf-8").splitlines()]
    return [ln for ln in lines if ln and not ln.startswith("#")]


async def propose(repo: str, questions_path: Path, out_path: Path) -> None:
    lines = _load_questions(questions_path)

    ctx = build_eval_context()
    rows: list[dict[str, object]] = []
    try:
        repo_id = await resolve_repo_id(ctx.engine, repo_slug=repo)
        for line in lines:
            not_in_repo = line.startswith("!")
            question = line.lstrip("!").strip()
            candidates: list[dict[str, object]] = []
            if not not_in_repo:
                hits = await vector_search(
                    question,
                    engine=ctx.engine,
                    provider=ctx.provider,
                    repo_id=repo_id,
                    k=FETCH_K,
                )
                hits = [h for h in hits if not _is_noise(h.ref.file_path)][:CANDIDATE_K]
                candidates = [
                    {
                        "file_path": h.ref.file_path,
                        "start_line": h.ref.start_line,
                        "end_line": h.ref.end_line,
                        "symbol": h.ref.symbol,
                        "_distance": round(h.distance, 4),
                        "_summary": h.summary,
                    }
                    for h in hits
                ]
            rows.append(
                {
                    "question": question,
                    "candidate_refs": candidates,
                    "expected_refs": [],
                    "expected_answer_keywords": [],
                    "not_in_repo": not_in_repo,
                    "reviewed": False,
                }
            )
            print(f"  [{len(rows):>2}] {question[:70]} → {len(candidates)} candidates")
    finally:
        await ctx.aclose()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    print(f"\nwrote {len(rows)} candidate rows → {out_path}")
    print("next: uv run python evals/tools/review_tui.py --candidates " + str(out_path))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(propose(args.repo, args.questions, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
