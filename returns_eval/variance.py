"""Luck or a real difference? Run candidates several times and compare them fairly.

A model can answer the same input differently each time. So one run of version A
against one run of version B can show a gap that is only luck. This module runs
each candidate R times on the same cases (seed 1, 2, ... R) and reports:

  - the spread: how much the score moves from run to run on its own
  - per-case pass rates: which cases are unstable
  - every critical failure in any run, because at real volume a rare one will happen
  - a paired comparison: for each case, B's pass rate minus A's, added up, with a 95%
    range from a seeded bootstrap. If the range includes 0, these runs can't tell the
    versions apart. Comparing case by case ("paired") is more sensitive than comparing
    two averages, because both versions answered the same cases (see Miller, 2024 in
    docs/sources.md).

Every number is computed from the runs; nothing is estimated from outside them.
"""

from __future__ import annotations

from typing import Any

from .candidates import load_candidate
from .cases import CaseSet
from .harness import run_eval
from .report import _wrap, frac
from .stats import bootstrap_mean


def repeated_runs(spec: str, case_set: CaseSet, runs: int, first_seed: int = 1) -> list[dict[str, Any]]:
    """Run one candidate `runs` times, seeds first_seed, first_seed+1, ... (seeds only matter for
    candidates with randomness; a script gives the same answer every time)."""
    out = []
    for seed in range(first_seed, first_seed + runs):
        candidate = load_candidate(spec)
        if hasattr(candidate, "seed"):
            candidate.seed = seed
        out.append(run_eval(candidate, case_set))
    return out


def case_pass_rates(runs: list[dict[str, Any]]) -> dict[str, float]:
    """For each case, the share of runs in which it passed."""
    ids = [r["case_id"] for r in runs[0]["results"]]
    return {cid: sum(next(r for r in run["results"] if r["case_id"] == cid)["passed"] for run in runs) / len(runs)
            for cid in ids}


def paired_difference(a_runs: list[dict[str, Any]], b_runs: list[dict[str, Any]], seed: int = 1) -> dict[str, Any]:
    """B minus A, in cases passed per run, with a 95% range. Positive means B passed more."""
    a, b = case_pass_rates(a_runs), case_pass_rates(b_runs)
    diffs = [b[cid] - a[cid] for cid in a]
    n = len(diffs)
    lo, hi = bootstrap_mean(diffs, seed=seed)
    return {"difference": sum(diffs), "low": lo * n, "high": hi * n, "cases": n,
            "per_case": {cid: b[cid] - a[cid] for cid in a}}


def verdict(diff: dict[str, Any]) -> str:
    if diff["low"] > 0:
        return "better"
    if diff["high"] < 0:
        return "worse"
    return "can't tell"


def criticals(runs: list[dict[str, Any]]) -> list[tuple[str, int, str]]:
    """(case id, seed, check) for every critical failure in any run."""
    out = []
    for run in runs:
        for r in run["results"]:
            if r["worst_severity"] == "critical":
                checks = [c["check"] for a in r["attempts"] for c in a["checks"]
                          if not c["passed"] and c["severity"] == "critical"]
                out.append((r["case_id"], run["meta"].get("seed", 0), checks[0] if checks else "?"))
    return out


