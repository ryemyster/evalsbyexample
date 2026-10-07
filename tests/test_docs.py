"""Keep the docs honest: every field, check, and command in code is documented."""

import re
import unittest
from pathlib import Path

from returns_eval.cases import CASE_CATEGORIES, CASE_FIELDS, CUSTOMER_FIELDS, EXPECTED_FIELDS, ITEM_FIELDS, ORDER_FIELDS
from returns_eval.cli import build_parser
from returns_eval.grading import SEVERITY
from returns_eval.human_review import CRITERIA

REPO = Path(__file__).resolve().parent.parent
CASE_DOC = (REPO / "docs" / "case-format.md").read_text()
GRADING_DOC = (REPO / "docs" / "grading.md").read_text()
README = (REPO / "README.md").read_text()
START = (REPO / "START_HERE.md").read_text()
TUTOR = (REPO / "TUTOR.md").read_text()
ALL_DOCS = {p.relative_to(REPO): p.read_text() for p in [*REPO.glob("*.md"), *REPO.glob("docs/*.md"),
                                                          *REPO.glob("exercises/*.md"), *REPO.glob("data/*/*.md")]}


class TestDocs(unittest.TestCase):
    def test_every_case_field_documented(self):
        fields = CASE_FIELDS | CUSTOMER_FIELDS | EXPECTED_FIELDS | ITEM_FIELDS | (ORDER_FIELDS - {"return", "refund"})
        fields |= {"label_issued_on", "shipped_on", "received_on", "inspection.status", "inspection.completed_on",
                   "status", "amount", "issued_on"}
        missing = sorted(f for f in fields if f"| `{f}` |" not in CASE_DOC)
        self.assertEqual(missing, [], "add these fields to docs/case-format.md")

    def test_every_category_documented(self):
        self.assertEqual([c for c in CASE_CATEGORIES if f"| `{c}` |" not in CASE_DOC], [])

    def test_every_check_and_review_criterion_documented(self):
        self.assertEqual([c for c in SEVERITY if f"| `{c}` | {SEVERITY[c]} |" not in GRADING_DOC], [])
        self.assertEqual([c for c in CRITERIA if f"| `{c}` |" not in GRADING_DOC], [])

    def test_every_cli_command_in_readme(self):
        commands = build_parser()._subparsers._group_actions[0].choices
        self.assertEqual([c for c in commands if not re.search(rf"returns_eval {re.escape(c)}\b", README)], [])

    def test_every_command_mentioned_in_docs_exists(self):
        commands = set(build_parser()._subparsers._group_actions[0].choices)
        for path, text in ALL_DOCS.items():
            for cmd in re.findall(r"(?:python3|PY|py) -m returns_eval ([a-z][a-z-]*)", text):
                self.assertIn(cmd, commands, f"{path} mentions 'returns_eval {cmd}', which is not a command")
            for n in re.findall(r"(?:python3|PY|py) -m exercises (\w+)", text):
                self.assertTrue(n == "all" or n.isdigit() and 1 <= int(n) <= 9, f"{path}: 'exercises {n}'")

    def test_onboarding_prompt_is_the_same_everywhere(self):
        prompt = re.search(r"```text\n(I'm a product manager.*?)```", START, re.S).group(1)
        self.assertIn(prompt, README, "README.md and START_HERE.md must show the same prompt")
        self.assertIn("TUTOR.md", prompt)

    def test_files_the_tutor_points_to_exist(self):
        for ref in sorted(set(re.findall(r"`((?:docs|data|exercises|playground|returns_eval)/[\w./-]+\.\w+)`", TUTOR))):
            if ref == "playground/my_notes.md":
                continue  # created during the course
            self.assertTrue((REPO / ref).exists(), f"TUTOR.md mentions {ref}, which doesn't exist")
        for link in re.findall(r"\]\(([\w./-]+\.md)\)", TUTOR + START):
            self.assertTrue((REPO / link).exists(), f"broken link: {link}")

    def test_agents_auto_load_the_tutor(self):
        agents = (REPO / "AGENTS.md").read_text()
        self.assertIn("TUTOR.md", agents)
        claude = (REPO / "CLAUDE.md").read_text().split()
        self.assertEqual(claude, ["@AGENTS.md", "@TUTOR.md"], "CLAUDE.md should only import AGENTS.md and TUTOR.md")
        self.assertIn("## Starting a session", TUTOR)
        self.assertIn("Let's learn evals together", TUTOR)

    def test_illustrative_labels(self):
        for path in (REPO / "data" / "pilot").iterdir():
            if path.suffix in (".csv", ".jsonl"):
                self.assertIn("ILLUSTRATIVE", path.name)
        for path in (REPO / "data" / "human_review").glob("*.csv"):
            self.assertIn("ILLUSTRATIVE", path.name)


if __name__ == "__main__":
    unittest.main()
