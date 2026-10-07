"""Clean up and start over.

clean  deletes generated run files in runs/. Your filled-in review scorecards
       are kept unless you ask for them too.
reset  puts tutorial files back the way they were when you cloned, so you can
       work through a part again. It always copies your current versions to
       backups/<time>/ first, so nothing you wrote is lost.

Reset restores from git, which every clone has. If you downloaded a ZIP instead,
it can still reset the case files; for other files it tells you what to do.
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from .cases import CASES_DIR, MANIFEST, REPO_ROOT

RUNS_DIR = REPO_ROOT / "runs"
BACKUPS_DIR = REPO_ROOT / "backups"

# What each reset group covers. Paths are relative to the repository root.
GROUPS = {
    "cases": ["data/cases"],
    "exercises": ["exercises"],
    "playground": ["playground"],
    "code": ["returns_eval", "data/gates.json", "data/policies"],
}
EXERCISE_TESTS = "exercises/tests"  # never touched; learners don't edit these


def clean(include_reviews: bool = False) -> list[Path]:
    """Delete saved runs (and optionally review CSVs). Returns what was removed."""
    removed = []
    if not RUNS_DIR.exists():
        return removed
    for path in sorted(RUNS_DIR.iterdir()):
        if path.name == ".gitkeep" or path.is_dir():
            continue
        if path.suffix in (".csv", ".md") and not include_reviews:  # reviews and briefs are the learner's work
            continue
        path.unlink()
        removed.append(path)
    return removed


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True)


def git_available() -> bool:
    if shutil.which("git") is None:
        return False
    top = _git("rev-parse", "--show-toplevel")
    return top.returncode == 0 and Path(top.stdout.strip()).resolve() == REPO_ROOT.resolve()


def changed_files(paths: list[str], ref: str = "HEAD") -> list[tuple[str, str]]:
    """(status, path) for files under `paths` that differ from `ref`, including new files."""
    changes: dict[str, str] = {}
    diff = _git("diff", "--name-status", ref, "--", *paths)
    if diff.returncode != 0:
        raise SystemExit(f"git could not compare with '{ref}': {diff.stderr.strip()}")
    for line in diff.stdout.splitlines():
        status, _, name = line.partition("\t")
        changes[name] = {"M": "changed", "D": "deleted", "A": "added"}.get(status[:1], "changed")
    untracked = _git("ls-files", "--others", "--exclude-standard", "--", *paths)
    for name in untracked.stdout.splitlines():
        changes[name] = "new file"
    return sorted((status, name) for name, status in changes.items()
                  if not name.startswith(EXERCISE_TESTS + "/"))


def exercise_paths(numbers: list[int]) -> list[str]:
    paths = []
    for n in numbers:
        found = sorted(p for p in (REPO_ROOT / "exercises").glob(f"ex{n:02d}_*") if p.is_file())
        if not found:
            raise SystemExit(f"No exercise {n}. Exercises are numbered 1-9.")
        paths += [str(p.relative_to(REPO_ROOT)) for p in found]
    return paths


def backup(names: list[str]) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target, n = BACKUPS_DIR / stamp, 1
    while target.exists():  # never overwrite an earlier backup
        n += 1
        target = BACKUPS_DIR / f"{stamp}-{n}"
    for name in names:
        src = REPO_ROOT / name
        if src.is_file():
            dest = target / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    return target


def restore_with_git(changes: list[tuple[str, str]], ref: str = "HEAD") -> None:
    tracked = [name for status, name in changes if status != "new file" and status != "added"]
    if tracked:
        result = _git("checkout", ref, "--", *tracked)
        if result.returncode != 0:
            raise SystemExit(f"git checkout failed: {result.stderr.strip()}")
    for status, name in changes:
        if status in ("new file", "added"):
            path = REPO_ROOT / name
            if status == "added":
                _git("rm", "--cached", "--quiet", "--", name)
            if path.is_file():
                path.unlink()


def reset_cases_without_git() -> list[str]:
    """Fallback for a ZIP download: empty the regression file and roll the manifest back."""
    touched = []
    regressions = CASES_DIR / "regressions.jsonl"
    if regressions.exists() and regressions.read_text(encoding="utf-8").strip():
        touched.append("data/cases/regressions.jsonl")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    first = manifest["changelog"][0]
    if manifest["version"] != first["version"] or len(manifest["changelog"]) > 1:
        touched.append("data/cases/manifest.json")
    if not touched:
        return []
    backup(touched)
    regressions.write_text("", encoding="utf-8")
    manifest["version"] = first["version"]
    manifest["changelog"] = [first]
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return touched


def _git_would_prompt_install() -> bool:
    """On a Mac without developer tools, running git opens an install dialog. Don't trigger it."""
    if platform.system() != "Darwin":
        return False
    return subprocess.run(["xcode-select", "-p"], capture_output=True).returncode != 0


def save_starting_point() -> str:
    """Make the folder a git repository with one commit, so `reset` can undo changes later."""
    if git_available():
        return "ok"
    if shutil.which("git") is None or _git_would_prompt_install():
        return "no-git"
    inside_other = _git("rev-parse", "--show-toplevel")
    if inside_other.returncode == 0:
        return "inside-other-repo"
    ident = ["-c", "user.name=Learner", "-c", "user.email=learner@example.com"]
    for args in (["init", "-q"], ["add", "-A"], [*ident, "commit", "-q", "-m", "Starting point"]):
        if _git(*args).returncode != 0:
            return "failed"
    return "saved"
