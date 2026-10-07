"""Command-line interface: python3 -m returns_eval <command>.

Run `python3 -m returns_eval --help` for the list of commands.
"""

from __future__ import annotations

import argparse
import glob as globmod
import sys
import textwrap
from pathlib import Path
from typing import Any

from . import gates, human_review, pilot, report, workspace
from .candidates import BUILT_IN, load_candidate
from .cases import CASE_CATEGORIES, CASES_DIR, MANIFEST, REPO_ROOT, CaseError, load_case_set, read_case_file, subset, validate_case
from .harness import RUNS_DIR, load_run, run_eval, save_run


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    try:
        return args.func(args) or 0
    except CaseError as exc:
        print(exc, file=sys.stderr)
        return 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python3 -m returns_eval",
                                description="Evals by example: grade drafted replies to return requests.")
    sub = p.add_subparsers(title="commands")

    def cmd(name: str, func, help_text: str) -> argparse.ArgumentParser:
        sp = sub.add_parser(name, help=help_text, description=help_text)
        sp.set_defaults(func=func)
        return sp

    def cases_arg(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--cases", nargs="+", metavar="FILE",
                        help="case files to use instead of data/cases/manifest.json")

    sp = cmd("start", cmd_start, "Check that everything is ready, save an undo point, and show your progress.")
    sp.add_argument("--no-save", action="store_true", help="don't create the git starting point used by reset")

    sp = cmd("cases", cmd_cases, "List the test cases.")
    sp.add_argument("--category", choices=CASE_CATEGORIES)
    cases_arg(sp)

    sp = cmd("show-case", cmd_show_case, "Show one case: input, record, and expected behavior.")
    sp.add_argument("case_id")
    cases_arg(sp)

    sp = cmd("add-case", cmd_add_case, "Validate a case (.json) and append it to data/cases/regressions.jsonl.")
    sp.add_argument("file", type=Path)
    sp.add_argument("--to", type=Path, default=None, help="case file to append to (default: data/cases/regressions.jsonl)")

    cmd("candidates", cmd_candidates, "List the built-in candidates.")

    sp = cmd("run", cmd_run, "Run a candidate on every case, grade it, save the run, and print a summary.")
    sp.add_argument("--candidate", required=True, help="built-in name or module.path:ClassName")
    sp.add_argument("--baseline", help="run file or candidate name to check G4 (no category worse than baseline)")
    sp.add_argument("--review", nargs="+", metavar="CSV", help="human review scorecards for gate G6")
    sp.add_argument("--repeat", type=int, default=1, help="attempts per case; a case passes only if all pass")
    sp.add_argument("--only", nargs="+", metavar="CASE_ID", help="run only these cases (e.g. to try a paid model cheaply)")
    sp.add_argument("--out", type=Path, default=RUNS_DIR, help="where to save the run file (default: runs/)")
    cases_arg(sp)

    sp = cmd("report", cmd_report, "Print the report for a saved run, or one case in detail.")
    sp.add_argument("run", help="run file path, 'latest', or 'latest:<candidate>'")
    sp.add_argument("--case", help="show this case in full: input, draft, trace, every check")

    sp = cmd("compare", cmd_compare, "Run (or load) a baseline and candidates on the same cases and compare them.")
    sp.add_argument("items", nargs="+", metavar="CANDIDATE_OR_RUN", help="first one is the baseline")
    sp.add_argument("--review", nargs="+", metavar="CSV", help="human review scorecards for gate G6")
    sp.add_argument("--allow-mismatch", action="store_true",
                    help="compare runs even if case set or grader versions differ (not recommended)")
    cases_arg(sp)

    sp = cmd("gate", cmd_gate, "Apply the release gates to a saved run. Exit code 0 only if ready for a pilot.")
    sp.add_argument("run", help="run file path, 'latest', or 'latest:<candidate>'")
    sp.add_argument("--baseline", help="run file or candidate name for gate G4")
    sp.add_argument("--review", nargs="+", metavar="CSV", help="human review scorecards for gate G6")

    sp = cmd("brief", cmd_brief, "Write a one-page decision brief (Markdown) comparing a candidate with the baseline.")
    sp.add_argument("baseline", help="candidate name or run file for the baseline")
    sp.add_argument("candidate", help="candidate name or run file to decide on")
    sp.add_argument("--review", nargs="+", metavar="CSV", help="human review scorecards for the candidate")
    sp.add_argument("--out", type=Path, help="default: runs/decision-brief-<candidate>.md")
    cases_arg(sp)

    sp = cmd("review-sheet", cmd_review_sheet, "Write a blank human review scorecard (CSV) for a run.")
    sp.add_argument("run")
    sp.add_argument("--out", type=Path, help="default: runs/review-<candidate>-<reviewer>.csv")
    sp.add_argument("--reviewer", default="", help="pre-fill the reviewer column")

    sp = cmd("review-summary", cmd_review_summary, "Summarize filled scorecards and reviewer agreement.")
    sp.add_argument("run")
    sp.add_argument("scorecards", nargs="+", metavar="CSV")

    sp = cmd("clean", cmd_clean, "Delete saved runs in runs/ (keeps review sheets and decision briefs unless --reviews).")
    sp.add_argument("--reviews", action="store_true", help="also delete review sheets and decision briefs in runs/")

    sp = cmd("reset", cmd_reset, "Put tutorial files back to their starting point (backs up your versions first). "
             "With no options, only reports what has changed.")
    sp.add_argument("--cases", action="store_true", help="data/cases/ (undo added regression cases and version bumps)")
    sp.add_argument("--exercises", nargs="*", type=int, metavar="N",
                    help="exercise files; give numbers to reset only those (e.g. --exercises 3 4)")
    sp.add_argument("--playground", action="store_true", help="playground/")
    sp.add_argument("--code", action="store_true", help="returns_eval/, data/gates.json, data/policies/ (undo experiments)")
    sp.add_argument("--runs", action="store_true", help="delete every saved run and review sheet (sheets are backed up)")
    sp.add_argument("--all", action="store_true", help="all of the above")
    sp.add_argument("--from", dest="ref", default="HEAD",
                    help="git commit to restore from (default HEAD; use origin/main if you committed your own changes)")
    sp.add_argument("--yes", action="store_true", help="don't ask for confirmation")

    sp = cmd("pilot", cmd_pilot, "Summarize the ILLUSTRATIVE supervised-pilot data.")
    sp.add_argument("--file", type=Path, default=pilot.PILOT_FILE)
    return p


