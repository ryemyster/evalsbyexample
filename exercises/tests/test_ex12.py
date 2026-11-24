from returns_eval.labels import load_items
from returns_eval.stats import cohen_kappa as reference_kappa

from ._support import ExerciseCase, load

ITEMS = load_items()


def kappa_for(key):
    return round(reference_kappa([i[key]["annotator-a"] for i in ITEMS], [i[key]["annotator-b"] for i in ITEMS]), 2)


class TestEx12(ExerciseCase):
    exercise = 12
    where = "exercises/ex12_agreement_beyond_chance.py"

    def setUp(self):
        self.mod = load("ex12_agreement_beyond_chance")

    def test_kappa_small_examples(self):
        k = self.call(self.mod.cohen_kappa, [1, 1, 0, 0], [1, 0, 0, 0])
        self.assertAlmostEqual(k, 0.5, places=6)
        self.assertAlmostEqual(self.call(self.mod.cohen_kappa, ["ok", "problem"], ["ok", "problem"]), 1.0, places=6)
        self.assertIsNone(self.call(self.mod.cohen_kappa, ["ok"] * 4, ["ok"] * 4),
                          "when both raters only ever used one label, return None")

    def test_kappa_on_the_labels(self):
        for key in ("first_rubric_labels", "labels"):
            a = [i[key]["annotator-a"] for i in ITEMS]
            b = [i[key]["annotator-b"] for i in ITEMS]
            self.assertAlmostEqual(self.call(self.mod.cohen_kappa, a, b), reference_kappa(a, b), places=6)

    def test_decision(self):
        d = self.mod.DECISION
        if "TODO" in repr(d):
            self.not_done("fill in DECISION from the labels and review-summary commands")
        self.assertAlmostEqual(float(d["first_rubric_kappa"]), kappa_for("first_rubric_labels"), delta=0.011)
        self.assertAlmostEqual(float(d["clear_rubric_kappa"]), kappa_for("labels"), delta=0.011)
        self.assertEqual(d["calibrate_against"], "clear rubric labels",
                         "a judge can only be as good as the labels you check it against")
        self.assertGreaterEqual(len(d["why_tone_review_kappa_is_zero"].split()), 15, "explain it in a few sentences")
