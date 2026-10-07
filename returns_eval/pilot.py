"""Summarize the (illustrative) supervised pilot.

An offline eval answers "are the drafts correct and safe on known cases?" A
pilot answers a different question: "does the job get done better?" This module
reads ticket-level pilot data and reports outcomes by arm, always as
numerator / denominator.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import median
from typing import Any

from .cases import DATA_DIR
from .report import _wrap, frac

PILOT_DIR = DATA_DIR / "pilot"
PILOT_FILE = PILOT_DIR / "pilot_tickets.ILLUSTRATIVE.csv"
INCIDENTS_FILE = PILOT_DIR / "incidents.ILLUSTRATIVE.jsonl"
BANNER = "ILLUSTRATIVE DATA: invented for teaching. Not results from any real pilot."


def load_tickets(path: Path = PILOT_FILE) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        row["handling_minutes"] = float(row["handling_minutes"])
    return rows


def load_incidents(path: Path = INCIDENTS_FILE) -> list[dict[str, Any]]:
    if not Path(path).exists():
        return []
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def median_minutes(rows: list[dict[str, Any]]) -> float | None:
    return median(r["handling_minutes"] for r in rows) if rows else None


def summary_lines(rows: list[dict[str, Any]], incidents: list[dict[str, Any]], path: Path = PILOT_FILE) -> list[str]:
    illustrative = "ILLUSTRATIVE" in Path(path).name.upper()
    arms = sorted({r["arm"] for r in rows}, key=lambda a: (a != "manual", a))
    by_arm = {a: [r for r in rows if r["arm"] == a] for a in arms}
    out = [BANNER, ""] if illustrative else []
    dates = sorted(r["date"] for r in rows)
    out.append(f"Supervised pilot: {len(rows)} tickets, {dates[0]} to {dates[-1]}" if rows else "No tickets.")
    out.append("  " + ", ".join(f"{a}: {len(by_arm[a])} tickets" for a in arms))

    def fmt(m: float | None) -> str:
        return "-" if m is None else f"{m:.1f} min"

    out += ["", f"{'Median handling time':<28}" + "".join(f"{a:>18}" for a in arms)]
    out.append(f"  {'all requests':<26}" + "".join(f"{fmt(median_minutes(by_arm[a])):>18}" for a in arms))
    for rtype in sorted({r["request_type"] for r in rows}):
        cells = []
        for a in arms:
            sub = [r for r in by_arm[a] if r["request_type"] == rtype]
            cells.append(f"{fmt(median_minutes(sub))} (n={len(sub)})")
        out.append(f"  {rtype:<26}" + "".join(f"{c:>18}" for c in cells))

    out += ["", "Repeat contacts (reopened within 7 days)"]
    for a in arms:
        n = sum(r["reopened_within_7_days"] == "yes" for r in by_arm[a])
        out.append(f"  {a:<26}{frac(n, len(by_arm[a])):>18}")

    assisted = [r for r in rows if r["draft_outcome"] not in ("n/a", "")]
    if assisted:
        out += ["", "Drafts (assisted arm only)"]
        for outcome in ("used_as_is", "edited", "discarded"):
            n = sum(r["draft_outcome"] == outcome for r in assisted)
            out.append(f"  {outcome:<26}{frac(n, len(assisted)):>18}")
        caught = [r for r in assisted if r["agent_caught_error"] not in ("none", "n/a", "")]
        out.append(f"  {'errors caught by agents':<26}{frac(len(caught), len(assisted)):>18}  "
                   + ", ".join(f"{r['ticket_id']} {r['agent_caught_error']}" for r in caught))
    if incidents:
        out += ["", "Incidents"]
        for inc in incidents:
            out += _wrap(f"{inc['incident_id']} ({inc['ticket_id']}, {inc['date']}): {inc['what_happened']}", "  ", "    ")
            out += _wrap(f"Why the offline eval missed it: {inc['why_the_offline_eval_missed_it']}", "    ", "      ")
            out += _wrap(f"Action: {inc['action']}", "    ", "      ")
    out += [
        "", "How to read this",
        "  - The offline eval said the drafts were correct on the 26 cases in set 1.0. It did not measure",
        "    time, rework, or repeat contacts. Those only show up here.",
        "  - Compare within a request type: the two arms got a different mix of requests.",
        "  - A high used_as_is rate is not proof of quality. Agents may accept a convenient draft and",
        "    the error surfaces later as a repeat contact.",
        "  - 20 tickets per arm cannot show that a rare, serious failure will not happen.",
    ]
    if illustrative:
        out += ["", BANNER]
    return out
