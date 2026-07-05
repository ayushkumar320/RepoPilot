"""Paired bootstrap significance test between two metric arrays.

Used by every phase gate: given per-question scores before and after a
change, decide whether the mean delta is statistically significant at
``alpha``. Small datasets will often report ``inconclusive`` — that is the
correct answer, not a bug.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from statistics import mean

DEFAULT_ALPHA = 0.05
DEFAULT_RESAMPLES = 10_000


@dataclass(slots=True)
class SignificanceResult:
    mean_before: float
    mean_after: float
    mean_delta: float
    ci_low: float
    ci_high: float
    alpha: float
    n: int
    significant: bool

    @property
    def verdict(self) -> str:
        if self.significant:
            return "significant improvement" if self.mean_delta > 0 else "significant regression"
        return "not significant"

    def as_dict(self) -> dict[str, float | int | bool | str]:
        return {
            "mean_before": self.mean_before,
            "mean_after": self.mean_after,
            "mean_delta": self.mean_delta,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "alpha": self.alpha,
            "n": self.n,
            "significant": self.significant,
            "verdict": self.verdict,
        }


def paired_bootstrap(
    before: list[float],
    after: list[float],
    *,
    alpha: float = DEFAULT_ALPHA,
    n_resamples: int = DEFAULT_RESAMPLES,
    seed: int = 0,
) -> SignificanceResult:
    if len(before) != len(after):
        raise ValueError(f"paired arrays must match: {len(before)} vs {len(after)}")
    if not before:
        raise ValueError("cannot test significance on empty arrays")

    deltas = [a - b for b, a in zip(before, after, strict=True)]
    n = len(deltas)
    rng = random.Random(seed)
    resampled_means = sorted(mean(rng.choices(deltas, k=n)) for _ in range(n_resamples))
    lo_idx = int((alpha / 2) * n_resamples)
    hi_idx = min(int((1 - alpha / 2) * n_resamples), n_resamples - 1)
    ci_low = resampled_means[lo_idx]
    ci_high = resampled_means[hi_idx]
    significant = ci_low > 0 or ci_high < 0

    return SignificanceResult(
        mean_before=mean(before),
        mean_after=mean(after),
        mean_delta=mean(deltas),
        ci_low=ci_low,
        ci_high=ci_high,
        alpha=alpha,
        n=n,
        significant=significant,
    )


__all__ = ["DEFAULT_ALPHA", "DEFAULT_RESAMPLES", "SignificanceResult", "paired_bootstrap"]
