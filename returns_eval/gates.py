"""Release gates: the rules agreed before anyone saw results (data/gates.json).

The decision is ordered on purpose. A critical failure blocks release no matter
how good the other numbers are; nothing below G1 can outvote it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .cases import DATA_DIR
from .human_review import ReviewSummary
from .report import by_category, frac

GATES_FILE = DATA_DIR / "gates.json"

BLOCKED = "BLOCKED"
NOT_READY = "NOT READY"
PENDING = "PENDING"
READY = "READY FOR A SUPERVISED PILOT"


@dataclass
class GateResult:
    id: str
    label: str
    status: str            # pass | fail | pending
    detail: str
    why: str = ""


@dataclass
class Decision:
    status: str
    headline: str
    next_steps: list[str] = field(default_factory=list)
    gates: list[GateResult] = field(default_factory=list)


def load_gates() -> dict[str, Any]:
    return json.loads(GATES_FILE.read_text(encoding="utf-8"))


def evaluate(run: dict[str, Any], baseline: dict[str, Any] | None = None,
             review: ReviewSummary | None = None, config: dict[str, Any] | None = None) -> Decision:
    config = config or load_gates()
    results = run["results"]
    total = len(results)
    gates: list[GateResult] = []

    for gate in config["gates"]:
        rule, gid, label, why = gate["rule"], gate["id"], gate["label"], gate.get("why", "")
        if rule == "max_critical_failures":
            crit = [r["case_id"] for r in results if r["worst_severity"] == "critical"]
            status = "pass" if len(crit) <= gate["max"] else "fail"
            detail = f"{frac(len(crit), total)} cases had one" + (f": {', '.join(crit)}" if crit else "")
        elif rule == "must_pass_cases":
            must = [r for r in results if r["must_pass"]]
            failed = [r["case_id"] for r in must if not r["passed"]]
            status = "fail" if failed else "pass"
            detail = f"{frac(len(must) - len(failed), len(must))} must-pass cases passed" + (
                f"; failed: {', '.join(failed)}" if failed else "")
        elif rule == "min_case_pass_rate":
            passed = sum(r["passed"] for r in results)
            status = "pass" if total and passed / total >= gate["min"] else "fail"
            detail = f"{frac(passed, total)} passed; need at least {gate['min']:.0%}"
        elif rule == "no_category_regression":
            if baseline is None:
                status, detail = "pending", "Not compared with the baseline yet. Use compare, or add --baseline baseline."
            elif baseline["meta"]["case_set_sha256"] != run["meta"]["case_set_sha256"]:
                status, detail = "pending", "The baseline was tested on different cases. Run both on the same cases."
            else:
                ours, theirs = by_category(results), by_category(baseline["results"])
                worse = [f"{cat} {frac(*ours[cat])} vs baseline {frac(*theirs[cat])}"
                         for cat in ours if cat in theirs and ours[cat][0] * theirs[cat][1] < theirs[cat][0] * ours[cat][1]]
                status = "fail" if worse else "pass"
                detail = ("Worse than the baseline at: " + "; ".join(worse)) if worse else \
                    f"Every type of request does at least as well as {baseline['meta']['candidate']}"
        elif rule == "max_candidate_errors":
            errors = [r["case_id"] for r in results if "candidate_error" in r["failed_checks"]]
            status = "pass" if len(errors) <= gate["max"] else "fail"
            detail = f"{frac(len(errors), total)} cases crashed" + (f": {', '.join(errors)}" if errors else "")
        # EXTEND HERE: add a gate rule. Add an elif for your rule name, then use it from
        # data/gates.json. Changing only a threshold needs no code: edit gates.json.
        # Worked example: docs/extending.md#add-a-release-gate
        elif rule == "human_review":
            status, detail = _human_gate(gate, review)
        else:
            raise ValueError(f"Unknown gate rule '{rule}' in {GATES_FILE}")
        gates.append(GateResult(gid, label, status, detail, why))

    return _decide(gates)


def _human_gate(gate: dict[str, Any], review: ReviewSummary | None) -> tuple[str, str]:
    if review is None:
        return "pending", "No person has reviewed the drafts yet."
    if not review.complete:
        stale = f"; {len(review.stale)} out of date (the draft changed after it was reviewed)" if review.stale else ""
        return "pending", f"{frac(review.reviewed, review.drafts)} drafts reviewed by a person{stale}."
    rewrites = review.counts["usability"]["major_rewrite"]
    incorrect = review.counts["policy_interpretation"]["incorrect"]
    ok = rewrites / review.drafts <= gate["max_major_rewrite_rate"] and incorrect <= gate["max_policy_incorrect"]
    tag = " (ILLUSTRATIVE review data)" if review.illustrative else ""
    return ("pass" if ok else "fail",
            f"major_rewrite {frac(rewrites, review.drafts)} (max {gate['max_major_rewrite_rate']:.0%}); "
            f"policy incorrect {frac(incorrect, review.drafts)} (max {gate['max_policy_incorrect']}){tag}")


def _decide(gates: list[GateResult]) -> Decision:
    by_id = {g.id: g for g in gates}
    failed = [g for g in gates if g.status == "fail"]
    pending = [g for g in gates if g.status == "pending"]
    if by_id.get("G1") and by_id["G1"].status == "fail":
        return Decision(BLOCKED, "Stop. At least one draft made a serious (critical) mistake. One is enough "
                        "to stop a launch, however good the other results are.", [
            "Look at each critical case: python3 -m returns_eval report <run> --case <id>",
            "Work out how it happened, fix it, then test ALL the cases again, not just the ones that failed.",
            "Turn any new kind of mistake into a test case, so it can't sneak back.",
        ], gates)
    if failed:
        return Decision(NOT_READY, "Not yet. Some of the rules the team agreed on aren't met.", [
            f"Fix: {g.id} {g.label}" for g in failed], gates)
    if pending:
        return Decision(PENDING, "Almost. The automatic checks passed, but something still has to happen "
                        "before anyone can decide.", [
            f"Still needed: {g.id} {g.label} ({g.detail})" for g in pending], gates)
    return Decision(READY, "Every rule passed. It's ready for a small, careful trial with real customers "
                    "(a supervised pilot), where a person checks every reply before it's sent.", [
        "Start small: a few support agents, with a person approving every reply.",
        "Measure whether the job really gets easier: time per ticket, how much agents fix, and whether "
        "customers write back about the same problem. Compare with agents working without the drafts.",
        "Turn every new mistake found in the trial into a test case, and test everything again.",
    ], gates)
