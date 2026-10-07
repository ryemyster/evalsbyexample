import copy
import unittest
from pathlib import Path

from returns_eval import gates, human_review
from returns_eval.candidates import load_candidate
from returns_eval.cases import DATA_DIR
from returns_eval.harness import run_eval

from .helpers import CORE

BASE = run_eval(load_candidate("baseline"), CORE)
V1 = run_eval(load_candidate("candidate-v1"), CORE)
V2 = run_eval(load_candidate("candidate-v2"), CORE)
REVIEWS = sorted((DATA_DIR / "human_review").glob("*.csv"))


def review_of(run):
    rows, problems = human_review.load_reviews(REVIEWS)
    assert not problems, problems
    return human_review.summarize(run, rows)


class TestGates(unittest.TestCase):
    def test_v1_blocked_by_criticals(self):
        decision = gates.evaluate(V1, BASE)
        self.assertEqual(decision.status, gates.BLOCKED)
        self.assertEqual({g.id: g.status for g in decision.gates}["G4"], "fail")

    def test_one_critical_blocks_an_otherwise_perfect_run(self):
        run = copy.deepcopy(V2)
        run["results"][0]["worst_severity"] = "critical"  # pretend one critical slipped in
        decision = gates.evaluate(run, BASE, review_of(V2))
        self.assertEqual(decision.status, gates.BLOCKED)

    def test_v2_pending_without_review_then_ready(self):
        self.assertEqual(gates.evaluate(V2, BASE).status, gates.PENDING)
        self.assertEqual(gates.evaluate(V2, BASE, review_of(V2)).status, gates.READY)

    def test_category_regression_needs_a_baseline(self):
        decision = gates.evaluate(V2, None, review_of(V2))
        self.assertEqual({g.id: g.status for g in decision.gates}["G4"], "pending")


class TestHumanReview(unittest.TestCase):
    def test_illustrative_reviews_match_current_v2_drafts(self):
        summary = review_of(V2)
        self.assertTrue(summary.complete, f"stale: {summary.stale}, unreviewed: {summary.unreviewed}")
        self.assertTrue(summary.illustrative)

    def test_reviews_go_stale_when_drafts_change(self):
        run = copy.deepcopy(V2)
        run["results"][0]["attempts"][0]["draft"]["fingerprint"] = "changed"
        summary = review_of(run)
        self.assertEqual(summary.stale, [run["results"][0]["case_id"]])
        self.assertFalse(summary.complete)

    def test_agreement(self):
        summary = review_of(V2)
        self.assertEqual(summary.agreement[("reviewer-a", "reviewer-b")]["usability"], (23, 26))

    def test_export_and_reload_blank_sheet(self):
        import tempfile
        cases = {c["id"]: c for c in CORE.cases}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sheet.csv"
            self.assertEqual(human_review.export_sheet(V2, cases, path, "me"), 26)
            rows, problems = human_review.load_reviews([path])
            self.assertEqual((rows, problems), ([], []))  # blank rows are "not reviewed yet"


if __name__ == "__main__":
    unittest.main()
