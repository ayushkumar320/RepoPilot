"""Lane B — deterministic code-health opportunities."""

from __future__ import annotations

from dataclasses import dataclass

from repopilot_agents.state import CodeRef, Difficulty, IntentProfile, Opportunity
from repopilot_agents.types import SymbolMetrics


@dataclass(frozen=True, slots=True)
class QualityCandidate:
    detector: str
    ref: CodeRef
    metrics: SymbolMetrics
    is_entry_point: bool = False
    is_public_api: bool = True


def _difficulty(metrics: SymbolMetrics) -> Difficulty:
    if metrics.fan_in >= 20 or metrics.cyclomatic >= 15:
        return "L"
    if metrics.fan_in >= 8 or metrics.cyclomatic >= 8:
        return "M"
    return "S"


def detect_quality_opportunities(
    candidates: list[QualityCandidate],
    *,
    profile: IntentProfile,
) -> list[Opportunity]:
    """Transform deterministic detector hits into unified opportunities."""
    opportunities: list[Opportunity] = []
    for candidate in candidates:
        metrics = candidate.metrics
        if candidate.detector == "dead_code" and candidate.is_entry_point:
            continue
        if candidate.detector == "missing_docstring" and not candidate.is_public_api:
            continue

        symbol = candidate.ref.symbol or candidate.ref.file_path
        has_tests = metrics.has_tests
        mergeability = 0.8 if has_tests else 0.55
        approachability = max(0.1, 1.0 - min(metrics.fan_in, 30) / 40)
        evidence_strength = (
            0.75 if candidate.detector in {"dead_code", "missing_docstring"} else 0.65
        )
        opportunities.append(
            Opportunity(
                lane="B_quality",
                title=f"{candidate.detector.replace('_', ' ').title()} in {symbol}",
                evidence_refs=[candidate.ref],
                why_this_matters=(
                    f"{symbol} matches the {candidate.detector} detector; this is a bounded cleanup "
                    f"for {profile.raw_text!r}."
                ),
                blast_radius="hub" if metrics.fan_in >= 10 else "isolated",
                difficulty=_difficulty(metrics),
                suggested_first_step=f"Open {candidate.ref.file_path} and verify the detector result against nearby tests.",
                files_to_touch=[candidate.ref.file_path],
                nearest_tests=[] if not has_tests else ["tests/"],
                mergeability=mergeability,
                approachability=approachability,
                evidence_strength=evidence_strength,
                intent_match=f"matches: {profile.raw_text!r}",
            )
        )
    return opportunities


def run_lane_b_quality(
    candidates: list[QualityCandidate],
    *,
    profile: IntentProfile,
) -> dict[str, list[Opportunity]]:
    return {"opportunity_list": detect_quality_opportunities(candidates, profile=profile)}


__all__ = ["QualityCandidate", "detect_quality_opportunities", "run_lane_b_quality"]
