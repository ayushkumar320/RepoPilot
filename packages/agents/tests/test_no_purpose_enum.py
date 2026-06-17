"""Hard CI rule: nothing in the source tree may branch on a ``purpose`` enum.

Phase 3 lifted the elasticity guarantee into CI. The architecture rule
is in ``docs/03_ARCHITECTURE.md`` § "State rules" #7:

> No capability code path depends on a "purpose" enum. If you find
> yourself writing ``if state.purpose == "learn":`` you've reintroduced
> the bucketed model and broken the elasticity property.

This test enforces it by grepping the source tree for the forbidden
patterns. If a future commit reintroduces a purpose enum, the test
fails — loudly, and with the offending file:line reported.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Patterns that signal a return-to-bucketed-thinking. Kept conservative
# — they catch the explicit cases the doc calls out without flagging
# perfectly innocent uses of the word "purpose" in comments.
FORBIDDEN_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bstate\.purpose\b"),
    re.compile(r"\bpurpose_enum\b"),
    re.compile(r"\bPurpose\s*=\s*Literal\["),
]


# Directories we scan. Tests and docs are excluded so this very file
# (and the architecture doc itself, which quotes the forbidden pattern)
# don't trip the check.
SCAN_ROOTS = [
    REPO_ROOT / "packages" / "agents" / "src",
    REPO_ROOT / "packages" / "core" / "src",
    REPO_ROOT / "packages" / "ingestion" / "src",
    REPO_ROOT / "packages" / "evals" / "src",
    REPO_ROOT / "apps",
]


def _iter_source_files() -> list[Path]:
    out: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        out.extend(root.rglob("*.py"))
    return out


def test_no_purpose_enum_in_source_tree() -> None:
    hits: list[str] = []
    for path in _iter_source_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(line):
                    hits.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")
    assert not hits, (
        "Found forbidden purpose-enum references — see docs/03 § State rules #7.\n"
        + "\n".join(hits)
    )
