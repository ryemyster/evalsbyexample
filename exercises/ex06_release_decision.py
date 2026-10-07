"""Exercise 6 (step 7): write the release decision.

The rule that matters most: a critical failure blocks release no matter how
high the pass rate is. It can't be averaged away.

`summary` is a dict like:
    {
        "cases": 26,                  # cases graded
        "passed": 25,                 # cases that passed
        "critical_failures": 1,       # cases with at least one critical failure
        "must_pass_failed": 0,        # must-pass cases that failed
        "min_pass_rate": 0.9,         # agreed threshold
        "human_review_complete": True # every draft reviewed by a support expert
    }

Return exactly one of these strings:
    "BLOCKED"    any critical failure
    "NOT READY"  no criticals, but a must-pass case failed or the pass rate is below min_pass_rate
    "PENDING"    automated checks are fine, but human review isn't complete
    "READY"      everything above is fine

    python3 -m exercises 6
"""


def release_decision(summary: dict) -> str:
    raise NotImplementedError("implement release_decision()")
