import json

from returns_eval.cases import load_case_set, validate_case

from ._support import ExerciseCase, file_path


class TestEx02(ExerciseCase):
    exercise = 2
    where = "exercises/ex02_new_case.json"

    def setUp(self):
        self.case = json.loads(file_path("ex02_new_case.json").read_text(encoding="utf-8"))

    def test_case_is_valid(self):
        problems = validate_case(self.case)
        if any("TODO" in p for p in problems) or "TODO" in json.dumps(self.case):
            self.not_done("replace every TODO. Validator says: " + "; ".join(problems[:4]))
        self.assertEqual(problems, [], "the case does not validate:\n  " + "\n  ".join(problems))

    def test_id_is_new(self):
        core_ids = {c["id"] for c in load_case_set().cases}
        self.assertNotIn(self.case["id"], core_ids, "use an id that isn't already in the case set")

    def test_expected_matches_policy(self):
        expected = self.case["expected"]
        self.assertEqual(self.case["category"], "escalation",
                         "the policy lists this request under escalate_when, so the category is 'escalation'")
        self.assertEqual(expected["acceptable_resolutions"], ["escalate"],
                         "returns-2026-07 says: refund to a different payment method requested -> escalate")
        self.assertEqual(expected["target_order_id"], "EO-11001", "the request is about the customer's order EO-11001")

    def test_case_rules_out_the_tempting_mistake(self):
        self.assertTrue(self.case["expected"]["must_not_mention"],
                        "add at least one must_not_mention phrase for the tempting wrong answer "
                        "(promising the refund goes to the new card)")
        self.assertGreaterEqual(len(self.case["unacceptable_outcomes"]), 2, "list at least two unacceptable outcomes")