def report_lines(named: dict[str, list[dict[str, Any]]], seed: int = 1) -> list[str]:
    names = list(named)
    first = named[names[0]]
    runs, cases = len(first), first[0]["meta"]["case_count"]
    seeds = [run["meta"].get("seed") for run in first]
    seed_text = f" (seeds {seeds[0]} to {seeds[-1]})" if seeds[0] is not None else ""
    col = max(18, *(len(n) + 2 for n in names))
    out = [f"Luck or a real difference? Each version answered the same {cases} test cases {runs} times{seed_text}."]
    simulated = [n for n in names if named[n][0]["meta"].get("simulated")]
    if simulated:
        what = "is a script" if len(simulated) == 1 else "are scripts"
        model = "a language model" if len(simulated) == 1 else "language models"
        out += _wrap(f"SIMULATED: {', '.join(simulated)} {what} with built-in randomness, not {model}. The numbers "
                     "show how to read repeated runs, not how any real model behaves.")
    scripted = [n for n in names if not named[n][0]["meta"].get("simulated")]
    if scripted:
        out += _wrap(f"{', '.join(scripted)}: a script that gives the same answer every time, so every run is the same.")

    out += ["", f"{'Cases passed in each run':<32}" + "".join(f"{n:>{col}}" for n in names)]
    scores = {n: [sum(r["passed"] for r in run["results"]) for run in named[n]] for n in names}
    for i in range(runs):
        label = f"  run {i + 1}" + (f" (seed {seeds[i]})" if seeds[i] is not None else "")
        out.append(f"{label:<32}" + "".join(f"{f'{scores[n][i]} / {cases}':>{col}}" for n in names))
    out.append(f"{'  lowest to highest':<32}" + "".join(f"{f'{min(scores[n])} to {max(scores[n])}':>{col}}" for n in names))
    out.append(f"{'  average':<32}" + "".join(
        f"{f'{sum(scores[n]) / runs:.1f} / {cases} ({sum(scores[n]) / runs / cases:.0%})':>{col}}" for n in names))

    out += ["", "Across all runs"]
    rates = {n: case_pass_rates(named[n]) for n in names}
    out.append(f"{'  cases that failed at least once':<32}" + "".join(
        f"{frac(sum(v < 1 for v in rates[n].values()), cases):>{col}}" for n in names))
    out.append(f"{'  cases that never passed':<32}" + "".join(
        f"{frac(sum(v == 0 for v in rates[n].values()), cases):>{col}}" for n in names))
    out.append(f"{'  runs with a critical failure':<32}" + "".join(
        f"{frac(sum(any(r['worst_severity'] == 'critical' for r in run['results']) for run in named[n]), runs):>{col}}"
        for n in names))
    for n in names:
        found = criticals(named[n])
        if found:
            out += _wrap(f"{n}: critical failures in " + "; ".join(f"{cid} (seed {s}, {chk})" for cid, s, chk in found)
                         + ". One run would have shown none of these if it had used a different seed.",
                         indent="  ", hang="    ")

    for n in names:
        shaky = sorted(((cid, v) for cid, v in rates[n].items() if 0 < v < 1), key=lambda x: (x[1], x[0]))
        if shaky:
            out += _wrap(f"{n}, cases whose result changed between runs (share of runs passed): "
                         + ", ".join(f"{cid} {round(v * runs)}/{runs}" for cid, v in shaky), indent="  ", hang="    ")

    base = names[0]
    for other in names[1:]:
        diff = paired_difference(named[base], named[other], seed=seed)
        out += ["", f"{other} compared with {base} (paired: the same cases, run for run)",
                f"  average difference: {diff['difference']:+.1f} cases per run",
                f"  95% range for the real difference: {diff['low']:+.1f} to {diff['high']:+.1f} cases per run"]
        v = verdict(diff)
        if v == "can't tell":
            text = (f"The range includes 0, so these {runs} runs can't tell {other} from {base}. "
                    "A gap this size is what luck alone can produce. More runs, or more cases, would narrow the range.")
        else:
            text = (f"The whole range is {'above' if v == 'better' else 'below'} 0, so {other} did {v} on these cases, "
                    "and luck alone is an unlikely explanation. It's still only these cases: it says nothing about "
                    "requests the case set doesn't cover.")
        out += _wrap(text, indent="  -> ", hang="     ")
        moved = sorted(((cid, d) for cid, d in diff["per_case"].items() if d), key=lambda x: (-abs(x[1]), x[0]))[:6]
        if moved:
            out += _wrap(f"biggest per-case differences (share of runs passed, {other} minus {base}): "
                         + ", ".join(f"{cid} {d:+.0%}" for cid, d in moved), indent="  ", hang="    ")
    return out
