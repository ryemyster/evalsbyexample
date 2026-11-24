"""Automated judges: grading by a model against a written criterion. Part of grading.

Never imports candidate code. Built-in judges are SIMULATED (judging/simulated.py).
Bring a real one with playground/my_judge.py, or any module.path:ClassName.
"""

from __future__ import annotations

import importlib
from typing import Any

from .base import CRITERIA, LOW_CONFIDENCE, Judge, LLMJudge, prompt_problems
from .simulated import JudgeA, JudgeB

# EXTEND HERE: register a judge by name, or give any judge command module.path:ClassName.
# A model-backed judge only implements complete(prompt). See docs/extending.md#add-a-judge
BUILT_IN_JUDGES: dict[str, type[Judge]] = {JudgeA.name: JudgeA, JudgeB.name: JudgeB}


def load_judge(spec: str, prompt: str | None = None) -> Judge:
    if spec in BUILT_IN_JUDGES:
        cls = BUILT_IN_JUDGES[spec]
    elif ":" in spec:
        module_name, _, attr = spec.partition(":")
        try:
            cls = getattr(importlib.import_module(module_name), attr)
        except (ImportError, AttributeError) as exc:
            raise SystemExit(f"Could not load judge '{spec}': {exc}") from exc
    else:
        raise SystemExit(f"Unknown judge '{spec}'. Built-in judges: {', '.join(BUILT_IN_JUDGES)}. "
                         "Or use module.path:ClassName.")
    judge = cls(prompt) if issubclass(cls, LLMJudge) else cls()
    if not isinstance(judge, Judge):
        raise SystemExit(f"'{spec}' is not a Judge.")
    return judge


def with_case_context(items: list[dict[str, Any]], cases: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Add what a judge may read about the case: the customer's message and the reference."""
    out = []
    for item in items:
        case = cases[item["case_id"]]
        exp = case["expected"]
        groups = "; ".join(" | ".join(g) for g in exp["must_mention"])
        out.append({**item, "customer_message": case["message"], "must_mention": exp["must_mention"],
                    "reference": exp["behavior"] + (f"\nIt must mention (one phrase from each group, or the same "
                                                    f"meaning in other words): {groups}" if groups else "")})
    return out


def items_from_run(run: dict[str, Any], cases: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """One judge item per case in a saved run (the first attempt's draft)."""
    family = "sim" if run["meta"].get("simulated") else "script"
    items = []
    for r in run["results"]:
        draft = r["attempts"][0]["draft"]
        if draft is None:
            continue
        items.append({"item_id": r["case_id"], "case_id": r["case_id"], "segment": draft["resolution"],
                      "source": run["meta"]["candidate"], "family": family, "reply_text": draft["reply_text"],
                      "failed_checks": [c["check"] for c in r["attempts"][0]["checks"] if not c["passed"]]})
    return with_case_context(items, cases)


__all__ = ["BUILT_IN_JUDGES", "CRITERIA", "LOW_CONFIDENCE", "Judge", "LLMJudge", "load_judge", "prompt_problems",
           "with_case_context", "items_from_run"]
