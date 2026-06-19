"""Lane A — issue triage backed by graph approachability."""

from __future__ import annotations

from repopilot_agents.state import CodeRef, IntentProfile, Opportunity, RejectedItem
from repopilot_agents.tools.github_issues import Issue
from repopilot_agents.types import SymbolMetrics


def approachability_score(metrics: SymbolMetrics) -> float:
    """Score issue approachability from graph facts, not GitHub labels."""
    fan_penalty = min(metrics.fan_in, 40) / 40
    complexity_penalty = min(metrics.cyclomatic, 20) / 40
    test_bonus = 0.15 if metrics.has_tests else 0.0
    return max(0.0, min(1.0, 0.85 - fan_penalty - complexity_penalty + test_bonus))


def _ref_for_issue(issue: Issue, fallback_symbol: str | None) -> CodeRef:
    file_path = issue.referenced_files[0] if issue.referenced_files else "UNKNOWN"
    return CodeRef(file_path=file_path, start_line=1, end_line=1, symbol=fallback_symbol)


def triage_issues(
    issues: list[Issue],
    *,
    metrics_by_symbol: dict[str, SymbolMetrics],
    profile: IntentProfile,
    limit: int = 3,
) -> tuple[list[Opportunity], list[RejectedItem]]:
    """Rank issues and keep the next three rejected reasons."""
    scored: list[tuple[float, Issue, SymbolMetrics | None]] = []
    for issue in issues:
        if profile.focus_keywords:
            haystack = " ".join(
                [issue.title, issue.body, *issue.labels, *issue.referenced_files]
            ).lower()
            if not any(keyword.lower() in haystack for keyword in profile.focus_keywords):
                continue
        metric = next(
            (
                metrics
                for symbol, metrics in metrics_by_symbol.items()
                if symbol in issue.body or any(symbol in path for path in issue.referenced_files)
            ),
            None,
        )
        score = approachability_score(metric) if metric is not None else 0.35
        scored.append((score, issue, metric))

    scored.sort(key=lambda item: (-item[0], item[1].number))
    accepted = scored[:limit]
    rejected = scored[limit : limit + 3]

    rejected_items = [
        RejectedItem(
            title=f"#{issue.number} {issue.title}",
            reason=(
                f"ranked down because {metric.symbol} has fan-in {metric.fan_in}"
                if metric is not None
                else "ranked down because no referenced symbol could be checked against the graph"
            ),
            evidence_refs=[_ref_for_issue(issue, metric.symbol if metric is not None else None)],
        )
        for _, issue, metric in rejected
    ]

    opportunities: list[Opportunity] = []
    for score, issue, metric in accepted:
        symbol = metric.symbol if metric is not None else None
        ref = _ref_for_issue(issue, symbol)
        opportunities.append(
            Opportunity(
                lane="A_issue",
                title=f"#{issue.number} {issue.title}",
                evidence_refs=[ref],
                why_this_matters=(
                    "This issue maps to a low-blast-radius area of the graph, "
                    "so it is a plausible first contribution."
                ),
                blast_radius="hub" if metric is not None and metric.fan_in >= 10 else "isolated",
                difficulty="S" if score >= 0.65 else "M",
                suggested_first_step=f"Open issue #{issue.number} and confirm the referenced file still matches the report.",
                files_to_touch=list(issue.referenced_files),
                nearest_tests=[] if metric is None or not metric.has_tests else ["tests/"],
                mergeability=0.7,
                approachability=score,
                evidence_strength=0.65 if metric is not None else 0.35,
                intent_match=f"matches: {profile.raw_text!r}",
                considered_and_rejected=rejected_items,
            )
        )
    return opportunities, rejected_items


def run_lane_a_triage(
    issues: list[Issue],
    *,
    metrics_by_symbol: dict[str, SymbolMetrics],
    profile: IntentProfile,
) -> dict[str, list[Opportunity]]:
    opportunities, _ = triage_issues(
        issues,
        metrics_by_symbol=metrics_by_symbol,
        profile=profile,
    )
    return {"triaged_issues": opportunities, "opportunity_list": opportunities}


__all__ = ["approachability_score", "run_lane_a_triage", "triage_issues"]
