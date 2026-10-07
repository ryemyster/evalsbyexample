"""Reference solution for Exercise 5."""


def failure_table(baseline_run, candidate_run):
    names = []
    for run in (baseline_run, candidate_run):
        for result in run["results"]:
            for name in result["failed_checks"]:
                if name not in names:
                    names.append(name)

    def failing(run, name):
        return sum(name in r["failed_checks"] for r in run["results"])

    total = len(candidate_run["results"])
    return {name: (failing(baseline_run, name), failing(candidate_run, name), total) for name in names}


def newly_failing(baseline_run, candidate_run):
    passed_before = {r["case_id"] for r in baseline_run["results"] if r["passed"]}
    return sorted(r["case_id"] for r in candidate_run["results"] if not r["passed"] and r["case_id"] in passed_before)


def critical_cases(run):
    return sorted(r["case_id"] for r in run["results"] if r["worst_severity"] == "critical")
