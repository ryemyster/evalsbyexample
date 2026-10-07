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


def header(meta: dict[str, Any]) -> list[str]:
    repeat = f" | repeat {meta['repeat']}" if meta.get("repeat", 1) > 1 else ""
    return [
        f"Candidate {meta['candidate']} v{meta['candidate_version']} | cases {meta['case_set_version']} "
        f"(sha {meta['case_set_sha256']}, {meta['case_count']} cases) | grader {meta['grader_version']}{repeat}",
        f"Run {meta['run_id']} at {meta['run_time_utc']}",
    ]


def summary(run: dict[str, Any]) -> list[str]:
    results = run["results"]
    out = header(run["meta"])
    passed = sum(r["passed"] for r in results)
    out += ["", f"CASES PASSED: {frac(passed, len(results))}", ""]
    out.append(f"{'By case category':<34}{'passed / total':>20}")
    for cat, (p, n) in by_category(results).items():
        out.append(f"  {cat:<32}{frac(p, n):>20}")
    out += ["", f"{'By check (failure type)':<34}{'severity':<10}{'cases failing / graded':>26}"]
    for name, (f, n) in by_check(results).items():
        if name == "candidate_error" and not f:
            continue
        out.append(f"  {name:<32}{SEVERITY[name]:<10}{frac(f, n):>26}")
    found = measures(results)
    if found:
        out += ["", "Other measures"] + [f"  {name:<40}{value:>24}" for name, value in found.items()]
    crit = [r for r in results if r["worst_severity"] == "critical"]
    out += ["", f"Critical failures: {len(crit)}" + (" (each one blocks release on its own)" if crit else "")]
    for r in crit:
        for c in _failed(r):
            if c["severity"] == "critical":
                out += _wrap(f"{r['case_id']}  {c['check']}: {c['evidence'][0]}", indent="  ", hang="          ")
    out += ["", "Cases:"]
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
    out = [f"{case['id']}  {case['title']}", f"category: {case['category']} | must_pass: {case['must_pass']} | "
           f"policy: {case['policy_version']} | as of {case['as_of']} | source: {case['source']}", ""]
    out += ["CUSTOMER", f"  {case['customer']['name']} ({case['customer']['customer_id']}, {case['customer']['email']})"]
    out += _wrap(f'"{case["message"]}"', indent="  ")
    out += ["", "ORDERS THE TOOLS CAN RETURN"]
    for o in case["orders"]:
        owner = "this customer" if o["customer_id"] == case["customer"]["customer_id"] else f"ANOTHER customer ({o['customer_name']})"
        items = "; ".join(f"{i['name']} ${i['price']}" + (" final sale" if i["final_sale"] else "")
                          + (" opened" if i["opened"] else "") for i in o["items"])
        out.append(f"  {o['order_id']} [{owner}] delivered {o['delivered_on'] or 'UNKNOWN'}: {items}")
        if o["return"]:
            ret = o["return"]
            out.append(f"      return: {ret['status']}, label {ret['label_issued_on']}, received {ret['received_on']}, "
                       f"inspection {ret['inspection']['status']}")
        out.append(f"      refund: {o['refund']['status']}" + (f" ${o['refund']['amount']} on {o['refund']['issued_on']}"
                                                              if o['refund']['amount'] else ""))
        if o["notes"]:
            out.append(f"      note: {o['notes']}")
    if not case["orders"]:
        out.append("  (none)")
    out += ["", "EXPECTED BEHAVIOR"] + _wrap(exp["behavior"], indent="  ")
    out.append(f"  acceptable resolution: {', '.join(exp['acceptable_resolutions'])} | target order: {exp['target_order_id']}")
    out += [f"  unacceptable: {u}" for u in case["unacceptable_outcomes"]]
    if exp["must_mention"]:
        out += _wrap("must mention (one phrase from each group): "
                     + "; ".join(" | ".join(g) for g in exp["must_mention"]), indent="  ", hang="    ")
    if exp["must_not_mention"]:
        out += _wrap("must not mention: " + " | ".join(exp["must_not_mention"]), indent="  ", hang="    ")
    return out


