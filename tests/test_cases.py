import json
import unittest

from returns_eval.cases import CASE_CATEGORIES, MANIFEST, load_case_set, validate_case

from .helpers import CORE


class TestCaseSet(unittest.TestCase):
    def test_default_set_loads_and_validates(self):
        cs = load_case_set()
        self.assertGreaterEqual(len(cs.cases), 20)
        self.assertEqual(cs.version, json.loads(MANIFEST.read_text())["version"])

    def test_every_category_is_covered(self):
        present = {c["category"] for c in CORE.cases}
        self.assertEqual(present, set(CASE_CATEGORIES))

    def test_all_people_are_fictional(self):
        for case in CORE.cases:
            self.assertTrue(case["customer"]["email"].endswith("@example.com"))
            for order in case["orders"]:
                self.assertTrue(order["customer_email"].endswith("@example.com"))

    def test_order_ids_unique_across_cases(self):
        ids = [o["order_id"] for c in CORE.cases for o in c["orders"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_validator_reports_problems_in_plain_language(self):
        case = json.loads(json.dumps(CORE.cases[0]))
        case["category"] = "nonsense"
        case["expected"]["target_order_id"] = "EO-99999"
        problems = validate_case(case)
        self.assertTrue(any("'category' must be one of" in p for p in problems))
        self.assertTrue(any("target_order_id" in p for p in problems))

    def test_sha_changes_when_a_case_changes(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            edited = json.loads(json.dumps(CORE.cases[0]))
            edited["message"] += " Thanks!"
            path = Path(tmp) / "one.jsonl"
            path.write_text(json.dumps(edited) + "\n")
            original = Path(tmp) / "orig.jsonl"
            original.write_text(json.dumps(CORE.cases[0]) + "\n")
            self.assertNotEqual(load_case_set([path]).sha256, load_case_set([original]).sha256)


if __name__ == "__main__":
    unittest.main()
