"""Exercise 4 (step 5): check that human reviewers agree before trusting their ratings.

Two support experts rated the same candidate-v2 drafts (ILLUSTRATIVE data in
data/human_review/). If they often disagree, the rubric is unclear, and an
average of their ratings hides that. Write two small functions.

Each review row is a dict with at least: "case_id", "draft_fingerprint", and
one key per criterion ("usability", "policy_interpretation", "tone",
"case_expectation_ok").

    python3 -m exercises 4

Then try the real command:
    python3 -m returns_eval review-summary latest:candidate-v2 data/human_review/*.csv
"""


def percent_agreement(reviews_a: list[dict], reviews_b: list[dict], criterion: str) -> tuple[int, int]:
    """Return (agree, total).

    total = drafts rated by BOTH reviewers, matched on case_id AND draft_fingerprint
            (a rating of an older version of a draft doesn't count).
    agree = how many of those got the same value for `criterion`.
    """
    raise NotImplementedError("implement percent_agreement()")


def disagreements(reviews_a: list[dict], reviews_b: list[dict], criterion: str) -> list[str]:
    """Case ids (sorted) where both reviewers rated the same draft but gave different values."""
    raise NotImplementedError("implement disagreements()")
