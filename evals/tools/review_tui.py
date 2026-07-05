"""Terminal review loop for candidate eval labels (Phase 0, Option A).

Walks every row of a ``*.candidates.jsonl`` file (from ``propose_labels.py``)
and lets a human accept/trim the candidate refs, add keywords, or reject the
row. Progress is saved after every keystroke, so quitting and resuming is
safe. Accepted rows are exported in the ``GroundingEvalRow`` schema.

Keys (per row):
    a  accept — pick which candidate refs are truly load-bearing, add keywords
    r  reject — drop the row entirely
    k  keep as not-in-repo hallucination probe (no refs)
    s  skip for now (stays unreviewed)
    q  quit (progress saved)

Usage::

    uv run python evals/tools/review_tui.py \
        --candidates evals/tools/candidates/flask_qa_v1.candidates.jsonl \
        --out packages/evals/src/repopilot_evals/datasets/flask_qa_v1.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def save(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def show_row(idx: int, total: int, row: dict) -> None:
    print("\n" + "=" * 78)
    print(f"[{idx + 1}/{total}] {row['question']}")
    if row.get("not_in_repo"):
        print("  (proposed as NOT-IN-REPO hallucination probe)")
    for i, ref in enumerate(row.get("candidate_refs", []), start=1):
        sym = ref.get("symbol") or "—"
        print(
            f"  {i}. {ref['file_path']}:{ref['start_line']}-{ref['end_line']}"
            f"  [{sym}]  d={ref.get('_distance', '?')}"
        )
        summary = ref.get("_summary")
        if summary:
            print(f"       {str(summary)[:90]}")


def accept_row(row: dict) -> None:
    picks = input("  keep which candidates? (e.g. 1,3 — REVIEW IN GITHUB FIRST): ").strip()
    chosen: list[dict] = []
    for token in picks.replace(" ", "").split(","):
        if token.isdigit() and 1 <= int(token) <= len(row["candidate_refs"]):
            ref = dict(row["candidate_refs"][int(token) - 1])
            ref.pop("_distance", None)
            ref.pop("_summary", None)
            chosen.append(ref)
    if not chosen:
        print("  no refs chosen — row left unreviewed")
        return
    for ref in chosen:
        adjust = input(
            f"  {ref['file_path']}:{ref['start_line']}-{ref['end_line']} — "
            "enter to keep, or 'start:end' to correct lines: "
        ).strip()
        if ":" in adjust:
            start, end = adjust.split(":", 1)
            ref["start_line"], ref["end_line"] = int(start), int(end)
    keywords = input("  expected answer keywords (comma-separated, 2-4): ").strip()
    row["expected_refs"] = chosen
    row["expected_answer_keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]
    row["not_in_repo"] = False
    row["reviewed"] = True
    print("  ✓ accepted")


def review(candidates_path: Path, out_path: Path | None) -> None:
    rows = load(candidates_path)
    pending = [i for i, r in enumerate(rows) if not r.get("reviewed") and not r.get("rejected")]
    print(f"{len(rows)} rows, {len(pending)} pending review")

    for idx in pending:
        row = rows[idx]
        show_row(idx, len(rows), row)
        while True:
            key = (
                input("  [a]ccept  [r]eject  [k]eep-not-in-repo  [s]kip  [q]uit > ").strip().lower()
            )
            if key == "a":
                accept_row(row)
                break
            if key == "r":
                row["rejected"] = True
                row["reviewed"] = True
                print("  ✗ rejected")
                break
            if key == "k":
                row["expected_refs"] = []
                row["not_in_repo"] = True
                row["reviewed"] = True
                print("  ✓ kept as hallucination probe")
                break
            if key == "s":
                break
            if key == "q":
                save(candidates_path, rows)
                print("progress saved; resume with the same command")
                return
        save(candidates_path, rows)

    save(candidates_path, rows)
    accepted = [r for r in rows if r.get("reviewed") and not r.get("rejected")]
    print(
        f"\nreview complete: {len(accepted)} accepted, "
        f"{sum(1 for r in rows if r.get('rejected'))} rejected"
    )

    if out_path and accepted:
        with out_path.open("w", encoding="utf-8") as fh:
            for row in accepted:
                fh.write(
                    json.dumps(
                        {
                            "question": row["question"],
                            "expected_refs": row["expected_refs"],
                            "expected_answer_keywords": row["expected_answer_keywords"],
                            "not_in_repo": row["not_in_repo"],
                        }
                    )
                    + "\n"
                )
        print(f"exported {len(accepted)} rows → {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument(
        "--out", type=Path, default=None, help="export accepted rows in GroundingEvalRow schema"
    )
    args = parser.parse_args()
    review(args.candidates, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
