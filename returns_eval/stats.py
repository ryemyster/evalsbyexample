"""Small, standard-library statistics used by Part 2 of the course.

Everything here is a plain function with no hidden state, so each number in a
report can be checked by hand. Where the course shows uncertainty, it uses:

  wilson()          a range for a rate measured on a small sample. Recommended over the
                    textbook "p +/- 1.96 * standard error" for small samples
                    (Brown, Cai & DasGupta, 2001). See docs/sources.md.
  bootstrap_mean()  a range for an average, found by re-drawing the sample many times
                    with a fixed seed, so the range is the same every time you run it.
  cohen_kappa()     agreement between two raters after removing the agreement you'd get
                    by chance (Cohen, 1960).
  confusion()       how often a grader's verdicts match a reference label, split into
                    the four kinds of right and wrong.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from statistics import mean
from typing import Any, Sequence


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for k successes out of n. (0, 1) when n is 0."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def frac_range(k: int, n: int) -> str:
    """ "9 / 20 (45%, likely 26% to 66%)": the count, the rate, and a 95% range for it."""
    if n == 0:
        return f"{k} / 0 (n/a)"
    lo, hi = wilson(k, n)
    return f"{k} / {n} ({k / n:.0%}, likely {lo:.0%} to {hi:.0%})"


def bootstrap_mean(values: Sequence[float], seed: int = 1, resamples: int = 4000,
                   level: float = 0.95) -> tuple[float, float]:
    """A range for the average of `values`: re-draw the values with replacement many times,
    take each average, and keep the middle `level` of them. Seeded, so it never changes."""
    if not values:
        return 0.0, 0.0
    rng = random.Random(f"bootstrap|{seed}")
    n = len(values)
    averages = sorted(sum(rng.choice(values) for _ in range(n)) / n for _ in range(resamples))
    cut = int(round((1 - level) / 2 * resamples))
    return averages[cut], averages[resamples - cut - 1]


def cohen_kappa(a: Sequence[Any], b: Sequence[Any]) -> float | None:
    """Agreement beyond chance between two raters who rated the same items.

    1 = always agree; 0 = agree only as often as chance would; below 0 = worse than chance.
    None when it can't be computed (no items, or both raters always gave the same single value).
    """
    if len(a) != len(b):
        raise ValueError("both raters must rate the same items")
    n = len(a)
    if n == 0:
        return None
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[v] * cb[v] for v in set(ca) | set(cb)) / (n * n)
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def confusion(truth: Sequence[str], verdicts: Sequence[str], positive: str) -> dict[str, int]:
    """Count the four outcomes, treating `positive` as "a problem was found".

    tp  the reference says problem, and the grader found it        (caught)
    fn  the reference says problem, but the grader passed it       (missed: false acceptance)
    fp  the reference says fine, but the grader flagged it         (false alarm: false rejection)
    tn  the reference says fine, and the grader passed it          (correctly passed)
    """
    if len(truth) != len(verdicts):
        raise ValueError("need one verdict per reference label")
    cm = {"tp": 0, "fn": 0, "fp": 0, "tn": 0}
    for t, v in zip(truth, verdicts):
        if t == positive:
            cm["tp" if v == positive else "fn"] += 1
        else:
            cm["fp" if v == positive else "tn"] += 1
    return cm


def rates(cm: dict[str, int]) -> dict[str, float | None]:
    """Precision, recall, specificity, F1, and accuracy from a confusion() result.
    A value is None when its denominator is 0 (for example, recall when there were no problems)."""
    tp, fn, fp, tn = cm["tp"], cm["fn"], cm["fp"], cm["tn"]

    def div(x: int, y: int) -> float | None:
        return x / y if y else None

    precision, recall = div(tp, tp + fp), div(tp, tp + fn)
    f1 = (2 * precision * recall / (precision + recall)
          if precision is not None and recall is not None and precision + recall else None)
    return {"precision": precision, "recall": recall, "specificity": div(tn, tn + fp),
            "f1": f1, "accuracy": div(tp + tn, tp + fn + fp + tn)}


def percentile(values: Sequence[float], q: float) -> float:
    """Nearest-rank percentile (q between 0 and 1). Same method as the p95 draft time."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


__all__ = ["wilson", "frac_range", "bootstrap_mean", "cohen_kappa", "confusion", "rates", "percentile", "mean"]
