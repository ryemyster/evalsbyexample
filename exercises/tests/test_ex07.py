import csv

from returns_eval.pilot import PILOT_FILE

from ._support import ExerciseCase, load

with PILOT_FILE.open(newline="", encoding="utf-8") as fh:
    ROWS = list(csv.DictReader(fh))


class TestEx07(ExerciseCase):
    exercise = 7
    where = "exercises/ex07_pilot_outcomes.py"

    def setUp(self):
        self.mod = load("ex07_pilot_outcomes")

    def test_overall_medians(self):
        self.assertEqual(self.call(self.mod.median_minutes, ROWS, "manual"), (9.5, 20))
        self.assertEqual(self.call(self.mod.median_minutes, ROWS, "assisted"), (6.5, 20))

    def test_escalations_got_slower(self):
        manual = self.call(self.mod.median_minutes, ROWS, "manual", "escalation")
        assisted = self.call(self.mod.median_minutes, ROWS, "assisted", "escalation")
        self.assertEqual((manual, assisted), ((12.5, 4), (14.5, 4)),
                         "the overall median hides that escalations took longer with drafts")

    def test_rates(self):
        self.assertEqual(self.call(self.mod.rate, ROWS, "manual", "reopened_within_7_days", "yes"), (2, 20))
        self.assertEqual(self.call(self.mod.rate, ROWS, "assisted", "reopened_within_7_days", "yes"), (3, 20))
        self.assertEqual(self.call(self.mod.rate, ROWS, "assisted", "draft_outcome", "used_as_is"), (9, 20))

    def test_explanation_written(self):
        text = self.mod.WHY_OFFLINE_IS_NOT_ENOUGH
        if "TODO" in text:
            self.not_done("write WHY_OFFLINE_IS_NOT_ENOUGH in your own words")
        self.assertGreaterEqual(len(text.split()), 20, "write at least two sentences")
