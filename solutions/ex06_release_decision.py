"""Reference solution for Exercise 6."""


def release_decision(summary):
    if summary["critical_failures"] > 0:
        return "BLOCKED"
    rate = summary["passed"] / summary["cases"] if summary["cases"] else 0
    if summary["must_pass_failed"] > 0 or rate < summary["min_pass_rate"]:
        return "NOT READY"
    if not summary["human_review_complete"]:
        return "PENDING"
    return "READY"
