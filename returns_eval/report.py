"""Plain-text reports.

Rules this module follows:
  - every rate is shown with its numerator and denominator ("13 / 26 (50%)")
  - failures are listed by case, never only as an average
  - critical failures are always listed individually
"""

from __future__ import annotations

import math
import textwrap
from typing import Any

from .cases import CASE_CATEGORIES
from .grading import CHECKS, SEVERITY

WIDTH = 92


def frac(n: int, d: int) -> str:
    return f"{n} / {d} ({n / d:.0%})" if d else f"{n} / 0 (n/a)"


def by_category(results: list[dict[str, Any]]) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    for cat in CASE_CATEGORIES:
        rows = [r for r in results if r["category"] == cat]
        if rows:
            out[cat] = (sum(r["passed"] for r in rows), len(rows))
    return out


def by_check(results: list[dict[str, Any]]) -> dict[str, tuple[int, int]]:
    """For each check: (cases failing it, cases graded)."""
    names = [name for name, _, _ in CHECKS] + ["candidate_error"]
    return {name: (sum(name in r["failed_checks"] for r in results), len(results)) for name in names}


def measures(results: list[dict[str, Any]]) -> dict[str, str]:
    """Product measures beyond pass/fail. Each is shown as numerator / denominator.

    Escalation recall = correct escalations / required escalations
    Reliability       = cases with the same result on every attempt / cases (needs --repeat)
    p95 draft time    = 95th percentile seconds to produce one draft (shown when drafts are slow
                        enough to matter, e.g. a real model)
    """
    out: dict[str, str] = {}
    required = [r for r in results if r.get("required_escalation")]
    if required:
        out["Escalation recall"] = frac(sum(r["escalated"] for r in required), len(required))
    if any(len(r["attempts"]) > 1 for r in results):
        out["Reliability (same result every attempt)"] = frac(sum(r.get("stable", True) for r in results), len(results))
    times = sorted(a.get("seconds", 0) for r in results for a in r["attempts"])
    if times and times[-1] >= 0.1:
        p95 = times[max(0, math.ceil(0.95 * len(times)) - 1)]
        out["p95 draft time"] = f"{p95:.1f} s (n={len(times)} drafts)"
    return out


MEASURE_HELP = {
    "Escalation recall": "needed a specialist and got one",
    "Reliability (same result every attempt)": "gave the same answer every time",
    "p95 draft time": "slowest 5% of drafts took this long",
}
NEXT_STEP_HELP = {
    "inform": "answer the question",
    "accept_return": "say yes to the return",
    "decline_return": "say no to the return",
    "ask_customer": "ask the customer for more information",
    "escalate": "hand it to a specialist",
}
RETURN_STATUS = {"label_issued": "not sent back yet", "in_transit": "on its way back", "received": "arrived back"}
INSPECTION = {"not_started": "not started", "pending": "not done yet", "passed": "passed", "failed": "failed"}
SEVERITY_KEY = "How serious: critical = one is enough to stop a launch; major = the case fails; minor = noted only."


def step(name: str | None) -> str:
    return f"{name} ({NEXT_STEP_HELP[name]})" if name in NEXT_STEP_HELP else str(name)


def header(meta: dict[str, Any]) -> list[str]:
    repeat = f" | repeat {meta['repeat']}" if meta.get("repeat", 1) > 1 else ""
    return [
        f"Tested {meta['candidate']} (version {meta['candidate_version']}) on {meta['case_count']} test cases",
        f"  To repeat this exactly: case set {meta['case_set_version']} (id {meta['case_set_sha256']}) | "
        f"grader {meta['grader_version']}{repeat} | run {meta['run_id']}",
    ]