def case_detail(run: dict[str, Any], case: dict[str, Any]) -> list[str]:
    """The case, then each attempt: draft, trace, and every check with its evidence."""
    result = next((r for r in run["results"] if r["case_id"] == case["id"]), None)
    if result is None:
        return [f"{case['id']} is not in this run."]
    out = case_lines(case)
    for i, attempt in enumerate(result["attempts"], start=1):
        label = f" (attempt {i} of {len(result['attempts'])})" if len(result["attempts"]) > 1 else ""
        out += ["", f"DRAFT FROM {run['meta']['candidate']}{label}"]
        draft = attempt["draft"]
        if draft:
            out.append(f"  resolution: {draft['resolution']} | order: {draft['order_id']} | fingerprint {draft['fingerprint']}")
            out += _wrap(draft["reply_text"], indent="  | ")
            if draft["note_for_agent"]:
                out += _wrap(f"note for agent: {draft['note_for_agent']}", indent="  ")
        else:
            out.append(f"  (no draft) {attempt['error']}")
        out += ["", "  TRACE (tool calls)"]
        out += [f"    {c['tool']}({', '.join(f'{k}={v!r}' for k, v in c['args'].items())})" for c in attempt["trace"]] or ["    (none)"]
        out += ["", "  CHECKS"]
        for c in attempt["checks"]:
            out.append(f"    {'pass' if c['passed'] else 'FAIL':<5}{c['check']:<19}{c['severity']:<9}{c['question']}")
            for e in c["evidence"]:
                out += _wrap(e, indent="           -> ", hang="              ")
    verdict = "PASS" if result["passed"] else f"FAIL (worst severity: {result['worst_severity']})"
    out += ["", f"RESULT: {verdict}"]
    return out


def compare(runs: list[dict[str, Any]]) -> list[str]:
    names = [r["meta"]["candidate"] for r in runs]
    col = max(22, *(len(n) + 2 for n in names))
    meta = runs[0]["meta"]
    out = [f"Comparing on case set {meta['case_set_version']} (sha {meta['case_set_sha256']}), grader {meta['grader_version']}",
           f"Baseline: {names[0]}", ""]
    out.append(f"{'':<32}" + "".join(f"{n:>{col}}" for n in names))
    out.append(f"{'CASES PASSED':<32}" + "".join(f"{frac(sum(x['passed'] for x in r['results']), len(r['results'])):>{col}}" for r in runs))
    out += ["", "By case category (passed / total)"]
    cats = [by_category(r["results"]) for r in runs]
    for cat in cats[0]:
        out.append(f"  {cat:<30}" + "".join(f"{frac(*c[cat]):>{col}}" for c in cats))
    out += ["", "By check (cases failing / graded; lower is better)"]
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
    base = {r["case_id"]: r for r in runs[0]["results"]}
    for run in runs[1:]:
        fixed = [r["case_id"] for r in run["results"] if r["passed"] and not base[r["case_id"]]["passed"]]
        broke = [r for r in run["results"] if not r["passed"] and base[r["case_id"]]["passed"]]
        out += ["", f"{run['meta']['candidate']} vs {names[0]}:",
                f"  now passing ({len(fixed)}): {', '.join(fixed) or 'none'}",
                f"  newly failing ({len(broke)}): " + (", ".join(f"{r['case_id']} [{r['worst_severity']}]" for r in broke) or "none")]
    return out


def gate_report(decision) -> list[str]:
    out = ["Release gates (data/gates.json)"]
    for g in decision.gates:
        out += _wrap(f"{g.status.upper():<8}{g.id} {g.label}: {g.detail}", indent="  ", hang="            ")
    out += ["", f"DECISION: {decision.status}", f"  {decision.headline}"]
    out += [f"  - {s}" for s in decision.next_steps]
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
