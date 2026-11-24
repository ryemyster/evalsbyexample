"""Exercise 12 (Part 2, Module 2): agreement beyond chance.

Two annotators labeled the same 64 drafts for tone, first with the team's vague
rubric and then with the clear one (ILLUSTRATIVE labels, data/labels/). Before
anyone builds a judge on these labels, check that the people agree, and not
just by luck. Full card: exercises/README.md, Exercise 12.

    python3 -m returns_eval labels
    python3 -m returns_eval review-summary latest:candidate-v2 data/human_review/*.csv
    python3 -m exercises 12

Part 1: implement Cohen's kappa. a and b are two equal-length lists of labels
("ok", "problem", or any other values), one per item, from two raters.

    observed = share of items where a and b match
    expected = sum over every label L of (share of a that is L) * (share of b that is L)
    kappa    = (observed - expected) / (1 - expected)

Return None if expected is exactly 1 (both raters only ever used one label, so
there's nothing to measure).
"""

from __future__ import annotations


def cohen_kappa(a: list, b: list) -> float | None:
    raise NotImplementedError("implement cohen_kappa()")


# Part 2: what the numbers mean. Round kappas to 2 decimals, as the labels command shows them.
DECISION = {
    "first_rubric_kappa": "TODO",          # a number, from python3 -m returns_eval labels
    "clear_rubric_kappa": "TODO",          # a number
    "calibrate_against": "TODO",           # "first rubric labels", "clear rubric labels", or "neither"
    "why_tone_review_kappa_is_zero": "TODO",  # review-summary: the reviewers gave the same tone rating to
                                              # 25 of 26 drafts, yet kappa is 0.00. Why, in your own words?
}
