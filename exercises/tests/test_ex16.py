from returns_eval.production import LAYERS, load_traces, specialist_routed

from ._support import ExerciseCase, load

TRACES = {t["trace_id"]: t for t in load_traces()}
ANSWERS = {  # each trace's acceptable answers
    "T-105": [{"orchestration"}],
    "T-109": [{"policy"}, {"orchestration"}, {"policy", "orchestration"}],
    "T-112": [{"data"}],
    "T-115": [{"evaluator"}],
    "T-120": [{"human_review"}],
    "T-124": [{"model"}],
    "T-203": [{"model", "orchestration"}],
}
HINTS = {
    "T-105": "read the send step and the note: the draft was fine",
    "T-109": "compare the policy version with the order date",
    "T-112": "the draft did the right thing with the record it had",
    "T-115": "look at the judge step: status and recorded_as",
    "T-120": "the judge flagged it; what happened next?",
    "T-124": "every step ran; which one chose the wrong next step?",
    "T-203": "two things went wrong: no draft arrived, and the ticket still went to the general queue",
}


class TestEx16(ExerciseCase):
    exercise = 16
    where = "exercises/ex16_failure_attribution.py"

    def setUp(self):
        self.mod = load("ex16_failure_attribution")

    def test_specialist_routed(self):
        for tid, t in TRACES.items():
            expected = not t["needed_specialist"] or any(s["step"] == "route" and s["queue"] == "specialist"
                                                         for s in t["steps"])
            self.assertEqual(self.call(self.mod.specialist_routed, t), expected, tid)
        self.assertEqual(self.call(specialist_routed, TRACES["T-203"]), False)

    def test_attribution(self):
        a = self.mod.ATTRIBUTION
        if "TODO" in repr(a):
            self.not_done("attribute every trace to a layer")
        for tid, acceptable in ANSWERS.items():
            given = set(a[tid]) if isinstance(a[tid], (list, tuple, set)) else {a[tid]}
            self.assertTrue(given <= set(LAYERS), f"{tid}: use the layer names {LAYERS}")
            self.assertIn(given, acceptable, f"{tid}: {HINTS[tid]}")

    def test_which_become_offline_cases(self):
        if "TODO" in repr(self.mod.NEW_OFFLINE_CASES):
            self.not_done("decide which traces become offline cases")
        self.assertEqual(set(self.mod.NEW_OFFLINE_CASES), {"T-124", "T-203"},
                         "an offline case tests the model on an input; routing, data, policy, and review failures "
                         "need fixes and tests in those systems instead")

    def test_t122_explained(self):
        if "TODO" in self.mod.T122:
            self.not_done("explain T-122")
        self.assertGreaterEqual(len(self.mod.T122.split()), 12)
