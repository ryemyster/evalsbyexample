"""Human review scorecard.

Some judgments don't reduce to a string match: is this draft usable as-is? Is
this a sensible reading of the policy? Support experts answer those on a
scorecard, one row per draft. The scorecard is a CSV so it opens in any
spreadsheet.

Each row records the draft's fingerprint. If the candidate changes and a draft
changes, the old review no longer counts ("stale") and that draft needs a new
review. Reviewers do not see the automated results, so the code's verdict
doesn't steer theirs.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any

# EXTEND HERE: add a scorecard criterion. Add a key with its allowed values (best first)
# and a line in GUIDE, then document it in docs/grading.md. See docs/extending.md
CRITERIA: dict[str, tuple[str, ...]] = {
    # values are ordered best -> worst
    "usability": ("send_as_is", "minor_edits", "major_rewrite"),
    "policy_interpretation": ("correct", "not_applicable", "debatable", "incorrect"),
    "tone": ("ok", "needs_work"),
    "case_expectation_ok": ("yes", "no"),
}
GUIDE = {
    "usability": "send_as_is = an agent would send it unchanged; minor_edits = small fixes; "
                 "major_rewrite = faster to write from scratch",
    "policy_interpretation": "correct / debatable (reasonable people could differ) / incorrect / "
                             "not_applicable (no policy question in this case)",
    "tone": "ok / needs_work",
    "case_expectation_ok": "yes / no: is the case's expected behavior itself right? (flags bad test cases)",
}
QUESTION = {
    "usability": "could an agent send it with little or no fixing?",
    "policy_interpretation": "did it read the store's rules sensibly?",
    "tone": "is the tone right for the customer?",
    "case_expectation_ok": "is the test case itself right?",
}
COLUMNS = ["case_id", "category", "title", "draft_fingerprint", "resolution", "order_id", "reply_text",
           "expected_behavior", *CRITERIA, "notes", "reviewer"]


def export_sheet(run: dict[str, Any], cases: dict[str, dict[str, Any]], path: Path, reviewer: str = "") -> int:
    """Write a blank scorecard for every draft in a run. Uses the first attempt."""
    rows = 0
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        for result in run["results"]:
            draft = result["attempts"][0]["draft"]
            if draft is None:
                continue
            case = cases[result["case_id"]]
            writer.writerow({
                "case_id": result["case_id"], "category": result["category"], "title": result["title"],
                "draft_fingerprint": draft["fingerprint"], "resolution": draft["resolution"],
                "order_id": draft["order_id"] or "", "reply_text": draft["reply_text"],
                "expected_behavior": case["expected"]["behavior"], "reviewer": reviewer,
                **{name: "" for name in CRITERIA}, "notes": "",
            })
            rows += 1
    return rows


def load_reviews(paths: list[str | Path]) -> tuple[list[dict[str, str]], list[str]]:
    """Read scorecards. Returns (rows, problems). Blank rows are skipped as 'not reviewed yet'."""
    rows, problems = [], []
    for path in paths:
        path = Path(path)
        if not path.exists():
            problems.append(f"Scorecard not found: {path}")
            continue
        with path.open(newline="", encoding="utf-8") as fh:
            for lineno, row in enumerate(csv.DictReader(fh), start=2):
                if not any((row.get(c) or "").strip() for c in CRITERIA):
                    continue
                # A column missing from the file means the scorecard predates that criterion: not rated.
                bad = [f"{c}={row.get(c)!r}" for c, allowed in CRITERIA.items()
                       if c in row and row[c] not in allowed]
                if bad or not (row.get("reviewer") or "").strip():
                    problems.append(f"{path.name}:{lineno} ({row.get('case_id')}): "
                                    + ("invalid " + ", ".join(bad) if bad else "missing reviewer name"))
                    continue
                rows.append({**row, "_file": path.name})
    return rows, problems


def percent_agreement(a: list[dict[str, str]], b: list[dict[str, str]], criterion: str) -> tuple[int, int]:
    """How often two reviewers gave the same rating to the same draft. Returns (agree, total)."""
    b_by_key = {(r["case_id"], r["draft_fingerprint"]): r for r in b}
    agree = total = 0
    for row in a:
        other = b_by_key.get((row["case_id"], row["draft_fingerprint"]))
        if other is None:
            continue
        if row.get(criterion) is None or other.get(criterion) is None:
            continue  # one of the scorecards doesn't have this criterion
        total += 1
        agree += row[criterion] == other[criterion]
    return agree, total


@dataclass
class ReviewSummary:
    candidate: str
    drafts: int
    reviewed: int
    stale: list[str] = field(default_factory=list)            # case ids whose review no longer matches
    unreviewed: list[str] = field(default_factory=list)
    worst: dict[str, dict[str, str]] = field(default_factory=dict)  # case_id -> criterion -> worst rating
    counts: dict[str, dict[str, int]] = field(default_factory=dict)
    agreement: dict[tuple[str, str], dict[str, tuple[int, int]]] = field(default_factory=dict)
    disagreements: list[str] = field(default_factory=list)
    reviewers: list[str] = field(default_factory=list)
    illustrative: bool = False

    @property
    def complete(self) -> bool:
        return self.drafts > 0 and self.reviewed == self.drafts


def summarize(run: dict[str, Any], rows: list[dict[str, str]]) -> ReviewSummary:
    current = {r["case_id"]: r["attempts"][0]["draft"]["fingerprint"]
               for r in run["results"] if r["attempts"][0]["draft"] is not None}
    fresh = [r for r in rows if current.get(r["case_id"]) == r["draft_fingerprint"]]
    stale = sorted({r["case_id"] for r in rows if r["case_id"] in current} - {r["case_id"] for r in fresh})
    summary = ReviewSummary(candidate=run["meta"]["candidate"], drafts=len(current),
                            reviewed=len({r["case_id"] for r in fresh}), stale=stale,
                            illustrative=any("ILLUSTRATIVE" in r["_file"].upper() for r in rows))
    summary.unreviewed = sorted(set(current) - {r["case_id"] for r in fresh})
    summary.reviewers = sorted({r["reviewer"] for r in fresh})

    for row in fresh:
        worst = summary.worst.setdefault(row["case_id"], {})
        for criterion, order in CRITERIA.items():
            value, prev = row.get(criterion), worst.get(criterion)
            if value is not None and (prev is None or order.index(value) > order.index(prev)):
                worst[criterion] = value
    for criterion, order in CRITERIA.items():
        summary.counts[criterion] = {v: sum(w.get(criterion) == v for w in summary.worst.values()) for v in order}

    by_reviewer = {name: [r for r in fresh if r["reviewer"] == name] for name in summary.reviewers}
    for a, b in combinations(summary.reviewers, 2):
        summary.agreement[(a, b)] = {c: percent_agreement(by_reviewer[a], by_reviewer[b], c) for c in CRITERIA}
        b_rows = {r["case_id"]: r for r in by_reviewer[b]}
        for row in by_reviewer[a]:
            other = b_rows.get(row["case_id"])
            if other is None:
                continue
            for c in CRITERIA:
                if row.get(c) is not None and other.get(c) is not None and row[c] != other[c]:
                    summary.disagreements.append(f"{row['case_id']} {c}: {a}={row[c]}, {b}={other[c]}")
    return summary
