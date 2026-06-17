"""Persisted eval reports.

Each eval run writes a timestamped JSON + Markdown pair under
``eval-reports/`` (gitignored). This turns "I saw a number once" into a
verifiable measurement trail — directly supporting RepoPilot's
"truthful over fluent" principle for the eval layer itself.

JSON is the machine-readable record (consumed by CI / dashboards later).
Markdown is the human-readable record (paste into PRs, share with
collaborators).
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPORTS_DIR = Path(__file__).resolve().parents[4] / "eval-reports"


def _now_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _coerce(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _coerce(v) for k, v in asdict(value).items()}
    if isinstance(value, list):
        return [_coerce(v) for v in value]
    if isinstance(value, dict):
        return {k: _coerce(v) for k, v in value.items()}
    return value


def _ensure_reports_dir() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORTS_DIR


def write_report(
    *,
    eval_name: str,
    dataset: str,
    gate: float,
    headline_metric: float,
    passed: bool,
    payload: dict[str, Any],
    markdown_body: str,
) -> tuple[Path, Path]:
    """Write a JSON + Markdown report pair. Returns ``(json_path, md_path)``."""
    stamp = _now_stamp()
    base = _ensure_reports_dir() / f"{stamp}-{eval_name}"
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")

    record = {
        "eval_name": eval_name,
        "dataset": dataset,
        "gate": gate,
        "headline_metric": headline_metric,
        "passed": passed,
        "timestamp_utc": stamp,
        "payload": _coerce(payload),
    }
    json_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    header = (
        f"# {eval_name} — {stamp}\n\n"
        f"- **Dataset:** `{dataset}`\n"
        f"- **Gate:** ≥ {gate:.0%}\n"
        f"- **Result:** {headline_metric:.1%} — {'PASS' if passed else 'FAIL'}\n\n"
    )
    md_path.write_text(header + markdown_body, encoding="utf-8")
    return json_path, md_path


def find_latest_report(eval_name: str) -> dict[str, Any] | None:
    """Return the most recent JSON record for ``eval_name``, or ``None``."""
    if not REPORTS_DIR.exists():
        return None
    candidates = sorted(REPORTS_DIR.glob(f"*-{eval_name}.json"))
    if not candidates:
        return None
    record: dict[str, Any] = json.loads(candidates[-1].read_text(encoding="utf-8"))
    return record


__all__ = ["REPORTS_DIR", "find_latest_report", "write_report"]
