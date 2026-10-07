import json

from returns_eval.candidates import load_candidate
from returns_eval.cases import CASES_DIR, MANIFEST, read_case_file, validate_case
from returns_eval.grading import grade_case
from returns_eval.harness import produce

from ._support import REPO, ExerciseCase, using_solutions

HOW = ("fill in exercises/ex08_regression_case.json, then run: "
       "python3 -m returns_eval add-case exercises/ex08_regression_case.json")


class TestEx08(ExerciseCase):
    exercise = 8
    where = "exercises/ex08_regression_case.json and data/cases/manifest.json"

    def setUp(self):
        source = REPO / "solutions" / "ex08_regression_case.jsonl" if using_solutions() else CASES_DIR / "regressions.jsonl"
        found = [c for c in read_case_file(source) if c.get("id") == "RC-027"]
        if not found:
            self.not_done(f"RC-027 is not in {source.relative_to(REPO)} yet; {HOW}")
        self.case = found[0]

    def test_case_is_valid(self):
        self.assertEqual(validate_case(self.case), [], "the regression case does not validate")

    def test_expected_behavior_targets_the_incident(self):
        exp = self.case["expected"]
        self.assertEqual(exp["acceptable_resolutions"], ["accept_return"], "returning one item in the window is allowed")
        self.assertEqual(exp["target_order_id"], "EO-10927")
        mentions = [p for group in exp["must_mention"] for p in group]
        self.assertIn("$38.00", mentions, "require the pillow's price, so a correct draft has to state it")
        self.assertIn("$134.00", exp["must_not_mention"], "rule out the order total that the pilot draft quoted")

    def test_regression_case_is_must_pass(self):
        self.assertTrue(self.case["must_pass"],
                        "set must_pass to true: a case written for a real incident should block release "
                        "if it fails, not get averaged in with everything else")

    def test_case_catches_the_bug(self):
        result = grade_case(self.case, [produce(load_candidate("candidate-v2"), self.case)])
        self.assertFalse(result["passed"],
                         "candidate-v2 should FAIL this case. If it passes, the case does not capture the incident.")

    def test_case_set_version_bumped(self):
        if using_solutions():
            self.skipTest("the solution case lives in solutions/, so the manifest isn't changed")
        version = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
        self.assertNotEqual(version, "1.0", "you changed the case set; bump 'version' in data/cases/manifest.json (e.g. to 1.1)")
