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
    sp.add_argument("--seed", type=int, help="for candidates with randomness: which roll of the dice (default 1)")
    sp.add_argument("--out", type=Path, default=RUNS_DIR, help="where to save the run file (default: runs/)")
    cases_arg(sp)

    sp = cmd("variance", cmd_variance, "Run candidates several times on the same cases: is a difference real, or luck?")
    sp.add_argument("items", nargs="+", metavar="CANDIDATE", help="the first one is compared with each of the others")
    sp.add_argument("--runs", type=int, default=10, help="runs per candidate (default 10)")
    sp.add_argument("--seed", type=int, default=1, help="seed of the first run; later runs use the next seeds")
    sp.add_argument("--only", nargs="+", metavar="CASE_ID", help="run only these cases")
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

    sp = cmd("rubric-check", cmd_rubric_check, "Check that a rubric's criteria say what a rater should look for.")
    sp.add_argument("file", type=Path)

    sp = cmd("labels", cmd_labels, "Show the human-labeled drafts: splits, annotator agreement, and leakage checks.")
    sp.add_argument("--file", type=Path, help="label file (default: the one in data/labels/manifest.json)")

    def judge_args(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--prompt", type=Path, help="judge prompt template (default: data/judges/tone.v1.txt)")

    sp = cmd("judge", cmd_judge, "Have an automated judge grade the drafts in a saved run (no labels needed).")
    sp.add_argument("judge", help="judge-a, judge-b, or module.path:ClassName")
    sp.add_argument("--run", required=True, help="run file, 'latest', or 'latest:<candidate>'")
    sp.add_argument("--criterion", default="tone", choices=("tone", "complete"))
    sp.add_argument("--versus", metavar="RUN", help="compare with another run's drafts, case by case (pairwise, both orders)")
    judge_args(sp)

    sp = cmd("bias-check", cmd_bias_check, "Probe a judge: does its verdict move when something irrelevant changes?")
    sp.add_argument("judge", help="judge-a, judge-b, or module.path:ClassName")
    judge_args(sp)

    sp = cmd("calibrate", cmd_calibrate, "Compare judges with people's labels: what each one catches, misses, and flags wrongly.")
    sp.add_argument("judges", nargs="+", metavar="JUDGE", help="judge-a, judge-b, or module.path:ClassName")
    sp.add_argument("--split", default="calibration", choices=("train", "calibration", "holdout", "all"))
    judge_args(sp)

    sp = cmd("budget", cmd_budget, "Work out a checking plan's weekly cost and how many problems still get through.")
    sp.add_argument("plan", type=Path, help="a plan file, e.g. exercises/ex15_eval_budget.json")
    sp.add_argument("--costs", type=Path, help="assumptions file (default: data/economics/costs.ILLUSTRATIVE.json)")

    sp = cmd("traces", cmd_traces, "Check ILLUSTRATIVE production traces step by step, and apply the rollback triggers.")
    sp.add_argument("--deployment", choices=("production", "canary"), help="show only one deployment")
    sp.add_argument("--trace", metavar="TRACE_ID", help="show one trace in full, e.g. T-105")
    sp.add_argument("--file", type=Path, help="trace file (default: data/production/traces.ILLUSTRATIVE.jsonl)")

    sp = cmd("clean", cmd_clean, "Delete saved runs in runs/ (keeps review sheets and decision briefs unless --reviews).")
    sp.add_argument("--reviews", action="store_true", help="also delete review sheets and decision briefs in runs/")

    sp = cmd("reset", cmd_reset, "Put tutorial files back to their starting point (backs up your versions first). "
             "With no options, only reports what has changed.")
    sp.add_argument("--cases", action="store_true", help="data/cases/ (undo added regression cases and version bumps)")
    sp.add_argument("--exercises", nargs="*", type=int, metavar="N",
                    help="exercise files; give numbers to reset only those (e.g. --exercises 3 4)")
    sp.add_argument("--playground", action="store_true", help="playground/")
    sp.add_argument("--code", action="store_true", help="returns_eval/, data/gates.json, data/policies/, and Part 2's data folders (undo experiments)")
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
    if args.seed is not None:
        if not hasattr(candidate, "seed"):
            raise SystemExit(f"{args.candidate} has no randomness, so --seed changes nothing. Leave it out.")
        candidate.seed = args.seed
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


def cmd_variance(args) -> int:
    from . import variance

    if args.runs < 2:
        raise SystemExit("--runs must be 2 or more; the point is to see how results move between runs.")
    case_set = load_case_set(_expand(args.cases))
    if args.only:
        case_set = subset(case_set, args.only)
    named = {}
    for item in args.items:
        runs = variance.repeated_runs(item, case_set, args.runs, args.seed)
        named[runs[0]["meta"]["candidate"]] = runs
    _print(variance.report_lines(named, seed=args.seed))
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
        print(f"\nHow often {a} and {b} gave the same rating, and how much of that is beyond chance (kappa)")
        for c, (agree, total) in crit.items():
            kappa = s.kappa.get((a, b), {}).get(c)
            kappa_text = "" if kappa is None else f"   kappa {kappa:.2f}"
            print(f"  {c:<24}{report.frac(agree, total):>16}{kappa_text}")
        print("  kappa: 1 = always agree; 0 = no better than chance (agreeing on the most common rating is easy).")
    if s.disagreements:
        print("\nDisagreements to talk through (then make the rating guide clearer, or fix the case):")
        for d in s.disagreements:
            print(f"  {d}")
    return 0


def cmd_rubric_check(args) -> int:
    from . import rubric

    data = rubric.load(args.file)
    errors, warnings = rubric.lint(data)
    print(f"Rubric {data.get('rubric', '?')} {data.get('version', '?')}: {len(data.get('criteria', []))} criteria "
          f"({_rel(args.file)})")
    for c in data.get("criteria", []):
        if isinstance(c, dict):
            print(f"  {c.get('id', '?'):<26}{str(c.get('scale', '?')):<12}graded by {str(c.get('graded_by', '?')):<7}"
                  f"reference: {c.get('reference', '?')}")
    if errors:
        print(f"\nNot ready: {len(errors)} problem(s). Raters using it would disagree, and so would a judge.")
        for e in errors:
            print(textwrap.fill(e, width=92, initial_indent="  - ", subsequent_indent="    "))
    for w in warnings:
        print(textwrap.fill(f"note: {w}", width=92, initial_indent="  ", subsequent_indent="    "))
    if not errors:
        print("\nReady: every criterion says what a rater looks at, what each value means, and who grades it.")
    return 1 if errors else 0


def cmd_labels(args) -> int:
    from . import labels

    _print(labels.health(labels.load_items(args.file)))
    return 0


def _judge_items(split: str | None = None, path=None):
    from . import labels
    from .judging import with_case_context

    return with_case_context(labels.load_items(path, split), _cases_by_id())


def cmd_judge(args) -> int:
    from .judging import items_from_run, load_judge

    judge = load_judge(args.judge, args.prompt)
    run = load_run(resolve_run(args.run))
    items = items_from_run(run, _cases_by_id(_case_files(run)))
    label = f"{run['meta']['candidate']} (run {run['meta']['run_id']})"
    if judge.simulated:
        print("SIMULATED judge: a script that behaves like an LLM judge with known flaws, not a language model.")
    if args.versus:
        other = load_run(resolve_run(args.versus))
        theirs = {i["case_id"]: i for i in items_from_run(other, _cases_by_id(_case_files(other)))}
        pairs = [(i, theirs[i["case_id"]]) for i in items if i["case_id"] in theirs]
        name_a, name_b = run["meta"]["candidate"], other["meta"]["candidate"]
        results = [judge.pairwise_both_orders(a, b) for a, b in pairs]
        print(f"{judge.name} compared the tone of {name_a} and {name_b} on {len(pairs)} cases, asking each "
              "question twice with the order swapped.\n")
        first = sum(r["a_first"] == "A" for r in results)
        print(f"  asked once, {name_a} shown first: {name_a} won {report.frac(first, len(results))}")
        print(f"  asked once, {name_b} shown first: {name_b} won "
              f"{report.frac(sum(r['b_first'] == 'B' for r in results), len(results))}")
        print(f"  the order decided the winner in {report.frac(sum(r['order_dependent'] for r in results), len(results))} cases")
        print("\n  Counting a win only when both orders agree:")
        for who, key in ((name_a, "A"), (name_b, "B"), ("tie (no difference, or the order decided)", "tie"),
                         ("unreadable answers", "error")):
            print(f"    {who:<44}{report.frac(sum(r['winner'] == key for r in results), len(results)):>16}")
        return 0
    verdicts = [judge.pointwise(i, args.criterion) for i in items]
    print(f"{judge.name} graded {len(items)} drafts from {label} for '{args.criterion}'.\n")
    for value in ("ok", "problem", "error"):
        print(f"  {value:<10}{report.frac(sum(v['verdict'] == value for v in verdicts), len(verdicts)):>16}")
    flagged = [(i, v) for i, v in zip(items, verdicts) if v["verdict"] != "ok"]
    if flagged:
        print("\nNot ok:")
        for i, v in flagged:
            conf = "" if v["confidence"] is None else f" (confidence {v['confidence']:.2f})"
            print(textwrap.fill(f"{i['case_id']}  {v['verdict']}{conf}: {v['reason']}", width=92,
                                initial_indent="  ", subsequent_indent="          "))
    if args.criterion == "complete":
        differ = [(i, v) for i, v in zip(items, verdicts)
                  if v["verdict"] != "error" and (v["verdict"] == "problem") != ("required_content" in i["failed_checks"])]
        if differ:
            print("\nWhere the judge and the required_content check (exact phrases) disagree:")
            for i, v in differ:
                check = "FAIL" if "required_content" in i["failed_checks"] else "pass"
                print(textwrap.fill(f"{i['case_id']}: check {check}, judge {v['verdict']}: {v['reason']}", width=92,
                                    initial_indent="  ", subsequent_indent="    "))
            print("  Read those drafts yourself. Which one was right? Neither is the answer key; people are.")
    print("\nThis judge hasn't been checked against people for this use yet. See: python3 -m returns_eval calibrate")
    return 0


def cmd_bias_check(args) -> int:
    from .judging import load_judge, probes

    items = [i for i in _judge_items() if i["split"] in ("train", "calibration")]
    judge = load_judge(args.judge, args.prompt)
    results = probes.run_probes(lambda: load_judge(args.judge, args.prompt), items, args.prompt,
                                lambda p: load_judge(args.judge, p))
    label = _rel(args.prompt) if args.prompt else "data/judges/tone.v1.txt"
    _print(probes.report_lines(judge, results, label, len(items)))
    return 0


def cmd_calibrate(args) -> int:
    from .judging import calibration, load_judge, prompt_problems

    items = _judge_items(args.split)
    if args.prompt:
        problems = prompt_problems(args.prompt.read_text(encoding="utf-8"))
        for p in problems:
            print(textwrap.fill(f"Prompt problem: {p}", width=92, subsequent_indent="  "))
        if problems:
            print()
    named = {}
    for spec in args.judges:
        judge = load_judge(spec, args.prompt)
        named[judge.name] = calibration.summarize(items, calibration.judge_items(judge, items))
    _print(calibration.report_lines(named, args.split, len(items)))
    return 0


def cmd_budget(args) -> int:
    import json

    from . import economics

    if not args.plan.exists():
        raise SystemExit(f"Plan file not found: {args.plan}. Start from exercises/ex15_eval_budget.json.")
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{args.plan} isn't valid JSON ({exc.msg}, line {exc.lineno}).") from exc
    costs = economics.load_costs(args.costs)
    commands = set(build_parser()._subparsers._group_actions[0].choices)
    problems = economics.plan_problems(plan, commands)
    threshold = plan.get("people_check_unsure_below")
    cases = _cases_by_id()
    rates = usage = None
    if plan.get("judge") in ("judge-a", "judge-b") and plan.get("measured_on") in ("calibration", "holdout", "calibration+holdout"):
        rates, usage = economics.judge_rates(plan["judge"], plan["measured_on"], cases, threshold)
    result = economics.evaluate(plan, costs, rates, usage)
    everyone = {"judge": None, "people_random_share": {s: 1.0 for s in costs["segment_share"]}}
    nobody = {"judge": None}
    references = {"people check every draft, no judge": economics.evaluate(everyone, costs, None, None),
                  "no judge and no people": economics.evaluate(nobody, costs, None, None)}
    _print(economics.report_lines(plan, costs, result, references, usage, problems))
    ok = not problems and result["eval_usd"] <= costs["weekly_budget_usd"] and \
        result["totals"]["missed"] <= costs["team_max_missed_per_week"]
    return 0 if ok else 1


def cmd_traces(args) -> int:
    from . import production

    traces = production.load_traces(args.file)
    if args.trace:
        found = [t for t in traces if t["trace_id"] == args.trace.upper()]
        if not found:
            raise SystemExit(f"No trace {args.trace}. Traces run from {traces[0]['trace_id']} to {traces[-1]['trace_id']}.")
        _print(production.trace_lines(found[0]))
        return 0
    _print(production.summary_lines(traces, args.deployment))
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
