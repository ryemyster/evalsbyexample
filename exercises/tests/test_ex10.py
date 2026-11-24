from returns_eval.candidates import load_candidate
from returns_eval.cases import CASES_DIR, load_case_set, subset
from returns_eval.harness import run_eval
from returns_eval.variance import paired_difference, repeated_runs, verdict

from ._support import ExerciseCase, load

CORE = load_case_set([CASES_DIR / "core.jsonl"])
FAKE = [
    {"attempts": [{"passed": True}, {"passed": True}, {"passed": True}]},
    {"attempts": [{"passed": True}, {"passed": False}, {"passed": True}]},
    {"attempts": [{"passed": False}, {"passed": False}, {"passed": False}]},
]
CHOICES = ("better", "worse", "can't tell")


def one_run_verdict(a, b):
    sa = sum(r["passed"] for r in a["results"])
    sb = sum(r["passed"] for r in b["results"])
    return "better" if sb > sa else "worse" if sb < sa else "can't tell"


class TestEx10(ExerciseCase):
    exercise = 10
    where = "exercises/ex10_luck_or_real.py"

    def setUp(self):
        self.mod = load("ex10_luck_or_real")

    def test_rates_on_a_small_example(self):
        self.assertEqual(self.call(self.mod.per_attempt_rate, FAKE), (5, 9))
        self.assertEqual(self.call(self.mod.every_attempt_rate, FAKE), (1, 3),
                         "only the first case passed on every attempt")

    def test_rates_on_a_real_repeated_run(self):
        candidate = load_candidate("sim-model-a")
        run = run_eval(candidate, subset(CORE, ["RC-001", "RC-002", "RC-021", "RC-022"]), repeat=5)
        attempts = [a["passed"] for r in run["results"] for a in r["attempts"]]
        self.assertEqual(self.call(self.mod.per_attempt_rate, run["results"]), (sum(attempts), len(attempts)))
        self.assertEqual(self.call(self.mod.every_attempt_rate, run["results"]),
                         (sum(r["passed"] for r in run["results"]), 4))

    def test_decision_matches_the_evidence(self):
        decision = self.mod.DECISION
        if "TODO" in repr(decision):
            self.not_done("fill in DECISION from the variance report")
        for key in ("b_vs_a_after_one_run", "b_vs_a_after_ten_runs", "c_vs_a_after_ten_runs"):
            self.assertIn(decision[key], CHOICES, f"{key} must be one of {CHOICES}")
        a = repeated_runs("sim-model-a", CORE, 10)
        b = repeated_runs("sim-model-b", CORE, 10)
        c = repeated_runs("sim-model-c", CORE, 10)
        self.assertEqual(decision["b_vs_a_after_one_run"], one_run_verdict(a[0], b[0]),
                         "compare the two seed-1 runs: CASES PASSED for each")
        self.assertEqual(decision["b_vs_a_after_ten_runs"], verdict(paired_difference(a, b)),
                         "read the '95% range for the real difference' line: does it include 0?")
        self.assertEqual(decision["c_vs_a_after_ten_runs"], verdict(paired_difference(a, c)))

    def test_who_was_wrong_on_rc002(self):
        answer = self.mod.DECISION["rc002_who_was_wrong"]
        if "TODO" in answer:
            self.not_done("read sim-model-a's RC-002 draft and decide who was wrong")
        self.assertEqual(answer, "check",
                         "the draft says the jacket can be sent back, in different words; the check only knows exact phrases")

    def test_explanation_written(self):
        text = self.mod.DECISION["why_one_run_is_not_enough"]
        if "TODO" in text:
            self.not_done("explain why one run isn't enough, in your own words")
        self.assertGreaterEqual(len(text.split()), 15, "write at least a couple of sentences")
