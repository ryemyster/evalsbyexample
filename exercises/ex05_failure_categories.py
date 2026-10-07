"""Exercise 5 (step 6): compare a baseline and a candidate by failure category.

candidate-v1 passes more cases than the baseline overall. Your job is to show
what that average hides. A run is the dict saved in runs/*.json; each item in
run["results"] has "case_id", "passed", "worst_severity", and "failed_checks"
(a list of check names such as "action_boundary").

    python3 -m exercises 5

Then compare with the real command:
    python3 -m returns_eval compare baseline candidate-v1
"""


def failure_table(baseline_run: dict, candidate_run: dict) -> dict[str, tuple[int, int, int]]:
    """For every check name that appears in either run's failed_checks, return
    (cases failing in baseline, cases failing in candidate, total cases).

    Example entry: {"action_boundary": (0, 2, 26)}
    """
    raise NotImplementedError("implement failure_table()")


def newly_failing(baseline_run: dict, candidate_run: dict) -> list[str]:
    """Sorted case ids that pass in the baseline but fail in the candidate."""
    raise NotImplementedError("implement newly_failing()")


def critical_cases(run: dict) -> list[str]:
    """Sorted case ids whose worst failure is critical."""
    raise NotImplementedError("implement critical_cases()")
