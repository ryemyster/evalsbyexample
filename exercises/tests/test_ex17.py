import re

from returns_eval.cases import load_case_set
from returns_eval.cli import build_parser
from returns_eval.labels import load_items
from returns_eval.production import load_traces

from ._support import REPO, ExerciseCase, file_path

KNOWN = ({c["id"] for c in load_case_set().cases} | {"RC-027"} | {t["trace_id"] for t in load_traces()}
         | {i["item_id"] for i in load_items()})
COMMANDS = set(build_parser()._subparsers._group_actions[0].choices)
SECTIONS = 12


class TestEx17(ExerciseCase):
    exercise = 17
    where = "exercises/ex17_capstone_decision.md"

    def setUp(self):
        self.text = file_path("ex17_capstone_decision.md").read_text(encoding="utf-8")
        parts = re.split(r"^## (\d+)\. .*$", self.text, flags=re.M)
        self.sections = {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}

    def test_every_section_is_written(self):
        self.assertEqual(sorted(self.sections), list(range(1, SECTIONS + 1)), "keep the 12 numbered sections")
        todo = [n for n, body in self.sections.items() if "TODO" in body]
        if todo:
            self.not_done(f"sections still marked TODO: {todo}")
        thin = [n for n, body in self.sections.items() if len(body.split()) < 20]
        self.assertEqual(thin, [], "write at least a couple of sentences in each section")

    def test_claims_point_at_evidence(self):
        ids = set(re.findall(r"\b(?:RC|T|L)-\d{3}\b", self.text))
        unknown = sorted(ids - KNOWN)
        self.assertEqual(unknown, [], "these ids don't exist in the cases, traces, or labels")
        used = set(re.findall(r"returns_eval ([a-z][a-z-]*)", self.text)) & COMMANDS
        self.assertGreaterEqual(len(ids) + len(used), 8,
                                "point at evidence: cases (RC-...), traces (T-...), labeled drafts (L-...), commands")

    def test_decision(self):
        m = re.search(r"^Decision:\s*(\w+)", self.sections.get(12, ""), flags=re.M | re.I)
        if not m or m.group(1).lower() == "todo":
            self.not_done("write 'Decision: ship', 'hold', or 'rollback' in section 12")
        decision = m.group(1).lower()
        self.assertIn(decision, ("ship", "hold", "rollback"))
        self.assertNotEqual(decision, "ship", "look past the single run: repeated runs, and the canary traces")
        self.assertRegex(self.text, r"\bR1\b", "a rollback trigger agreed in advance fired; say what you do about it")
