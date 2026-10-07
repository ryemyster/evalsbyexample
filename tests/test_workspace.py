"""reset and clean, tested in a throwaway git clone so this folder is never touched."""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HAS_GIT = shutil.which("git") is not None


def sh(cwd, *args):
    return subprocess.run(list(args), cwd=cwd, capture_output=True, text=True)


@unittest.skipUnless(HAS_GIT, "git is not installed")
class TestReset(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        shutil.copytree(REPO, self.root, ignore=shutil.ignore_patterns(".git", "__pycache__", "backups", "*.json.bak"))
        for f in (self.root / "runs").iterdir():
            if f.name != ".gitkeep":
                f.unlink()
        for args in (["git", "init", "-q"], ["git", "add", "-A"],
                     ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qm", "start"]):
            self.assertEqual(sh(self.root, *args).returncode, 0)

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args):
        return sh(self.root, sys.executable, "-m", "returns_eval", *args)

    def test_report_then_reset_restores_and_backs_up(self):
        ex = self.root / "exercises" / "ex03_refund_timing_check.py"
        original = ex.read_text()
        ex.write_text(original + "\n# my attempt\n")
        (self.root / "playground" / "idea.py").write_text("x = 1\n")
        regressions = self.root / "data" / "cases" / "regressions.jsonl"
        regressions.write_text(regressions.read_text() + "\n")  # any change (blank lines are ignored)

        report = self.cli("reset").stdout
        for name in ("exercises/ex03_refund_timing_check.py", "playground/idea.py", "data/cases/regressions.jsonl"):
            self.assertIn(name, report)
        self.assertEqual(ex.read_text(), original + "\n# my attempt\n", "a report must not change anything")

        refused = self.cli("reset", "--all")  # not interactive and no --yes
        self.assertEqual(refused.returncode, 1)

        done = self.cli("reset", "--all", "--yes")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(ex.read_text(), original)
        self.assertFalse((self.root / "playground" / "idea.py").exists())
        self.assertEqual(sh(self.root, "git", "status", "--porcelain").stdout.strip(), "")
        backups = list((self.root / "backups").rglob("ex03_refund_timing_check.py"))
        self.assertEqual(len(backups), 1)
        self.assertIn("# my attempt", backups[0].read_text())

    def test_reset_one_exercise_only(self):
        for n in ("03", "04"):
            path = next((self.root / "exercises").glob(f"ex{n}_*.py"))
            path.write_text(path.read_text() + "\n# edited\n")
        self.cli("reset", "--exercises", "3", "--yes")
        status = sh(self.root, "git", "status", "--porcelain").stdout
        self.assertNotIn("ex03", status)
        self.assertIn("ex04", status)

    def test_clean_keeps_review_sheets_unless_asked(self):
        self.cli("run", "--candidate", "baseline", "--only", "RC-001")
        self.cli("review-sheet", "latest", "--reviewer", "me")
        self.cli("clean")
        left = sorted(p.name for p in (self.root / "runs").iterdir() if p.name != ".gitkeep")
        self.assertEqual(left, ["review-baseline-me.csv"])
        self.cli("clean", "--reviews")
        self.assertEqual([p.name for p in (self.root / "runs").iterdir() if p.name != ".gitkeep"], [])


@unittest.skipUnless(HAS_GIT, "git is not installed")
class TestStart(unittest.TestCase):
    def test_start_saves_an_undo_point_then_tracks_progress(self):
        from returns_eval import workspace
        if workspace._git_would_prompt_install():
            self.skipTest("git would ask to install developer tools")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"  # like a ZIP download: no .git
            shutil.copytree(REPO, root, ignore=shutil.ignore_patterns(".git", "__pycache__", "backups"))
            for f in (root / "runs").iterdir():
                if f.name != ".gitkeep":
                    f.unlink()
            first = sh(root, sys.executable, "-m", "returns_eval", "start")
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            self.assertIn("saved a starting point", first.stdout)
            self.assertTrue((root / ".git").is_dir())

            def done(text):  # exercise numbers listed as done, e.g. "exercises done 2 of 9 (6, 8)"
                m = re.search(r"exercises done \d+ of 9 \(([\d, ]+)\)", text)
                return set(m.group(1).split(", ")) if m else set()

            before = done(first.stdout)
            if not before:
                self.assertIn("new: nothing done yet", first.stdout)
            shutil.copy(root / "solutions" / "ex06_release_decision.py", root / "exercises")
            (root / "playground" / "my_notes.md").write_text("notes\n")
            again = sh(root, sys.executable, "-m", "returns_eval", "start")
            self.assertIn("changes can be undone with reset", again.stdout)
            self.assertEqual(done(again.stdout), before | {"6"})
            self.assertIn("notes in playground/my_notes.md", again.stdout)


class TestResetWithoutGit(unittest.TestCase):
    def test_cases_reset_works_from_a_zip_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            shutil.copytree(REPO, root, ignore=shutil.ignore_patterns(".git", "__pycache__", "backups"))
            (root / "data" / "cases" / "regressions.jsonl").write_text(
                (root / "solutions" / "ex08_regression_case.jsonl").read_text())
            manifest = root / "data" / "cases" / "manifest.json"
            data = json.loads(manifest.read_text())
            start = data["changelog"][0]["version"]
            data["version"] = "9.9"
            data["changelog"].append({"version": "9.9", "date": "2026-08-27", "change": "test"})
            manifest.write_text(json.dumps(data))
            out = sh(root, sys.executable, "-m", "returns_eval", "reset", "--cases", "--yes")
            self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
            self.assertEqual((root / "data" / "cases" / "regressions.jsonl").read_text(), "")
            restored = json.loads(manifest.read_text())
            self.assertEqual((restored["version"], len(restored["changelog"])), (start, 1))


if __name__ == "__main__":
    unittest.main()
