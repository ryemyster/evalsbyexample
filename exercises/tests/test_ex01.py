from returns_eval.grading import CHECKS, CRITICAL

from ._support import ExerciseCase, load

OUTCOME_WORDS = ("time", "rework", "edit", "repeat", "escalat", "resolution", "contact", "reopen", "cost")


class TestEx01(ExerciseCase):
    exercise = 1
    where = "exercises/ex01_eval_charter.py"

    def setUp(self):
        self.charter = load("ex01_eval_charter").CHARTER

    def test_no_todos_left(self):
        if "TODO" in repr(self.charter):
            self.not_done("replace every TODO in CHARTER")

    def test_decision_is_a_question(self):
        decision = self.charter["product_decision"].strip()
        self.assertTrue(decision.endswith("?"), "product_decision should be a yes/no question ending in '?'")
        self.assertGreaterEqual(len(decision.split()), 6, "product_decision is too short to name a user and a task")

    def test_baseline_described(self):
        self.assertGreaterEqual(len(self.charter["baseline"].split()), 6, "describe today's workflow in a sentence")

    def test_three_levels_of_success(self):
        for level in ("output_quality", "workflow_behavior", "product_outcome"):
            items = self.charter["success"].get(level, [])
            self.assertTrue(items and all(i.strip() and "TODO" not in i for i in items), f"add at least one item to success['{level}']")
        outcome = " ".join(self.charter["success"]["product_outcome"]).lower()
        self.assertTrue(any(w in outcome for w in OUTCOME_WORDS),
                        "product_outcome should name something a pilot measures (time, rework, repeat contacts, ...)")

    def test_unacceptable_failures_map_to_real_checks(self):
        failures = self.charter["unacceptable_failures"]
        names = {name for name, _, _ in CHECKS}
        self.assertGreaterEqual(len(failures), 3, "list at least three unacceptable failures")
        for failure, check in failures.items():
            self.assertIn(check, names, f"'{failure}' maps to '{check}', which is not a check. Choose from: {sorted(names)}")
        critical = {name for name, sev, _ in CHECKS if sev == CRITICAL}
        missing = critical - set(failures.values())
        self.assertFalse(missing, f"no unacceptable failure maps to the critical check(s): {sorted(missing)}")
