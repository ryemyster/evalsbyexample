from ._support import ExerciseCase, load


def s(**overrides):
    base = {"cases": 26, "passed": 26, "critical_failures": 0, "must_pass_failed": 0,
            "min_pass_rate": 0.9, "human_review_complete": True}
    return {**base, **overrides}


class TestEx06(ExerciseCase):
    exercise = 6
    where = "exercises/ex06_release_decision.py"

    def setUp(self):
        self.decide = load("ex06_release_decision").release_decision

    def test_all_good(self):
        self.assertEqual(self.call(self.decide, s()), "READY")

    def test_one_critical_blocks_a_great_score(self):
        self.assertEqual(self.call(self.decide, s(passed=999, cases=1000, critical_failures=1)), "BLOCKED",
                         "999 of 1000 passing does not outweigh one unauthorized refund")

    def test_critical_blocks_even_when_review_is_incomplete(self):
        self.assertEqual(self.call(self.decide, s(critical_failures=2, human_review_complete=False)), "BLOCKED")

    def test_low_pass_rate(self):
        self.assertEqual(self.call(self.decide, s(passed=13)), "NOT READY")

    def test_must_pass_failure(self):
        self.assertEqual(self.call(self.decide, s(passed=25, must_pass_failed=1)), "NOT READY")

    def test_human_review_pending(self):
        self.assertEqual(self.call(self.decide, s(human_review_complete=False)), "PENDING")

    def test_threshold_is_inclusive(self):
        self.assertEqual(self.call(self.decide, s(cases=10, passed=9)), "READY", "9/10 meets a 0.9 threshold")
