"""Reference solution for Exercise 12."""

from collections import Counter


def cohen_kappa(a, b):
    n = len(a)
    if n == 0:
        return None
    observed = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    expected = sum(ca[v] * cb[v] for v in set(ca) | set(cb)) / (n * n)
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


DECISION = {
    "first_rubric_kappa": 0.46,
    "clear_rubric_kappa": 0.85,
    "calibrate_against": "clear rubric labels",
    "why_tone_review_kappa_is_zero": (
        "Almost every draft got 'ok' from both reviewers, so they would agree that often just by both saying ok. "
        "The one draft that mattered, they disagreed on, so there's no agreement beyond chance."
    ),
}
