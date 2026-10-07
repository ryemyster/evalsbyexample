import csv

from ._support import REPO, ExerciseCase, load

A = [
    {"case_id": "RC-001", "draft_fingerprint": "aaa", "usability": "send_as_is"},
    {"case_id": "RC-002", "draft_fingerprint": "bbb", "usability": "minor_edits"},
    {"case_id": "RC-003", "draft_fingerprint": "ccc", "usability": "major_rewrite"},
    {"case_id": "RC-004", "draft_fingerprint": "ddd", "usability": "send_as_is"},
]
B = [
    {"case_id": "RC-001", "draft_fingerprint": "aaa", "usability": "send_as_is"},
    {"case_id": "RC-002", "draft_fingerprint": "bbb", "usability": "send_as_is"},
    {"case_id": "RC-003", "draft_fingerprint": "OLD", "usability": "major_rewrite"},  # older draft: skip
    # RC-004 not reviewed by B: skip
]


def _read(name):
    with (REPO / "data" / "human_review" / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class TestEx04(ExerciseCase):
    exercise = 4
    where = "exercises/ex04_reviewer_agreement.py"

    def setUp(self):
        self.mod = load("ex04_reviewer_agreement")

    def test_agreement_counts_only_matching_drafts(self):
        self.assertEqual(self.call(self.mod.percent_agreement, A, B, "usability"), (1, 2),
                         "RC-003 has a different fingerprint and RC-004 was rated by only one reviewer; "
                         "expected 1 agreement out of 2 comparable drafts")

    def test_disagreements(self):
        self.assertEqual(self.call(self.mod.disagreements, A, B, "usability"), ["RC-002"])

    def test_no_overlap(self):
        self.assertEqual(self.call(self.mod.percent_agreement, A, [], "usability"), (0, 0))

    def test_illustrative_scorecards(self):
        a = _read("candidate-v2.reviewer-a.ILLUSTRATIVE.csv")
        b = _read("candidate-v2.reviewer-b.ILLUSTRATIVE.csv")
        self.assertEqual(self.call(self.mod.percent_agreement, a, b, "usability"), (23, 26))
        self.assertEqual(self.call(self.mod.disagreements, a, b, "policy_interpretation"), ["RC-017"])
