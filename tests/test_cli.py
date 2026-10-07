import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def cli(*args, module="returns_eval", env=None):
    proc = subprocess.run([sys.executable, "-m", module, *args], cwd=REPO, capture_output=True, text=True,
                          env={**os.environ, **(env or {})})
    return proc.returncode, proc.stdout + proc.stderr


class TestCLI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = cls.tmp.name
        cls.runs = {}
        for name in ("baseline", "candidate-v1", "candidate-v2"):
            code, text = cli("run", "--candidate", name, "--out", cls.out, "--cases", "data/cases/core.jsonl")
            assert code == 0, text
            cls.runs[name] = re.search(r"^Saved (.+\.json)$", text, re.M).group(1)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_help_and_listing(self):
        for args in (["--help"], ["cases"], ["cases", "--category", "escalation"], ["show-case", "RC-001"], ["candidates"]):
            code, text = cli(*args)
            self.assertEqual(code, 0, text)
        self.assertIn("RC-026", cli("cases")[1])

    def test_run_v1_shows_blocked_with_counts(self):
        code, text = cli("report", self.runs["candidate-v1"])
        self.assertEqual(code, 0, text)
        self.assertIn("CASES PASSED: 13 / 26 (50%)", text)
        self.assertIn("Critical failures: 5", text)

    def test_case_detail(self):
        code, text = cli("report", self.runs["candidate-v1"], "--case", "RC-001")
        self.assertEqual(code, 0, text)
        for part in ("WHAT A GOOD REPLY DOES", "WHAT IT LOOKED UP", "refund_commitment", "RESULT: FAIL (worst severity: critical)"):
            self.assertIn(part, text)

    def test_gate_exit_codes(self):
        self.assertEqual(cli("gate", self.runs["candidate-v1"], "--baseline", self.runs["baseline"])[0], 1)
        code, text = cli("gate", self.runs["candidate-v2"], "--baseline", self.runs["baseline"],
                         "--review", "data/human_review/candidate-v2.reviewer-a.ILLUSTRATIVE.csv",
                         "data/human_review/candidate-v2.reviewer-b.ILLUSTRATIVE.csv")
        self.assertEqual(code, 0, text)
        self.assertIn("READY FOR A SUPERVISED PILOT", text)

    def test_compare_saved_runs(self):
        code, text = cli("compare", self.runs["baseline"], self.runs["candidate-v1"])
        self.assertEqual(code, 0, text)
        self.assertIn("newly failing (2): RC-024 [critical], RC-025 [critical]", text)

    def test_compare_refuses_mismatched_case_sets(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, text = cli("run", "--candidate", "baseline", "--out", tmp, "--cases", "solutions/ex02_new_case.json")
            other = re.search(r"^Saved (.+\.json)$", text, re.M).group(1)
            code, text = cli("compare", other, self.runs["candidate-v1"])
            self.assertEqual(code, 2)
            self.assertIn("different case sets", text)

    def test_review_sheet_and_summary(self):
        sheet = Path(self.out) / "sheet.csv"
        code, text = cli("review-sheet", self.runs["candidate-v2"], "--out", str(sheet), "--reviewer", "me")
        self.assertEqual(code, 0, text)
        self.assertTrue(sheet.exists())
        code, text = cli("review-summary", self.runs["candidate-v2"], "data/human_review/candidate-v2.reviewer-a.ILLUSTRATIVE.csv",
                         "data/human_review/candidate-v2.reviewer-b.ILLUSTRATIVE.csv")
        self.assertEqual(code, 0, text)
        self.assertIn("ILLUSTRATIVE", text)

    def test_pilot_is_labeled_illustrative(self):
        code, text = cli("pilot")
        self.assertEqual(code, 0, text)
        self.assertTrue(text.startswith("ILLUSTRATIVE DATA"))

    def test_repeat(self):
        code, text = cli("run", "--candidate", "candidate-v2", "--repeat", "2", "--out", self.out,
                         "--cases", "data/cases/core.jsonl")
        self.assertEqual(code, 0, text)
        self.assertIn("repeat 2", text)

    def test_add_case_rejects_invalid(self):
        code, text = cli("add-case", "exercises/ex02_new_case.json", "--to", str(Path(self.out) / "x.jsonl"))
        self.assertEqual(code, 1)
        self.assertIn("Not added", text)


class TestExercises(unittest.TestCase):
    """Stubs must fail with a helpful message; reference solutions must pass."""

    def test_solutions_pass(self):
        code, text = cli("all", "--solution", module="exercises")
        self.assertEqual(code, 0, text)

    def test_exercise_runner_never_crashes(self):
        # Unfinished exercises fail with a message, finished ones pass; neither should crash.
        code, text = cli("all", module="exercises")
        self.assertIn(code, (0, 1), text)
        for n in range(1, 10):
            self.assertIn(f"Exercise {n}:", text)
        self.assertNotIn("Traceback", text)


if __name__ == "__main__":
    unittest.main()
