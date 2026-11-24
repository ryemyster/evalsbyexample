"""Exercise 16 (Part 2, Module 6): which layer failed?

A week of ILLUSTRATIVE production traces shows problems. A failed check is a
symptom; the fix depends on which layer caused it. Full card: exercises/README.md,
Exercise 16.

    python3 -m returns_eval traces
    python3 -m returns_eval traces --trace T-105      # and the others below
    python3 -m exercises 16

Part 1: one small function. A trace is a dict (see data/production/README.md):
trace["needed_specialist"] is True or False, and trace["steps"] is a list of dicts,
each with "step"; the "route" step has "queue" ("general" or "specialist").
"""

LAYERS = ("model", "orchestration", "policy", "data", "evaluator", "human_review")


def specialist_routed(trace: dict) -> bool:
    """True unless the ticket needed a specialist and was routed somewhere else."""
    raise NotImplementedError("implement specialist_routed()")


# Part 2: for each trace, the layer (or layers, as a list) that failed. Use the names in LAYERS.
ATTRIBUTION = {
    "T-105": "TODO",
    "T-109": "TODO",
    "T-112": "TODO",
    "T-115": "TODO",
    "T-120": "TODO",
    "T-124": "TODO",
    "T-203": "TODO",
}

# Part 3: which of those traces should become a new case in the offline case set (data/cases/)?
# The others need a fix and a test somewhere else (the routing code, the policy service, ...).
NEW_OFFLINE_CASES = ["TODO"]

# Part 4: T-122 failed a critical check too. Was that a failure of the system? Explain in a sentence or two.
T122 = "TODO"
