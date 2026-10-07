"""A one-page decision brief, generated from saved runs.

The evidence, gates, and sample sizes are filled in from the runs. The parts only
a person can write (why now, the recommendation, the owners) are left as prompts
in italics. Every number names its source, so the brief can be checked.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .gates import Decision
from .human_review import ReviewSummary
from .report import by_category, frac, measures

NEXT_STAGE = {
    "BLOCKED": "Fix the critical failures and rerun every case. No pilot.",
    "NOT READY": "Fix the failed gates and rerun every case.",
    "PENDING": "Finish what's pending (usually human review), then decide.",
    "READY FOR A SUPERVISED PILOT": "Supervised pilot: limited traffic, a human approves every reply.",
}


def _row(label: str, base: str, cand: str, source: str) -> str:
    return f"| {label} | {base} | {cand} | {source} |"


def build(baseline: dict[str, Any], candidate: dict[str, Any], decision: Decision,
          review: ReviewSummary | None = None) -> str:
    b, c = baseline["results"], candidate["results"]
    bm, cm = baseline["meta"], candidate["meta"]
    bmeas, cmeas = measures(b), measures(c)
    source = f"case set {cm['case_set_version']} ({cm['case_count']} cases), grader {cm['grader_version']}"
    illustrative = review is not None and review.illustrative

    def crit(results):
        return frac(sum(r["worst_severity"] == "critical" for r in results), len(results))

    worse = [cat for cat, (p, n) in by_category(c).items()
             if cat in by_category(b) and p * by_category(b)[cat][1] < by_category(b)[cat][0] * n]
    lines = [
        f"# Decision brief: {cm['candidate']} vs {bm['candidate']}",
        "",
        f"Generated {datetime.now(timezone.utc).date().isoformat()} (UTC) from runs `{bm['run_id']}` and `{cm['run_id']}`. "
        "Every number shows its sample size and source."
        + (" **Human review figures use ILLUSTRATIVE (invented) scorecards.**" if illustrative else ""),
        "",
        "## Decision",
        "",
        f"**{decision.status}.** {decision.headline}",
        "",
        f"Next stage: {NEXT_STAGE.get(decision.status, '')}",
        "",
        "## Why now",
        "",
        "_In one or two sentences: what's happening to customers or the business, and what waiting costs._",
        "",
        "## Evidence",
        "",
        f"| Measure | Baseline: {bm['candidate']} | {cm['candidate']} | Source |",
        "|---|---|---|---|",
        _row("Cases passed", frac(sum(r["passed"] for r in b), len(b)), frac(sum(r["passed"] for r in c), len(c)), source),
        _row("Cases with a critical failure", crit(b), crit(c), source),
    ]
    for name in dict.fromkeys([*bmeas, *cmeas]):
        lines.append(_row(name, bmeas.get(name, "-"), cmeas.get(name, "-"), source))
    lines.append(_row("Categories worse than baseline", "-", ", ".join(worse) or "none", source))
    if review is not None and review.drafts:
        agree = next(iter(review.agreement.values()), {}).get("usability")
        agree_text = f"; reviewers agreed on usability for {frac(*agree)}" if agree else ""
        lines.append(_row("Drafts needing a major rewrite (human review)", "-",
                          frac(review.counts["usability"]["major_rewrite"], review.reviewed),
                          f"{len(review.reviewers)} reviewer(s){agree_text}"
                          + (" (ILLUSTRATIVE)" if illustrative else "")))
    lines += ["", "By request type (cases passed):", "",
              f"| Request type | {bm['candidate']} | {cm['candidate']} |", "|---|---|---|"]
    bcat = by_category(b)
    for cat, (p, n) in by_category(c).items():
        lines.append(f"| {cat} | {frac(*bcat[cat]) if cat in bcat else '-'} | {frac(p, n)} |")

    lines += ["", "## Release gates", ""]
    lines += [f"- **{g.status.upper()}** {g.id} {g.label}: {g.detail}" for g in decision.gates]
    lines += [
        "",
        "## Recommendation",
        "",
        "_What you're asking the team to approve: which request types, how much traffic, who keeps human "
        "review, and when you'll report back._",
        "",
        "## Stop and rollback conditions",
        "",
        "- Any unauthorized action (refund, sent message, order change) or exposure of another customer's "
        "data: stop immediately and go back to agents working without drafts.",
        "- A false refund commitment reaches a customer: stop and review the case.",
        "- Escalation recall below 100% on cases that require a specialist: send those request types to people only.",
        "- Agent rework or repeat contacts above the manual baseline for two review periods: reduce traffic and investigate.",
        "- Any model, prompt, or policy change: freeze expansion and rerun every case first.",
        "",
        "## Owners",
        "",
        "| Role | Name |",
        "|---|---|",
        "| Decision owner (PM) | _name_ |",
        "| Policy owner (what counts as a correct answer) | _name_ |",
        "| Eval owner (cases, checks, reruns) | _name_ |",
        "| Rollback owner (can turn drafts off) | _name_ |",
        "",
        "## What this evidence doesn't show",
        "",
        f"- These are offline results on {cm['case_count']} written cases. They show whether drafts are correct "
        "and safe on situations someone thought of. They don't show handling time, rework, or customer outcomes; "
        "a supervised pilot measures those.",
        f"- {cm['case_count']} cases can't show that a rare, serious failure won't happen at scale.",
    ]
    if bm["case_set_sha256"] != cm["case_set_sha256"] or bm["grader_version"] != cm["grader_version"]:
        lines += ["", "**Warning:** these runs used different case sets or grader versions, so they aren't directly comparable."]
    return "\n".join(lines) + "\n"
