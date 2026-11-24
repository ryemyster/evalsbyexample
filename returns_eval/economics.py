"""What will checking cost each week, and how many problems will still get through?

An evaluation plan mixes three kinds of checking:
  code checks    run on every draft, cost almost nothing, and enforce the critical gates
  a judge        cheap per draft, but it misses some problems and flags some fine drafts
  people         the most trusted and the most expensive

This module takes a plan (which judge, which drafts people see), the judge's
MEASURED error rates per segment (from the labeled drafts, computed fresh each time),
and ASSUMED volumes and prices (data/economics/costs.ILLUSTRATIVE.json), and works
out the expected weekly cost and the expected problems nobody sees. Every line says
whether its number was measured or assumed.

The model is deliberately simple: each segment's problems and fine drafts are
handled at the judge's measured rates for that segment. It ignores that rates on a
few dozen labeled drafts are uncertain, so the report shows how many labeled drafts
each rate rests on.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .cases import DATA_DIR
from .judging import LOW_CONFIDENCE, load_judge, with_case_context
from .labels import load_items
from .report import _wrap

COSTS_FILE = DATA_DIR / "economics" / "costs.ILLUSTRATIVE.json"
PRICES_FILE = DATA_DIR / "economics" / "prices.ILLUSTRATIVE.json"
WEEKS_PER_MONTH = 52 / 12


def load_costs(path: Path | None = None) -> dict[str, Any]:
    return json.loads(Path(path or COSTS_FILE).read_text(encoding="utf-8"))


def judge_rates(judge_name: str, split: str, cases: dict[str, dict[str, Any]], threshold: float | None
                ) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    """Per segment: how the judge treats problems and fine drafts, measured on labeled drafts.

    flag_p   share of problems it flags          seen_p  share of problems a person sees via flag or unsure
    flag_ok  share of fine drafts it flags       seen_ok share of fine drafts sent to a person
    """
    splits = split.split("+")
    items = with_case_context([i for s in splits for i in load_items(split=s)], cases)
    judge = load_judge(judge_name)
    verdicts = [judge.pointwise(i) for i in items]
    tokens = judge.last_usage or {}  # one typical call: the last one made
    rates: dict[str, dict[str, float]] = {}
    for seg in sorted({i["segment"] for i in items}):
        rows = [(i, v) for i, v in zip(items, verdicts) if i["segment"] == seg]
        probs = [v for i, v in rows if i["final"] == "problem"]
        oks = [v for i, v in rows if i["final"] == "ok"]

        def unsure(v):
            return threshold is not None and v["confidence"] is not None and v["confidence"] < threshold

        rates[seg] = {
            "n_problem": len(probs), "n_ok": len(oks),
            "flag_p": sum(v["verdict"] == "problem" for v in probs) / len(probs) if probs else None,
            "unsure_p": sum(v["verdict"] != "problem" and unsure(v) for v in probs) / len(probs) if probs else None,
            "flag_ok": sum(v["verdict"] == "problem" for v in oks) / len(oks) if oks else 0.0,
            "unsure_ok": sum(v["verdict"] != "problem" and unsure(v) for v in oks) / len(oks) if oks else 0.0,
        }
    all_p = [v for i, v in zip(items, verdicts) if i["final"] == "problem"]
    overall = {"flag_p": sum(v["verdict"] == "problem" for v in all_p) / len(all_p),
               "unsure_p": sum(v["verdict"] != "problem" and threshold is not None and v["confidence"] is not None
                               and v["confidence"] < threshold for v in all_p) / len(all_p)}
    for r in rates.values():  # a segment with no labeled problems borrows the overall rate, marked in the report
        r["borrowed"] = r["flag_p"] is None
        if r["borrowed"]:
            r["flag_p"], r["unsure_p"] = overall["flag_p"], overall["unsure_p"]
    usage = {"input_tokens": tokens.get("input_tokens", 0), "output_tokens": tokens.get("output_tokens", 0),
             "price_key": tokens.get("price_key"), "labeled": len(items), "split": split}
    return rates, usage


def plan_problems(plan: dict[str, Any], command_names: set[str]) -> list[str]:
    problems = []
    if plan.get("code_checks_share") != 1.0:
        problems.append("code_checks_share must be 1.0: the code checks enforce the critical gates and cost almost "
                        "nothing, so every draft gets them.")
    if plan.get("judge") not in (None, "judge-a", "judge-b"):
        problems.append('judge must be "judge-a", "judge-b", or null (no judge).')
    if plan.get("measured_on") not in ("calibration", "holdout", "calibration+holdout"):
        problems.append('measured_on must be "calibration", "holdout", or "calibration+holdout".')
    for key in ("judge_share", "people_random_share"):
        for seg, share in (plan.get(key) or {}).items():
            if not isinstance(share, (int, float)) or not 0 <= share <= 1:
                problems.append(f"{key}.{seg} must be a share between 0 and 1.")
    evidence = plan.get("evidence") or []
    if len(evidence) < 2:
        problems.append("evidence needs at least two entries, each a claim and the command that shows it.")
    for e in evidence:
        claim, command = str(e.get("claim", "")), str(e.get("command", ""))
        m = re.match(r"python3 -m returns_eval ([a-z-]+)", command)
        if "TODO" in claim + command or not claim.strip():
            problems.append("an evidence entry still has a TODO or an empty claim.")
        elif not m or m.group(1) not in command_names:
            problems.append(f"evidence command isn't a course command: {command!r}")
    if "TODO" in str(plan.get("why", "TODO")) or len(str(plan.get("why", "")).split()) < 20:
        problems.append("why: explain the plan in a few sentences, pointing at measured numbers.")
    return problems


def evaluate(plan: dict[str, Any], costs: dict[str, Any], rates: dict[str, dict[str, float]] | None,
             usage: dict[str, Any] | None) -> dict[str, Any]:
    """Expected weekly reviews, cost, and problems nobody sees, per segment and in total."""
    person = costs["person"]
    prices = json.loads(PRICES_FILE.read_text(encoding="utf-8"))["per_million_tokens"]
    flags, unsure = plan.get("people_check_flags", True), plan.get("people_check_unsure_below") is not None
    rows, totals = {}, {"drafts": 0.0, "problems": 0.0, "missed": 0.0, "flag_reviews": 0.0, "random_checks": 0.0,
                        "judged": 0.0}
    for seg, share in costs["segment_share"].items():
        n = costs["weekly_drafts"] * share
        p = n * costs["tone_problem_rate"][seg]
        ok = n - p
        j = (plan.get("judge_share") or {}).get(seg, 1.0) if plan.get("judge") else 0.0
        rnd = (plan.get("people_random_share") or {}).get(seg, 0.0)
        r = (rates or {}).get(seg) or {"flag_p": 0, "unsure_p": 0, "flag_ok": 0, "unsure_ok": 0}
        seen_p = (r["flag_p"] if flags else 0) + (r["unsure_p"] if unsure else 0)
        seen_ok = (r["flag_ok"] if flags else 0) + (r["unsure_ok"] if unsure else 0)
        flag_reviews = j * (p * seen_p + ok * seen_ok)
        # people's random checks cover drafts not already sent to them
        random_checks = rnd * (n - flag_reviews)
        missed = p * (j * (1 - seen_p) + (1 - j)) * (1 - rnd)
        rows[seg] = {"drafts": n, "problems": p, "judged": n * j, "flag_reviews": flag_reviews,
                     "random_checks": random_checks, "missed": missed, "borrowed": r.get("borrowed", False),
                     "n_problem": r.get("n_problem")}
        for k in totals:
            totals[k] += rows[seg][k]
    people_usd = (totals["flag_reviews"] * person["minutes_per_flag_review"]
                  + totals["random_checks"] * person["minutes_per_tone_check"]) * person["usd_per_minute"]
    judge_usd = 0.0
    if plan.get("judge") and usage and usage.get("price_key") in prices:
        price = prices[usage["price_key"]]
        judge_usd = totals["judged"] * (usage["input_tokens"] * price["input"] + usage["output_tokens"] * price["output"]) / 1e6
    rl = costs["relabeling"]
    relabel_usd = (plan.get("relabel_drafts_per_month", 0) * rl["minutes_per_draft"] * rl["annotators"]
                   * person["usd_per_minute"]) / WEEKS_PER_MONTH
    eval_usd = people_usd + judge_usd + relabel_usd
    resolved = costs["weekly_drafts"] * costs["resolved_share"]
    return {"rows": rows, "totals": totals, "people_usd": people_usd, "judge_usd": judge_usd,
            "relabel_usd": relabel_usd, "eval_usd": eval_usd,
            "mistake_usd": totals["missed"] * costs["cost_of_a_rude_reply_sent_usd"],
            "per_resolved_usd": (eval_usd + costs["weekly_drafts"] * costs["drafting_usd_per_draft"]) / resolved,
            "per_caught_usd": eval_usd / max(totals["problems"] - totals["missed"], 1e-9)}


def report_lines(plan: dict[str, Any], costs: dict[str, Any], result: dict[str, Any], references: dict[str, dict[str, Any]],
                 usage: dict[str, Any] | None, problems: list[str]) -> list[str]:
    t = result["totals"]
    out = [f"Evaluation budget for: {plan.get('plan', 'your plan')}",
           "ILLUSTRATIVE: volumes, problem rates, and costs are made-up assumptions (data/economics/costs.ILLUSTRATIVE.json).",
           f"MEASURED: the judge's error rates come from {usage['labeled']} labeled drafts ({usage['split']} split)."
           if usage else "No judge in this plan.", ""]
    out.append(f"{'segment':<16}{'drafts':>8}{'problems':>10}{'judged':>8}{'to people':>11}{'missed':>9}   labeled problems")
    for seg, r in result["rows"].items():
        note = "-" if not plan.get("judge") else f"{r['n_problem']}" + (" (overall rate used)" if r["borrowed"] else "")
        out.append(f"{seg:<16}{r['drafts']:>8.0f}{r['problems']:>10.1f}{r['judged']:>8.0f}"
                   f"{r['flag_reviews'] + r['random_checks']:>11.0f}{r['missed']:>9.1f}   {note}")
    out.append(f"{'total':<16}{t['drafts']:>8.0f}{t['problems']:>10.1f}{t['judged']:>8.0f}"
               f"{t['flag_reviews'] + t['random_checks']:>11.0f}{t['missed']:>9.1f}")
    budget, cap = costs["weekly_budget_usd"], costs["team_max_missed_per_week"]
    def money(label: str, usd: float, extra: str = "") -> str:
        return f"  {label:<58}${usd:>8.2f}{extra}"

    out += ["", "Weekly cost of checking (ILLUSTRATIVE prices)",
            money(f"people: {t['flag_reviews']:.0f} flag or unsure reviews, {t['random_checks']:.0f} spot checks",
                  result["people_usd"]),
            money(f"judge: {t['judged']:.0f} calls", result["judge_usd"]),
            money(f"fresh labels to recheck the judge ({plan.get('relabel_drafts_per_month', 0)} drafts a month)",
                  result["relabel_usd"]),
            money("total", result["eval_usd"], f"   budget ${budget}"),
            "", "What it buys",
            f"  {'tone problems expected per week':<58}{t['problems']:>9.1f}   (assumed; see the costs file)",
            f"  {'problems nobody sees':<58}{t['missed']:>9.1f}   team limit {cap}",
            money("cost per problem caught", result["per_caught_usd"]),
            money("cost per resolved ticket (drafting + checking)", result["per_resolved_usd"]),
            money(f"misses, if each costs ${costs['cost_of_a_rude_reply_sent_usd']} (ILLUSTRATIVE)", result["mistake_usd"])]
    out += ["", "For comparison (same assumptions)"]
    for name, ref in references.items():
        out.append(f"  {name:<40}${ref['eval_usd']:>8.2f} a week, {ref['totals']['missed']:>5.1f} problems nobody sees")
    over = result["eval_usd"] > budget
    many = t["missed"] > cap
    out += [""]
    if problems:
        out.append("Plan problems:")
        out += [line for p in problems for line in _wrap(p, indent="  - ", hang="    ")]
    verdict = ("WITHIN BUDGET AND LIMIT" if not over and not many and not problems else
               "NOT YET: " + ", ".join(x for x, bad in (("over budget", over), ("too many missed", many),
                                                         ("plan problems", bool(problems))) if bad))
    out.append(f"PLAN: {verdict}")
    out += _wrap("Uncertainty: each judge rate rests on a handful of labeled drafts per segment, so treat 'missed' as a "
                 "rough estimate. Spot-check real traffic and relabel regularly to keep it honest.", indent="  ", hang="  ")
    return out
