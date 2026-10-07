import itertools
import time
import unittest

from returns_eval import brief, gates
from returns_eval.candidates import load_candidate
from returns_eval.candidates.candidate_v2 import CandidateV2
from returns_eval.harness import run_eval
from returns_eval.report import measures

from .helpers import CORE

BASE = run_eval(load_candidate("baseline"), CORE)
V1 = run_eval(load_candidate("candidate-v1"), CORE)
V2 = run_eval(load_candidate("candidate-v2"), CORE)


class Flaky(CandidateV2):
    """Escalates every other call, so repeated attempts disagree."""
    name = "flaky"
    _calls = itertools.count()

    def draft_reply(self, request, tools):
        draft = super().draft_reply(request, tools)
        if next(self._calls) % 2:
            draft.resolution = "escalate"
        return draft


class Slow(CandidateV2):
    name = "slow"

    def draft_reply(self, request, tools):
        time.sleep(0.11)
        return super().draft_reply(request, tools)


class TestMeasures(unittest.TestCase):
    def test_escalation_recall(self):
        self.assertEqual(measures(BASE["results"])["Escalation recall"], "2 / 6 (33%)")
        self.assertEqual(measures(V1["results"])["Escalation recall"], "2 / 6 (33%)")
        self.assertEqual(measures(V2["results"])["Escalation recall"], "6 / 6 (100%)")

    def test_reliability_only_with_repeats(self):
        self.assertNotIn("Reliability (same result every attempt)", measures(V2["results"]))
        flaky = run_eval(Flaky(), CORE, repeat=2)
        reliability = measures(flaky["results"])["Reliability (same result every attempt)"]
        self.assertTrue(reliability.startswith(tuple(f"{n} / 26" for n in range(26))), reliability)

    def test_draft_time_only_when_slow(self):
        self.assertNotIn("p95 draft time", measures(V2["results"]))
        from returns_eval.cases import subset
        slow = run_eval(Slow(), subset(CORE, ["RC-001", "RC-002"]))
        self.assertIn("p95 draft time", measures(slow["results"]))


class TestBrief(unittest.TestCase):
    def test_blocked_brief_shows_evidence_and_leaves_pm_sections(self):
        text = brief.build(BASE, V1, gates.evaluate(V1, BASE))
        for part in ("**BLOCKED.**", "| Cases with a critical failure | 0 / 26 (0%) | 5 / 26 (19%) |",
                     "unauthorized_action", "## Why now", "_name_", "## Stop and rollback conditions"):
            self.assertIn(part, text)
        self.assertNotIn("ILLUSTRATIVE", text)


if __name__ == "__main__":
    unittest.main()
