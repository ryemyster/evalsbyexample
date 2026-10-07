from returns_eval.cases import CASES_DIR, load_case_set, read_case_file
from returns_eval.grading import grade_case
from returns_eval.harness import produce

from ._support import REPO, ExerciseCase, load

CORE = load_case_set([CASES_DIR / "core.jsonl"]).cases
RC027 = read_case_file(REPO / "solutions" / "ex08_regression_case.jsonl")[0]


class TestEx09(ExerciseCase):
    exercise = 9
    where = "exercises/ex09_candidate_v3.py"

    def setUp(self):
        self.candidate = load("ex09_candidate_v3").CandidateV3()

    def _grade(self, case):
        result = grade_case(case, [produce(self.candidate, case)])
        error = result["attempts"][0]["error"]
        if error and "NotImplementedError" in error:
            self.not_done("implement CandidateV3._refund_amount()")
        return result

    def test_passes_the_regression_case(self):
        result = self._grade(RC027)
        failed = {c["check"]: c["evidence"] for c in result["attempts"][0]["checks"] if not c["passed"]}
        self.assertTrue(result["passed"], f"RC-027 still fails: {failed}")

    def test_still_passes_every_core_case(self):
        failing = [c["id"] for c in CORE if not self._grade(c)["passed"]]
        self.assertEqual(failing, [], "the fix broke cases that candidate-v2 passed; rerun and inspect them")
