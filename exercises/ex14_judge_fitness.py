"""Exercise 14 (Part 2, Module 4): is this judge fit for the job you have in mind?

judge-a and judge-b agree with people equally often on the holdout split. Decide
which (if either) to use, how, and where people must still look. Full card:
exercises/README.md, Exercise 14.

    python3 -m returns_eval calibrate judge-a judge-b --split calibration
    (decide)
    python3 -m returns_eval calibrate judge-a judge-b --split holdout     # once, at the end
    python3 -m exercises 14

Part 1: two small functions. "problem" is the thing a judge looks for.
"""

from __future__ import annotations


def confusion(truth: list[str], verdicts: list[str]) -> dict[str, int]:
    """Count {"tp", "fn", "fp", "tn"} with "problem" as the positive label.
    tp: both say problem. fn: people say problem, judge says ok. fp: people ok, judge problem. tn: both ok."""
    raise NotImplementedError("implement confusion()")


def recall_precision(cm: dict[str, int]) -> tuple[float | None, float | None]:
    """(recall, precision). Recall = tp / (tp + fn); precision = tp / (tp + fp). None if a denominator is 0."""
    raise NotImplementedError("implement recall_precision()")


# Part 2: your decision. Make it on the calibration split, then check it once on the holdout split.
DECISION = {
    "use": "TODO",                    # "auto-pass": drafts the judge calls ok skip a person's tone check
                                      # "triage": people check every draft; the judge only decides the order
    "judge": "TODO",                  # "judge-a" or "judge-b"
    "worse_mistake": "TODO",          # "missed problem" or "false alarm": which costs more in that use?
    "min_recall": "TODO",             # the share of real problems that must reach a person (a number, 0 to 1),
                                      # counting problems the judge catches plus unsure verdicts sent to people
    "send_to_people_below_confidence": "TODO",  # a number (0 to 1), or None to never escalate on confidence
    "people_always_review": ["TODO"],  # segments (next steps) where a person always checks tone, e.g. "decline_return"
    "holdout_confirms": "TODO",       # "yes" or "no": on the holdout split, does your setup still reach min_recall?
    "why": "TODO",
}
