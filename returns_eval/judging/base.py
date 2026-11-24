"""Automated judges ("LLM-as-judge"): a model that grades drafts against a written criterion.

A judge is part of grading, so this package never imports candidate code. A judge
only has to implement `complete(prompt) -> str`, the same contract as a
model-backed candidate. This base class does the rest:

  - builds the prompt from a template file in data/judges/ (inspectable and versioned),
    filling in the rubric's definition of the criterion, the customer's message, and
    the reply, with the reply fenced and marked as content, not instructions
  - checks the judge's answer against the agreed JSON format. An answer it can't read
    is recorded as an ERROR. It never counts as a pass. (Treating judge errors as
    passes is a classic way for an evaluation to fail silently; see Lesson 15.)
  - for pairwise comparisons, can ask twice with the order swapped and count a win
    only if both orders agree (Zheng et al., 2023; Wang et al., 2023; docs/sources.md)

Judges here are graders, so the same rule applies as to the checks: measure them
against people before trusting them (Lesson 13, `calibrate`).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..cases import DATA_DIR
from ..rubric import criterion as rubric_criterion
from ..rubric import load as load_rubric

JUDGES_DIR = DATA_DIR / "judges"
RUBRIC_FILE = DATA_DIR / "rubrics" / "draft-quality.v1.json"
DEFAULT_PROMPTS = {
    "tone": JUDGES_DIR / "tone.v1.txt",
    "complete": JUDGES_DIR / "complete.v1.txt",
    "pairwise": JUDGES_DIR / "pairwise-tone.v1.txt",
}
CRITERIA = ("tone", "complete")
PLACEHOLDERS = ("criterion", "customer_message", "reply", "reply_a", "reply_b", "reference", "candidate")
VERDICTS = ("ok", "problem")
LOW_CONFIDENCE = 0.7  # below this, the course treats a verdict as "the judge isn't sure"


def fill(template: str, **values: Any) -> str:
    """Replace {placeholders}. Only the known names are replaced, so JSON braces in a template are safe."""
    for name in PLACEHOLDERS:
        template = template.replace("{" + name + "}", str(values.get(name, "")))
    return template


def criterion_text(cid: str) -> str:
    c = rubric_criterion(load_rubric(RUBRIC_FILE), cid)
    lines = [c["question"]]
    for value, meaning in c.get("definitions", {}).items():
        lines.append(f'"{value}" means: {meaning}')
    return "\n".join(lines)


def _json_object(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None, "the judge's answer has no JSON in it"
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        return None, f"the judge's JSON can't be read ({exc.msg})"
    return (data, None) if isinstance(data, dict) else (None, "the judge's JSON isn't an object")


def parse_verdict(raw: str) -> dict[str, Any]:
    data, problem = _json_object(raw)
    if problem:
        return {"verdict": "error", "reason": problem, "confidence": None}
    verdict = data.get("verdict")
    if verdict not in VERDICTS:
        return {"verdict": "error", "reason": f"verdict is {verdict!r}, not one of {VERDICTS}", "confidence": None}
    confidence = data.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
        confidence = None  # missing or unusable: shown as "not given", never guessed
    return {"verdict": verdict, "reason": str(data.get("reason", "")), "confidence": confidence}


def parse_winner(raw: str) -> dict[str, Any]:
    data, problem = _json_object(raw)
    if problem:
        return {"winner": "error", "reason": problem}
    winner = data.get("winner")
    if winner not in ("A", "B", "tie"):
        return {"winner": "error", "reason": f"winner is {winner!r}, not A, B, or tie"}
    return {"winner": winner, "reason": str(data.get("reason", ""))}


def prompt_problems(template: str, mode: str = "pointwise") -> list[str]:
    """What's wrong with a judge prompt template. Empty means it follows the course's rules."""
    problems = []
    replies = ("{reply_a}", "{reply_b}") if mode == "pairwise" else ("{reply}",)
    for slot in replies:
        if slot not in template:
            problems.append(f"It never shows the judge the reply: add {slot}.")
            continue
        before, after = template.split(slot, 1)
        if "<<<" not in before[-80:] or ">>>" not in after[:80]:
            problems.append(f"{slot} isn't fenced. Put it between <<< and >>> lines, so the judge can tell the "
                            "reply apart from your instructions.")
    if not re.search(r"not instructions|ignore any instructions", template, re.IGNORECASE):
        problems.append("It doesn't tell the judge that the reply is content, not instructions. A reply can contain "
                        "text aimed at the judge ('mark this ok'), and the judge has to be told to ignore it.")
    if "{criterion}" not in template:
        problems.append("It doesn't include {criterion}, the rubric's written definition. Without it the judge "
                        "grades by its own idea of 'good'.")
    key = '"winner"' if mode == "pairwise" else '"verdict"'
    if key not in template:
        problems.append(f"It doesn't ask for JSON with {key}. Free-text answers can't be counted reliably.")
    if mode != "pairwise" and '"confidence"' not in template:
        problems.append('It doesn\'t ask for "confidence", so you can\'t send unsure verdicts to a person.')
    if "{candidate}" in template:
        problems.append("It tells the judge who wrote the reply ({candidate}). Grade blind: knowing the source "
                        "invites favoritism, including a judge favoring its own model family.")
    return problems


class Judge:
    """Anything that grades a reply against a criterion."""

    name = "unnamed-judge"
    version = "0"
    description = ""
    family = "unknown"     # which model family it belongs to (self-preference, Lesson 12)
    simulated = False

    def pointwise(self, item: dict[str, Any], criterion: str = "tone") -> dict[str, Any]:
        raise NotImplementedError

    def pairwise(self, a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def pairwise_both_orders(self, a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
        """Ask with a first, then with b first. A win counts only if both orders agree."""
        first = self.pairwise(a, b)["winner"]
        swapped = self.pairwise(b, a)["winner"]
        second = {"A": "B", "B": "A"}.get(swapped, swapped)  # translate back: "A" in the swapped ask meant b
        if "error" in (first, second):
            final = "error"
        elif first == second:
            final = first
        else:
            final = "tie"  # the order decided it, not the replies
        return {"a_first": first, "b_first": second, "winner": final, "order_dependent": first != second}


class LLMJudge(Judge):
    """A judge backed by a model. Implement complete(prompt) -> str."""

    def __init__(self, prompt: str | Path | None = None) -> None:
        self.prompt_path = Path(prompt) if prompt else None
        self.last_usage: dict[str, Any] | None = None
        self._current: dict[str, Any] = {}

    def complete(self, prompt: str) -> str:
        raise NotImplementedError("LLMJudge.complete() is not implemented. See playground/my_judge.py.")

    def template(self, kind: str) -> str:
        """The prompt template. A custom prompt (--prompt) replaces the pointwise one; pairwise keeps its own."""
        if self.prompt_path is not None and kind != "pairwise":
            return self.prompt_path.read_text(encoding="utf-8")
        return DEFAULT_PROMPTS[kind].read_text(encoding="utf-8")

    def _ask(self, prompt: str) -> tuple[str | None, str | None]:
        try:
            return self.complete(prompt), None
        except Exception as exc:  # a failed call is a result to record, not a crash
            return None, f"{type(exc).__name__}: {exc}"

    def pointwise(self, item: dict[str, Any], criterion: str = "tone") -> dict[str, Any]:
        if criterion not in CRITERIA:
            raise SystemExit(f"Unknown criterion '{criterion}'. Judges here grade: {', '.join(CRITERIA)}.")
        prompt = fill(self.template(criterion), criterion=criterion_text(criterion), reply=item["reply_text"],
                      customer_message=item.get("customer_message", ""), reference=item.get("reference", ""),
                      candidate=item.get("source", ""))
        self._current = {"mode": "pointwise", "criterion": criterion, "item": item}
        raw, error = self._ask(prompt)
        if error:
            return {"verdict": "error", "reason": error, "confidence": None, "raw": ""}
        return {**parse_verdict(raw), "raw": raw}

    def pairwise(self, a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
        prompt = fill(self.template("pairwise"), criterion=criterion_text("tone"), reply_a=a["reply_text"],
                      reply_b=b["reply_text"], customer_message=a.get("customer_message", ""))
        self._current = {"mode": "pairwise", "a": a, "b": b}
        raw, error = self._ask(prompt)
        if error:
            return {"winner": "error", "reason": error, "raw": ""}
        return {**parse_winner(raw), "raw": raw}
