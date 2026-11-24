from returns_eval.cases import load_case_set
from returns_eval.judging import load_judge, with_case_context
from returns_eval.labels import load_items
from returns_eval.stats import confusion as reference_confusion

from ._support import ExerciseCase, load

CASES = {c["id"]: c for c in load_case_set().cases}
SEGMENTS = {"accept_return", "decline_return", "escalate", "inform", "ask_customer"}


def reaches_people(decision, split):
    """For the chosen setup on a split: (problems a person ends up seeing, problems, problems nobody sees)."""
    items = with_case_context(load_items(split=split), CASES)
    judge = load_judge(decision["judge"])
    threshold = decision["send_to_people_below_confidence"]
    seen, unseen = 0, []
    for item in items:
        if item["final"] != "problem":
            continue
        v = judge.pointwise(item)
        sent = (v["verdict"] == "problem"
                or (threshold is not None and v["confidence"] is not None and v["confidence"] < threshold)
                or item["segment"] in decision["people_always_review"]
                or decision["use"] == "triage")
        if sent:
            seen += 1
        else:
            unseen.append(f"{item['item_id']} ({item['segment']})")
    total = sum(i["final"] == "problem" for i in items)
    return seen, total, unseen


class TestEx14(ExerciseCase):
    exercise = 14
    where = "exercises/ex14_judge_fitness.py"

    def setUp(self):
        self.mod = load("ex14_judge_fitness")

    def test_confusion_and_rates(self):
        truth = ["problem", "problem", "ok", "ok", "ok"]
        said = ["problem", "ok", "problem", "ok", "ok"]
        cm = self.call(self.mod.confusion, truth, said)
        self.assertEqual(cm, reference_confusion(truth, said, "problem"))
        self.assertEqual(self.call(self.mod.recall_precision, cm), (0.5, 0.5))
        self.assertEqual(self.call(self.mod.recall_precision, {"tp": 0, "fn": 0, "fp": 0, "tn": 4}), (None, None))

    def test_decision_is_complete(self):
        d = self.mod.DECISION
        if "TODO" in repr(d):
            self.not_done("fill in DECISION after running calibrate on the calibration split")
        self.assertIn(d["use"], ("auto-pass", "triage"))
        self.assertIn(d["judge"], ("judge-a", "judge-b"))
        self.assertIn(d["worse_mistake"], ("missed problem", "false alarm"))
        self.assertTrue(isinstance(d["min_recall"], (int, float)) and 0 < d["min_recall"] <= 1)
        t = d["send_to_people_below_confidence"]
        self.assertTrue(t is None or (isinstance(t, (int, float)) and 0 < t <= 1))
        self.assertTrue(set(d["people_always_review"]) <= SEGMENTS, f"segments are: {sorted(SEGMENTS)}")
        self.assertGreaterEqual(len(d["why"].split()), 25, "give your reasons, pointing at numbers you saw")

    def test_decision_holds_on_the_calibration_split(self):
        d = self.mod.DECISION
        if "TODO" in repr(d):
            self.not_done("fill in DECISION")
        if d["use"] == "auto-pass" and d["worse_mistake"] != "missed problem":
            self.fail("if passed drafts skip a person, a missed problem goes to a customer. Is a false alarm really worse?")
        seen, total, unseen = reaches_people(d, "calibration")
        self.assertGreaterEqual(seen / total, d["min_recall"],
                                f"on the calibration split only {seen} of {total} problems reach a person with this "
                                f"setup; nobody sees {', '.join(unseen)}. Change the judge, the confidence rule, "
                                "or the segments people always review")

    def test_holdout_answer_matches(self):
        d = self.mod.DECISION
        if "TODO" in repr(d):
            self.not_done("fill in DECISION")
        seen, total, _ = reaches_people(d, "holdout")
        expected = "yes" if seen / total >= d["min_recall"] else "no"
        self.assertEqual(d["holdout_confirms"], expected,
                         f"on the holdout split, {seen} of {total} problems reach a person with your setup")
