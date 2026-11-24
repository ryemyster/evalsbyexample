"""Reference solution for Exercise 10."""


def per_attempt_rate(results):
    attempts = [a for r in results for a in r["attempts"]]
    return sum(a["passed"] for a in attempts), len(attempts)


def every_attempt_rate(results):
    return sum(all(a["passed"] for a in r["attempts"]) for r in results), len(results)


DECISION = {
    "b_vs_a_after_one_run": "better",
    "b_vs_a_after_ten_runs": "can't tell",
    "c_vs_a_after_ten_runs": "better",
    "rc002_who_was_wrong": "check",
    "why_one_run_is_not_enough": (
        "The same model scored anywhere from 21 to 26 out of 26 depending on the seed, so a two-case gap "
        "between single runs is the size of the wobble itself. Only the paired comparison over ten runs "
        "shows whether the gap is bigger than luck."
    ),
}
