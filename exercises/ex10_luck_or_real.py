"""Exercise 10 (Part 2, Module 1): luck, or a real improvement?

The team tried two new prompts for a model. One run each says prompt 2 (sim-model-b)
beats prompt 1 (sim-model-a). Before anyone switches, find out whether that's real.
The models are SIMULATED: scripts with built-in randomness, so this costs nothing.
Full card (objective, evidence, decision, reflection): exercises/README.md, Exercise 10.

    python3 -m returns_eval run --candidate sim-model-a
    python3 -m returns_eval run --candidate sim-model-b
    python3 -m returns_eval report latest:sim-model-a --case RC-002
    python3 -m returns_eval variance sim-model-a sim-model-b sim-model-c --runs 10
    python3 -m exercises 10

Part 1: two small functions. `results` is run["results"] from a run made with --repeat:
each item has "attempts", a list where every attempt has "passed" (True or False).
"""


def per_attempt_rate(results: list[dict]) -> tuple[int, int]:
    """Across every attempt of every case: (attempts that passed, attempts).
    This is what one customer meets: one draft, one roll of the dice."""
    raise NotImplementedError("implement per_attempt_rate()")


def every_attempt_rate(results: list[dict]) -> tuple[int, int]:
    """(cases that passed on EVERY attempt, cases). Sometimes written pass^k: it asks
    whether the assistant is right reliably, not just once."""
    raise NotImplementedError("implement every_attempt_rate()")


# Part 2: your reading of the evidence. Use "better", "worse", or "can't tell" for the
# comparisons, and "model" or "check" for who was wrong.
DECISION = {
    "b_vs_a_after_one_run": "TODO",    # run 1 (seed 1) only: how does sim-model-b look next to sim-model-a?
    "b_vs_a_after_ten_runs": "TODO",   # from the variance report
    "c_vs_a_after_ten_runs": "TODO",   # from the variance report
    "rc002_who_was_wrong": "TODO",     # sim-model-a, seed 1, RC-002: read the draft. Was the model wrong, or the check?
    "why_one_run_is_not_enough": "TODO: in your own words",
}