def summary(run: dict[str, Any]) -> list[str]:
    results = run["results"]
    out = header(run["meta"])
    passed = sum(r["passed"] for r in results)
    out += ["", f"CASES PASSED: {frac(passed, len(results))}", ""]
    out.append(f"{'Results by type of request':<34}{'passed / total':>20}")
    for cat, (p, n) in by_category(results).items():
        out.append(f"  {cat:<32}{frac(p, n):>20}")
    out += ["", f"{'Problems found, by check':<34}{'how serious':<12}{'cases with this problem':>24}"]
    for name, (f, n) in by_check(results).items():
        if name == "candidate_error" and not f:
            continue
        out.append(f"  {name:<32}{SEVERITY[name]:<12}{frac(f, n):>24}")
    out.append(f"  {SEVERITY_KEY}")
    found = measures(results)
    if found:
        out += ["", "Other measures"] + [f"  {name:<40}{value:>16}   {MEASURE_HELP.get(name, '')}"
                                         for name, value in found.items()]
    crit = [r for r in results if r["worst_severity"] == "critical"]
    out += ["", f"Critical failures: {len(crit)}" + (" (serious mistakes: any one of them stops a launch)" if crit else "")]
    for r in crit:
        for c in _failed(r):
            if c["severity"] == "critical":
                out += _wrap(f"{r['case_id']}  {c['check']}: {c['evidence'][0]}", indent="  ", hang="          ")
    out += ["", "Every case (PASS or FAIL, then the checks it failed):"]
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        sev = f"[{r['worst_severity']}]" if r["worst_severity"] else ""
        attempts = f" {r['attempts_passed']}/{len(r['attempts'])} attempts" if len(r["attempts"]) > 1 else ""
        failed = ", ".join(r["failed_checks"])
        out.append(f"  {r['case_id']} {mark} {sev:<11}{r['category']:<20}{failed}{attempts}")
    return out


def case_lines(case: dict[str, Any]) -> list[str]:
    """The case itself: who wrote in, what the records say, and what should happen."""
    exp = case["expected"]
    out = [f"{case['id']}  {case['title']}",
           f"type of request: {case['category']} | must pass: {'yes' if case['must_pass'] else 'no'} | "
           f"policy: {case['policy_version']} | today's date in this case: {case['as_of']}", ""]
    out += ["CUSTOMER", f"  {case['customer']['name']} ({case['customer']['customer_id']}, {case['customer']['email']})"]
    out += _wrap(f'"{case["message"]}"', indent="  ")
    out += ["", "ORDERS THE ASSISTANT CAN LOOK UP"]
    for o in case["orders"]:
        owner = "this customer" if o["customer_id"] == case["customer"]["customer_id"] else f"ANOTHER customer ({o['customer_name']})"
        items = "; ".join(f"{i['name']} ${i['price']}" + (" final sale" if i["final_sale"] else "")
                          + (" opened" if i["opened"] else "") for i in o["items"])
        out.append(f"  {o['order_id']} [{owner}] delivered {o['delivered_on'] or 'UNKNOWN'}: {items}")
        if o["return"]:
            ret = o["return"]
            parts = []
            if ret["label_issued_on"]:
                parts.append(f"label sent {ret['label_issued_on']}")
            parts.append(f"arrived back {ret['received_on']}" if ret["received_on"]
                         else RETURN_STATUS.get(ret["status"], ret["status"]))
            parts.append(f"inspection {INSPECTION.get(ret['inspection']['status'], ret['inspection']['status'])}")
            out.append("      return: " + ", ".join(parts))
        refund = o["refund"]
        out.append("      refund: " + (f"sent ${refund['amount']} on {refund['issued_on']}" if refund["status"] == "issued"
                                       else "not sent yet"))
        if o["notes"]:
            out.append(f"      note: {o['notes']}")
    if not case["orders"]:
        out.append("  (none)")
    out += ["", "WHAT A GOOD REPLY DOES (expected behavior)"] + _wrap(exp["behavior"], indent="  ")
    out += _wrap("okay next steps: " + ", ".join(step(r) for r in exp["acceptable_resolutions"])
                 + f" | right order: {exp['target_order_id'] or 'none yet'}", indent="  ", hang="    ")
    out += [f"  not okay: {u}" for u in case["unacceptable_outcomes"]]
    if exp["must_mention"]:
        out += _wrap("must mention (at least one phrase from each group): "
                     + "; ".join(" | ".join(g) for g in exp["must_mention"]), indent="  ", hang="    ")
    if exp["must_not_mention"]:
        out += _wrap("must never say: " + " | ".join(exp["must_not_mention"]), indent="  ", hang="    ")
    return out