# --- helpers ----------------------------------------------------------------

def _expand(paths: list[str] | None) -> list[str] | None:
    """Expand wildcards like data/human_review/*.csv ourselves. Windows shells don't."""
    if not paths:
        return paths
    out: list[str] = []
    for p in paths:
        matches = sorted(globmod.glob(p)) if any(ch in p for ch in "*?[") else []
        out += matches or [p]
    return out


def _print(lines: list[str]) -> None:
    print("\n".join(lines))


def _rel(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def resolve_run(ref: str) -> Path:
    """Accept a path, 'latest', or 'latest:<candidate>'."""
    if ref == "latest" or ref.startswith("latest:"):
        name = ref.partition(":")[2]
        pattern = f"*_{name}.json" if name else "*.json"
        found = sorted(RUNS_DIR.glob(pattern)) + sorted(RUNS_DIR.glob(pattern.replace(".json", "-*.json")))
        found = sorted(found, key=lambda p: p.stat().st_mtime)
        if not found:
            raise SystemExit(f"No saved runs match '{ref}' in {_rel(RUNS_DIR)}. "
                             "Create one with: python3 -m returns_eval run --candidate <name>")
        return found[-1]
    return Path(ref)


def _run_or_load(item: str, case_set, repeat: int = 1, out: Path = RUNS_DIR) -> dict[str, Any]:
    path = Path(item)
    if item.endswith(".json") or item.startswith("latest"):
        return load_run(resolve_run(item))
    if path.exists():
        return load_run(path)
    run = run_eval(load_candidate(item), case_set, repeat=repeat)
    saved = save_run(run, out)
    print(f"Ran {run['meta']['candidate']}: saved {_rel(saved)}")
    return run


def _cases_by_id(paths=None) -> dict[str, dict[str, Any]]:
    return {c["id"]: c for c in load_case_set(paths).cases}


def _review_summary(run: dict[str, Any], paths: list[str] | None):
    if not paths:
        return None
    rows, problems = human_review.load_reviews(paths)
    for p in problems:
        print(f"Scorecard problem: {p}", file=sys.stderr)
    return human_review.summarize(run, rows)


# --- commands ---------------------------------------------------------------

def cmd_start(args) -> int:
    import platform as plat

    def line(label: str, value: str) -> None:
        print(f"  {label:<14}{value}")

    print("Evals by example: ready check")
    line("Python", f"{plat.python_version()} ok")
    cs = load_case_set()
    line("Course files", f"ok ({len(cs.cases)} test cases, {len(BUILT_IN)} versions of the assistant to test)")

    status = "skipped (--no-save)" if args.no_save else workspace.save_starting_point()
    line("Undo", {
        "ok": "ok (changes can be undone with reset)",
        "saved": "ok (saved a starting point, so any change can be undone with reset)",
        "no-git": "limited: git isn't available, so only reset --cases can undo changes",
        "inside-other-repo": "limited: this folder is inside another git repository; reset compares with it",
        "failed": "limited: couldn't save a starting point; reset --cases still works",
    }.get(status, status))

    from exercises.__main__ import TITLES, check
    done = [n for n in TITLES if (lambda r: r[1] > 0 and r[0] == r[1])(check(n))]
    notes = REPO_ROOT / "playground" / "my_notes.md"
    changed = workspace.changed_files(list(workspace.GROUPS)) if workspace.git_available() else []
    started = bool(done) or notes.exists() or bool(changed)
    if not started:
        line("Progress", "new: nothing done yet")
    else:
        parts = [f"exercises done {len(done)} of {len(TITLES)}" + (f" ({', '.join(map(str, done))})" if done else "")]
        if notes.exists():
            parts.append("notes in playground/my_notes.md")
        if changed:
            parts.append(f"{len(changed)} file(s) changed since the start")
        line("Progress", "; ".join(parts))
    print("Ready." + ("" if started else " First step: python3 -m returns_eval run --candidate candidate-v1"))
    return 0


def cmd_cases(args) -> int:
    cs = load_case_set(args.cases)
    rows = [c for c in cs.cases if not args.category or c["category"] == args.category]
    print(f"Showing {len(rows)} of {len(cs.cases)} cases (case set {cs.version}, id {cs.sha256}; files: {', '.join(cs.files)})")
    print()
    print(f"{'ID':<8}{'TYPE OF REQUEST':<21}{'MUST':<6}{'RIGHT NEXT STEP':<26}TITLE")
    for c in rows:
        must = "yes" if c["must_pass"] else ""
        expected = "/".join(c["expected"]["acceptable_resolutions"])
        print(f"{c['id']:<8}{c['category']:<21}{must:<6}{expected:<26}{c['title']}")
    print()
    counts = {cat: sum(c["category"] == cat for c in cs.cases) for cat in CASE_CATEGORIES}
    print("Per type of request: " + ", ".join(f"{k} {v}" for k, v in counts.items() if v))
    print("MUST = a case that must pass, or the release is blocked.")
    print("See one case in full: python3 -m returns_eval show-case RC-001")
    return 0


def cmd_show_case(args) -> int:
    cases = _cases_by_id(args.cases)
    case = cases.get(args.case_id.upper())
    if case is None:
        raise SystemExit(f"No case {args.case_id}. List them with: python3 -m returns_eval cases")
    _print(report.case_lines(case))
    return 0


def cmd_add_case(args) -> int:
    import json

    target = args.to or CASES_DIR / "regressions.jsonl"
    new_cases = read_case_file(args.file)
    existing = {c["id"] for c in load_case_set().cases}
    problems = [p for c in new_cases for p in validate_case(c)]
    problems += [f"{c['id']}: id already exists in the case set" for c in new_cases if c.get("id") in existing]
    if problems:
        print("Not added. Fix these first:\n  " + "\n  ".join(problems))
        return 1
    with Path(target).open("a", encoding="utf-8") as fh:
        for case in new_cases:
            fh.write(json.dumps(case, ensure_ascii=False) + "\n")
    print(f"Added {', '.join(c['id'] for c in new_cases)} to {_rel(target)}.")
    version = json.loads(MANIFEST.read_text(encoding="utf-8"))["version"]
    print(f"Now bump \"version\" in {_rel(MANIFEST)} (currently {version}) and add a changelog line,")
    print("so runs made before and after this change are never compared by mistake.")
    return 0


def cmd_candidates(args) -> int:
    for name, cls in BUILT_IN.items():
        print(f"{name:<14} v{cls.version:<5} {cls.description}")
    print("\nAlso: any module.path:ClassName, e.g. exercises.ex09_candidate_v3:CandidateV3")
    print("Optional LLM adapter (not used by default): see docs/llm-adapter.md")
    return 0


def cmd_run(args) -> int:
    if args.repeat < 1:
        raise SystemExit("--repeat must be 1 or more")
    case_set = load_case_set(_expand(args.cases))
    if args.only:
        case_set = subset(case_set, args.only)
    candidate = load_candidate(args.candidate)
    run = run_eval(candidate, case_set, repeat=args.repeat)
    path = save_run(run, args.out)
    _print(report.summary(run))
    baseline = _run_or_load(args.baseline, case_set) if args.baseline else None
    decision = gates.evaluate(run, baseline, _review_summary(run, _expand(args.review)))
    print()
    _print(report.gate_report(decision))
    print(f"\nSaved {_rel(path)}")
    errors = {a["error"] for r in run["results"] for a in r["attempts"] if a["error"]}
    crashed = sum("candidate_error" in r["failed_checks"] for r in run["results"])
    if crashed == len(run["results"]) and len(errors) == 1:
        print(f"\nEvery case failed with the same error, so this is likely setup, not the model:\n  {errors.pop()}")
        return 1
    worst = next((r for r in run["results"] if r["worst_severity"] == "critical"),
                 next((r for r in run["results"] if not r["passed"]), None))
    if worst:
        print(f"Look at one failure in detail: python3 -m returns_eval report {_rel(path)} --case {worst['case_id']}")
    return 0


def cmd_report(args) -> int:
    run = load_run(resolve_run(args.run))
    if args.case:
        cases = _cases_by_id(_case_files(run))
        case = cases.get(args.case.upper())
        if case is None:
            raise SystemExit(f"No case {args.case} in this run's case set.")
        _print(report.case_detail(run, case))
    else:
        _print(report.summary(run))
    return 0


def _case_files(run: dict[str, Any]) -> list[str] | None:
    if run["meta"]["case_set_version"] == "custom":
        return [str(REPO_ROOT / f) if not Path(f).is_absolute() else f for f in run["meta"]["case_files"]]
    return None


def cmd_compare(args) -> int:
    case_set = load_case_set(args.cases)
    runs = [_run_or_load(item, case_set) for item in args.items]
    keys = {(r["meta"]["case_set_sha256"], r["meta"]["grader_version"]) for r in runs}
    if len(keys) > 1:
        print("WARNING: these runs used different case sets or grader versions, so comparing them isn't fair:")
        for r in runs:
            m = r["meta"]
            print(f"  {m['candidate']}: cases {m['case_set_version']} sha {m['case_set_sha256']}, grader {m['grader_version']}")
        if not args.allow_mismatch:
            print("Rerun them on the same cases, or pass --allow-mismatch if you understand the risk.")
            return 2
    print()
    _print(report.compare(runs))
    for run in runs[1:]:
        decision = gates.evaluate(run, runs[0], _review_summary(run, _expand(args.review)))
        print(f"\n== Gates for {run['meta']['candidate']} ==")
        _print(report.gate_report(decision))
    return 0


def cmd_gate(args) -> int:
    run = load_run(resolve_run(args.run))
    baseline = None
    if args.baseline:
        baseline = _run_or_load(args.baseline, load_case_set(_case_files(run)))
    decision = gates.evaluate(run, baseline, _review_summary(run, _expand(args.review)))
    _print(report.header(run["meta"]) + [""] + report.gate_report(decision))
    return 0 if decision.status == gates.READY else 1


def cmd_brief(args) -> int:
    from . import brief

    case_set = load_case_set(_expand(args.cases))
    base, cand = _run_or_load(args.baseline, case_set), _run_or_load(args.candidate, case_set)
    review = _review_summary(cand, _expand(args.review))
    decision = gates.evaluate(cand, base, review)
    text = brief.build(base, cand, decision, review)
    out = args.out or RUNS_DIR / f"decision-brief-{cand['meta']['candidate']}.md"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(text, encoding="utf-8")
    print(text)
    print(f"Saved {_rel(out)}. Fill in the parts in italics: why now, the recommendation, and the owners.")
    return 0


def cmd_review_sheet(args) -> int:
    run = load_run(resolve_run(args.run))
    out = args.out or RUNS_DIR / f"review-{run['meta']['candidate']}-{args.reviewer or 'reviewer'}.csv"
    n = human_review.export_sheet(run, _cases_by_id(_case_files(run)), out, args.reviewer)
    print(f"Wrote {n} drafts to {_rel(out)}")
    print("Fill in one rating per column for each row (open it in any spreadsheet):")
    for name, guide in human_review.GUIDE.items():
        print(textwrap.fill(f"{name}: {guide}", width=92, initial_indent="  ", subsequent_indent="    "))
    print(f"Then: python3 -m returns_eval review-summary {_rel(resolve_run(args.run))} {_rel(out)}")
    return 0


def cmd_review_summary(args) -> int:
    run = load_run(resolve_run(args.run))
    rows, problems = human_review.load_reviews(_expand(args.scorecards))
    s = human_review.summarize(run, rows)
    if s.illustrative:
        print("ILLUSTRATIVE review data: the reviewers and ratings are invented for teaching.\n")
    print(f"Human review of {s.candidate}: {report.frac(s.reviewed, s.drafts)} drafts reviewed "
          f"by {', '.join(s.reviewers) or 'nobody yet'}")
    if s.stale:
        print(f"  Stale (draft changed since it was reviewed): {', '.join(s.stale)}")
    if s.unreviewed:
        print(f"  Not yet reviewed: {', '.join(s.unreviewed)}")
    for p in problems:
        print(f"  Problem: {p}")
    print("\nRatings (if two reviewers disagree, the worse rating counts)")
    for criterion, counts in s.counts.items():
        rated = sum(counts.values())
        question = human_review.QUESTION.get(criterion)
        print(f"  {criterion}" + (f" ({question})" if question else "")
              + ("" if rated == s.reviewed else f" [rated on {rated} of {s.reviewed} drafts]"))
        for value, n in counts.items():
            print(f"    {value:<16}{report.frac(n, s.reviewed):>16}")
    for (a, b), crit in s.agreement.items():
        print(f"\nHow often {a} and {b} gave the same rating")
        for c, (agree, total) in crit.items():
            print(f"  {c:<24}{report.frac(agree, total):>16}")
    if s.disagreements:
        print("\nDisagreements to talk through (then make the rating guide clearer, or fix the case):")
        for d in s.disagreements:
            print(f"  {d}")
    return 0


def cmd_clean(args) -> int:
    removed = workspace.clean(include_reviews=args.reviews)
    kept = sorted(p.name for p in RUNS_DIR.iterdir() if p.suffix in (".csv", ".md")) if not args.reviews else []
    print(f"Deleted {len(removed)} file(s) from {_rel(RUNS_DIR)}.")
    if kept:
        print(f"Kept {len(kept)} review sheet(s) or brief(s): {', '.join(kept)}. Add --reviews to delete them too.")
    print("Rebuild the standard results with: python3 -m returns_eval compare baseline candidate-v1 candidate-v2")
    return 0


def cmd_reset(args) -> int:
    groups = []
    if args.all or args.cases:
        groups.append("cases")
    if args.all or args.exercises is not None:
        groups.append("exercises")
    if args.all or args.playground:
        groups.append("playground")
    if args.all or args.code:
        groups.append("code")
    wipe_runs = args.all or args.runs
    report_only = not groups and not wipe_runs

    paths = []
    for group in (workspace.GROUPS if report_only else groups):
        if group == "exercises" and args.exercises:
            paths += workspace.exercise_paths(args.exercises)
        else:
            paths += workspace.GROUPS[group]

    if not workspace.git_available():
        if report_only:
            print("This folder isn't a git clone, so reset can't compare it with the original files.")
            print("It can still reset the case files: python3 -m returns_eval reset --cases")
            return 0
        if "cases" in groups:
            touched = workspace.reset_cases_without_git()
            print("Reset " + (", ".join(touched) if touched else "nothing; the case files were already at the start") + ".")
        others = [g for g in groups if g != "cases"]
        if others:
            print(f"Can't restore {', '.join(others)} without git. Re-download those files from the "
                  "repository on GitHub, or clone it with git so reset can do it for you.")
        if wipe_runs:
            _wipe_runs()
        return 0

    changes = workspace.changed_files(paths, args.ref)
    if report_only:
        if not changes:
            print("Everything is at the starting point. Nothing to reset.")
        else:
            since = "the start" if args.ref == "HEAD" else args.ref
            print(f"Files you've changed since {since}:")
            for status, name in changes:
                print(f"  {status:<9}{name}")
            print("\nTo put a part back the way it was, use reset with: --cases, --exercises [N ...], "
                  "--playground, --code, --runs, or --all")
        return 0

    if changes:
        print("These files will be put back to their starting point:")
        for status, name in changes:
            print(f"  {status:<9}{name}")
        if not args.yes and not _confirm(f"Reset {len(changes)} file(s)? Your versions are backed up first."):
            print("Nothing changed.")
            return 1
        saved = workspace.backup([name for _, name in changes])
        workspace.restore_with_git(changes, args.ref)
        print(f"Done. Your previous versions are in {_rel(saved)}/")
    elif groups:
        print("Those files are already at the starting point.")
    if wipe_runs:
        _wipe_runs()
    return 0


def _wipe_runs() -> None:
    sheets = [str(p.relative_to(REPO_ROOT)) for p in RUNS_DIR.iterdir() if p.suffix in (".csv", ".md")]
    if sheets:
        print(f"Review scorecards backed up to {_rel(workspace.backup(sheets))}/")
    print(f"Deleted {len(workspace.clean(include_reviews=True))} file(s) from {_rel(RUNS_DIR)}.")


def _confirm(question: str) -> bool:
    if not sys.stdin.isatty():
        print("Not running interactively; add --yes to confirm.")
        return False
    return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")


def cmd_pilot(args) -> int:
    _print(pilot.summary_lines(pilot.load_tickets(args.file), pilot.load_incidents(), args.file))
    return 0
