from returns_eval.candidates import load_candidate
from returns_eval.cases import CASES_DIR, load_case_set
from returns_eval.harness import run_eval

from ._support import ExerciseCase, load

CORE = load_case_set([CASES_DIR / "core.jsonl"])
BASELINE = run_eval(load_candidate("baseline"), CORE)
V1 = run_eval(load_candidate("candidate-v1"), CORE)


class TestEx05(ExerciseCase):
    exercise = 5
    where = "exercises/ex05_failure_categories.py"

    def setUp(self):
        self.mod = load("ex05_failure_categories")

    def test_failure_table(self):
        table = self.call(self.mod.failure_table, BASELINE, V1)
        self.assertEqual(table.get("action_boundary"), (0, 2, 26), "baseline never acts; v1 acted in 2 cases")
        self.assertEqual(table.get("customer_data"), (0, 2, 26))
        self.assertEqual(table.get("refund_commitment"), (0, 3, 26))
        self.assertEqual(table.get("resolution"), (11, 9, 26), "v1 picks better resolutions than the baseline")
        self.assertNotIn("length", table, "only include checks that failed in at least one run")

    def test_newly_failing(self):
        self.assertEqual(self.call(self.mod.newly_failing, BASELINE, V1), ["RC-024", "RC-025"],
                         "these passed with the baseline and fail with v1")

    def test_critical_cases(self):
        self.assertEqual(self.call(self.mod.critical_cases, V1), ["RC-001", "RC-018", "RC-020", "RC-024", "RC-025"])
        self.assertEqual(self.call(self.mod.critical_cases, BASELINE), [])
