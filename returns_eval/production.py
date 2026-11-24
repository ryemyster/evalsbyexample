"""Evaluate whole traces from production, not just drafts.

Offline, the eval grades one draft at a time. In production, a draft is one step
in a chain: look up the order, load the policy, draft, judge, route, a person
reviews, send. A perfect draft can still end badly if another step fails. So this
module reads ILLUSTRATIVE traces (data/production/) and asks questions about the
whole trajectory. Each check is a symptom; it doesn't say which layer is to blame.
Working that out (model, orchestration, policy, data, evaluator, or human review)
is the learner's job in Exercise 16.

It also compares production with the offline case set (are the test cases like
real traffic?) and applies the rollback triggers agreed before the canary started.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any

from .cases import DATA_DIR, available_policy_versions, load_case_set, load_policy
from .grading import CRITICAL, SEVERITY
from .report import _wrap, frac
from .stats import percentile

PRODUCTION_DIR = DATA_DIR / "production"
TRACES_FILE = PRODUCTION_DIR / "traces.ILLUSTRATIVE.jsonl"
TRIGGERS_FILE = PRODUCTION_DIR / "rollback_triggers.json"
LAYERS = ("model", "orchestration", "policy", "data", "evaluator", "human_review")


def load_traces(path: Path | None = None) -> list[dict[str, Any]]:
    path = Path(path or TRACES_FILE)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_triggers() -> dict[str, Any]:
    return json.loads(TRIGGERS_FILE.read_text(encoding="utf-8"))


def step(trace: dict[str, Any], name: str) -> dict[str, Any]:
    return next((s for s in trace["steps"] if s["step"] == name), {})


def policy_for(placed_on: str) -> str | None:
    """The policy version that applies to an order, worked out from the policy files themselves."""
    for version in sorted(available_policy_versions()):
        rule = load_policy(version)["applies_to_orders_placed"]
        if placed_on >= rule["on_or_after"] and (rule["before"] is None or placed_on < rule["before"]):
            return version
    return None


# Each check: (name, question, function returning an empty string if it passes, or the evidence if not).
def _draft_produced(t):
    d = step(t, "draft")
    return "" if d.get("status") == "ok" else f"no draft: the model step ended with '{d.get('status')}' after {d.get('ms')} ms"


def _right_policy(t):
    used, should = step(t, "load_policy").get("policy_version"), policy_for(t["order_placed_on"])
    return "" if used == should else f"used {used} for an order placed {t['order_placed_on']}; {should} applies"


def _own_orders_only(t):
    return "" if step(t, "lookup").get("all_owned_by_requester", True) else "looked up an order that belongs to someone else"


def _complete_record(t):
    return "" if step(t, "lookup").get("record_complete", True) else "the order record was missing information when drafted"


def _blocked_draft_not_sent(t):
    critical = [c for c in step(t, "draft").get("checks_failed", []) if SEVERITY.get(c) == CRITICAL]
    action = step(t, "human_review").get("action")
    return "" if not critical or action != "approved" else f"sent unchanged despite a critical check failure: {', '.join(critical)}"


def _judge_errors_not_counted_as_pass(t):
    j = step(t, "judge")
    if j.get("status") == "error" and j.get("recorded_as") == "ok":
        return "the judge failed, and the pipeline recorded its missing verdict as 'ok'"
    return ""


def _specialist_routed(t):
    if not t["needed_specialist"]:
        return ""
    queue = step(t, "route").get("queue")
    return "" if queue == "specialist" else f"needed a specialist but went to the {queue} queue"


def _real_review(t):
    r = step(t, "human_review")
    if r.get("action") == "approved" and r.get("seconds", 0) < 10:
        flagged = step(t, "judge").get("verdict") == "problem"
        return f"approved after {r['seconds']} seconds" + (", although the judge had flagged it" if flagged else "")
    return ""


def _right_ticket(t):
    sent = step(t, "send").get("ticket_id")
    return "" if sent == t["ticket_id"] else f"the reply for {t['ticket_id']} was sent to {sent}"


def _within_time(t):
    limit = load_triggers()["latency_budget_ms"]
    total = sum(s.get("ms", 0) for s in t["steps"] if s["step"] in ("lookup", "load_policy", "draft", "judge"))
    return "" if total <= limit else f"took {total} ms before a person saw anything; the limit is {limit} ms"


CHECKS = [
    ("draft_produced", "Did the agent get a draft at all?", _draft_produced),
    ("right_policy", "Was the policy version that applies to this order used?", _right_policy),
    ("own_orders_only", "Did it only look up the customer's own orders?", _own_orders_only),
    ("complete_record", "Was the order record complete when the draft was written?", _complete_record),
    ("blocked_draft_not_sent", "Was a draft that failed a critical check kept from going out unchanged?", _blocked_draft_not_sent),
    ("judge_errors_not_counted_as_pass", "When the judge failed, was that kept from counting as a pass?", _judge_errors_not_counted_as_pass),
    ("specialist_routed", "Did a request that needed a specialist reach the specialist queue?", _specialist_routed),
    ("real_review", "Did a person actually read the draft before approving it?", _real_review),
    ("right_ticket", "Did the reply go to the ticket it was written for?", _right_ticket),
    ("within_time", "Did the automated steps finish within the time limit?", _within_time),
]


def check_trace(t: dict[str, Any]) -> dict[str, str]:
    """{check name: evidence} for every check this trace fails."""
    return {name: problem for name, _, fn in CHECKS if (problem := fn(t))}


def specialist_routed(t: dict[str, Any]) -> bool:
    return not _specialist_routed(t)


def triggers_fired(traces: list[dict[str, Any]], deployment: str) -> list[tuple[dict[str, Any], str]]:
    rows = [t for t in traces if t["deployment"] == deployment]
    fired = []
    for trig in load_triggers()["triggers"]:
        if deployment not in trig["deployments"] or not rows:
            continue
        failing = [t["trace_id"] for t in rows if trig["check"] in check_trace(t)]
        if "max_failures" in trig and len(failing) > trig["max_failures"]:
            fired.append((trig, f"{frac(len(failing), len(rows))} traces: {', '.join(failing)}"))
        if "min_rate" in trig and (len(rows) - len(failing)) / len(rows) < trig["min_rate"]:
            fired.append((trig, f"{frac(len(rows) - len(failing), len(rows))} passed; need at least {trig['min_rate']:.0%}"))
    return fired


def _length_bucket(n: int) -> str:
    return "under 200" if n < 200 else "200 to 499" if n < 500 else "500 to 999" if n < 1000 else "1,000 or more"


def summary_lines(traces: list[dict[str, Any]], deployment: str | None = None) -> list[str]:
    deployments = [deployment] if deployment else sorted({t["deployment"] for t in traces}, key=lambda d: d != "production")
    out = ["ILLUSTRATIVE DATA: these traces are invented for teaching. They are not from a real system.", ""]
    span = sorted(t["date"] for t in traces)
    out.append(f"Production traces, {span[0]} to {span[-1]}: " + ", ".join(
        f"{d} {sum(t['deployment'] == d for t in traces)} tickets "
        f"({', '.join(sorted({t['candidate'] for t in traces if t['deployment'] == d}))})" for d in deployments))
    out.append("  production = what agents use today; canary = a small share of tickets on the new version")
    col = 22
    out += ["", f"{'':<44}" + "".join(f"{d:>{col}}" for d in deployments)]
    by = {d: [t for t in traces if t["deployment"] == d] for d in deployments}

    def row(label, fn):
        out.append(f"{label:<44}" + "".join(f"{fn(by[d]):>{col}}" for d in deployments))

    row("drafts produced", lambda rows: frac(sum(step(t, "draft").get("status") == "ok" for t in rows), len(rows)))
    row("model time per draft, median / p95", lambda rows: (
        lambda ms: f"{median(ms) / 1000:.1f} s / {percentile(ms, 0.95) / 1000:.1f} s")(
        [step(t, "draft")["ms"] for t in rows]))
    row("tokens per draft (in / out), median", lambda rows: (
        lambda ds: f"{median(x['input_tokens'] for x in ds):.0f} / {median(x['output_tokens'] for x in ds):.0f}"
        if ds else "-")([step(t, "draft") for t in rows if step(t, "draft").get("status") == "ok"]))
    row("agent sent the draft as written", lambda rows: frac(sum(step(t, "human_review").get("action") == "approved"
                                                                  for t in rows), len(rows)))
    row("customer wrote back within 7 days", lambda rows: frac(sum(t["outcome"]["reopened_within_7_days"] for t in rows),
                                                               len(rows)))

    out += ["", "Trajectory checks: traces that failed (a symptom, not a verdict on which layer is to blame)"]
    for name, question, _ in CHECKS:
        failing = {d: [t["trace_id"] for t in by[d] if name in check_trace(t)] for d in deployments}
        out.append(f"  {name:<42}" + "".join(f"{frac(len(failing[d]), len(by[d])):>{col}}" for d in deployments))
    out.append("")
    for d in deployments:
        for t in by[d]:
            for name, problem in check_trace(t).items():
                out += _wrap(f"{t['trace_id']} ({d}, {t['request_type']}) {name}: {problem}", indent="  ", hang="      ")

    cases = load_case_set().cases
    out += ["", "Are the test cases like real traffic? Customer message length, in characters"]
    out.append(f"  {'':<20}{'offline cases':>16}" + "".join(f"{d:>{col}}" for d in deployments))
    buckets = ("under 200", "200 to 499", "500 to 999", "1,000 or more")
    for b in buckets:
        c = sum(_length_bucket(len(x["message"])) == b for x in cases)
        out.append(f"  {b:<20}{frac(c, len(cases)):>16}" + "".join(
            f"{frac(sum(_length_bucket(t['message_chars']) == b for t in by[d]), len(by[d])):>{col}}" for d in deployments))
    longest = max(len(x["message"]) for x in cases)
    out += _wrap(f"The longest offline case message is {longest} characters. Anything that only goes wrong on longer "
                 "messages can't show up offline until a case like that is added.", indent="  ", hang="  ")

    out += ["", "Rollback triggers agreed before the canary (data/production/rollback_triggers.json)"]
    for d in deployments:
        fired = triggers_fired(traces, d)
        if not fired:
            out.append(f"  {d}: none fired")
        for trig, detail in fired:
            out += _wrap(f"{d}: {trig['id']} FIRED ({trig['check']}, {detail}). Agreed action: {trig['action']}",
                         indent="  ", hang="      ")
    out += ["", "How to read this"]
    out += _wrap("A failed check says what went wrong, not where. Open a trace to see each step "
                 "(python3 -m returns_eval traces --trace T-105) and decide which layer failed: the model, the "
                 "orchestration around it, the policy, the data, the evaluator, or human review. Each layer has a "
                 "different owner and a different fix.", indent="  ", hang="  ")
    return out


def trace_lines(t: dict[str, Any]) -> list[str]:
    out = ["ILLUSTRATIVE trace.", f"{t['trace_id']}  {t['deployment']}  {t['candidate']} {t['candidate_version']}  "
           f"{t['date']}  ticket {t['ticket_id']}",
           f"  request type: {t['request_type']} | message: {t['message_chars']} characters | order placed "
           f"{t['order_placed_on']} | needed a specialist: {'yes' if t['needed_specialist'] else 'no'}", "", "STEPS"]
    for s in t["steps"]:
        details = ", ".join(f"{k}={v}" for k, v in s.items() if k != "step")
        out += _wrap(f"{s['step']:<14}{details}", indent="  ", hang="                ")
    out.append(f"  outcome: customer wrote back within 7 days: {'yes' if t['outcome']['reopened_within_7_days'] else 'no'}")
    if t.get("note"):
        out += _wrap(f"note: {t['note']}", indent="  ", hang="        ")
    problems = check_trace(t)
    out += ["", "TRAJECTORY CHECKS"]
    for name, question, _ in CHECKS:
        out.append(f"  {'FAIL' if name in problems else 'pass':<5}{name:<34}{question}")
        if name in problems:
            out += _wrap(f"-> {problems[name]}", indent="         ", hang="            ")
    out += ["", f"Which layer failed? One of: {', '.join(LAYERS)}. (Exercise 16)"]
    return out
