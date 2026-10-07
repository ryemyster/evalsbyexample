"""Reference solution for Exercise 7."""

from statistics import median


def median_minutes(rows, arm, request_type=None):
    picked = [float(r["handling_minutes"]) for r in rows
              if r["arm"] == arm and (request_type is None or r["request_type"] == request_type)]
    return median(picked), len(picked)


def rate(rows, arm, column, value):
    in_arm = [r for r in rows if r["arm"] == arm]
    return sum(r[column] == value for r in in_arm), len(in_arm)


WHY_OFFLINE_IS_NOT_ENOUGH = (
    "The offline eval checks drafts against known cases; it never measures how long an agent spends "
    "reviewing them or whether customers come back. In the pilot, escalations got slower and repeat "
    "contacts did not fall, and an agent caught a wrong amount on a kind of order the cases never covered."
)