def case_detail(run: dict[str, Any], case: dict[str, Any]) -> list[str]:
    """The case, then each attempt: draft, trace, and every check with its evidence."""
    result = next((r for r in run["results"] if r["case_id"] == case["id"]), None)
    if result is None:
        return [f"{case['id']} is not in this run."]
    out = case_lines(case)
    for i, attempt in enumerate(result["attempts"], start=1):
        label = f" (attempt {i} of {len(result['attempts'])})" if len(result["attempts"]) > 1 else ""
        out += ["", f"THE DRAFT {run['meta']['candidate']} WROTE{label}"]
        draft = attempt["draft"]
        if draft:
            out.append(f"  next step: {step(draft['resolution'])} | order: {draft['order_id'] or 'none'} | "
                       f"draft id {draft['fingerprint']}")
            out += _wrap(draft["reply_text"], indent="  | ")
            if draft["note_for_agent"]:
                out += _wrap(f"note for the support agent: {draft['note_for_agent']}", indent="  ")
        else:
            out.append(f"  (no draft) {attempt['error']}")
        out += ["", "  WHAT IT LOOKED UP OR TRIED TO DO (the trace)"]
        out += [f"    {c['tool']}({', '.join(f'{k}={v!r}' for k, v in c['args'].items())})" for c in attempt["trace"]] or ["    (nothing)"]
        out += ["", "  CHECKS (questions asked about every draft)"]
        for c in attempt["checks"]:
            out.append(f"    {'pass' if c['passed'] else 'FAIL':<5}{c['check']:<19}{c['severity']:<9}{c['question']}")
            for e in c["evidence"]:
                out += _wrap(e, indent="           -> ", hang="              ")
        out.append(f"  {SEVERITY_KEY}")
    verdict = "PASS" if result["passed"] else f"FAIL (worst severity: {result['worst_severity']})"
    out += ["", f"RESULT: {verdict}"]
    return out


def compare(runs: list[dict[str, Any]]) -> list[str]:
    names = [r["meta"]["candidate"] for r in runs]
    col = max(22, *(len(n) + 2 for n in names))
    meta = runs[0]["meta"]
    out = [f"Every version answered the same {meta['case_count']} test cases and was graded the same way.",
           f"  (case set {meta['case_set_version']}, id {meta['case_set_sha256']} | grader {meta['grader_version']})",
           f"Baseline, the approach to beat: {names[0]}", ""]
    out.append(f"{'':<32}" + "".join(f"{n:>{col}}" for n in names))
    out.append(f"{'CASES PASSED':<32}" + "".join(f"{frac(sum(x['passed'] for x in r['results']), len(r['results'])):>{col}}" for r in runs))
    out += ["", "Results by type of request (passed / total)"]
    cats = [by_category(r["results"]) for r in runs]
    for cat in cats[0]:
        out.append(f"  {cat:<30}" + "".join(f"{frac(*c[cat]):>{col}}" for c in cats))
    out += ["", "Problems found, by check (cases with this problem; lower is better)"]
    checks = [by_check(r["results"]) for r in runs]
    for name in checks[0]:
        if name == "candidate_error" and not any(c[name][0] for c in checks):
            continue
        out.append(f"  {name + ' (' + SEVERITY[name] + ')':<30}" + "".join(f"{frac(*c[name]):>{col}}" for c in checks))
    found = [measures(r["results"]) for r in runs]
    names_found = [n for n in dict.fromkeys(k for f in found for k in f)]
    if names_found:
        out += ["", "Other measures"]
        for name in names_found:
            out.append(f"  {name:<30}" + "".join(f"{f.get(name, '-'):>{col}}" for f in found))
            if MEASURE_HELP.get(name):
                out.append(f"    ({MEASURE_HELP[name]})")
    base = {r["case_id"]: r for r in runs[0]["results"]}
    for run in runs[1:]:
        fixed = [r["case_id"] for r in run["results"] if r["passed"] and not base[r["case_id"]]["passed"]]
        broke = [r for r in run["results"] if not r["passed"] and base[r["case_id"]]["passed"]]
        out += ["", f"{run['meta']['candidate']} compared with {names[0]}:",
                f"  now passing ({len(fixed)}): {', '.join(fixed) or 'none'}",
                f"  newly failing ({len(broke)}): " + (", ".join(f"{r['case_id']} [{r['worst_severity']}]" for r in broke) or "none")]
    return out


def gate_report(decision) -> list[str]:
    out = ["Release gates: the rules agreed before testing (data/gates.json)"]
    for g in decision.gates:
        out += _wrap(f"{g.status.upper():<8}{g.id} {g.label}: {g.detail}", indent="  ", hang="            ")
    out += ["", f"DECISION: {decision.status}"] + _wrap(decision.headline, indent="  ")
    for s in decision.next_steps:
        out += _wrap(s, indent="  - ", hang="    ")
    return out


def _failed(result: dict[str, Any]) -> list[dict[str, Any]]:
    seen, out = set(), []
    for attempt in result["attempts"]:
        for c in attempt["checks"]:
            if not c["passed"] and c["check"] not in seen:
                seen.add(c["check"])
                out.append(c)
    return out


def _wrap(text: str, indent: str = "", hang: str | None = None) -> list[str]:
    return textwrap.wrap(text, width=WIDTH, initial_indent=indent,
                         subsequent_indent=hang if hang is not None else indent) or [indent]
