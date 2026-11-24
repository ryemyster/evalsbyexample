"""Evaluate the evaluator: compare a judge's verdicts with people's labels.

"Problem" is the positive class: it's what the judge is looking for. So:
  caught           people say problem, judge says problem
  missed           people say problem, judge says ok      (false acceptance)
  false alarm      people say ok, judge says problem      (false rejection)
  correctly passed people say ok, judge says ok

Overall agreement hides which kind of mistake a judge makes, and which kind
matters depends on how you'll use it. So the report always shows the four counts,
recall and precision, agreement beyond chance, results by segment, and results by
the judge's own confidence. Small samples carry 95% ranges (Wilson). Nothing here
says what number is "good enough": that depends on what a missed problem and a
false alarm each cost you, which is the learner's call (Exercise 14).
"""

from __future__ import annotations

from typing import Any

from ..report import _wrap, frac
from ..stats import cohen_kappa, confusion, rates, wilson
from .base import LOW_CONFIDENCE, Judge

POSITIVE = "problem"


def judge_items(judge: Judge, items: list[dict[str, Any]], criterion: str = "tone") -> list[dict[str, Any]]:
    return [judge.pointwise(item, criterion) for item in items]


def summarize(items: list[dict[str, Any]], verdicts: list[dict[str, Any]]) -> dict[str, Any]:
    """Everything the report shows, for one judge on one set of labeled items."""
    truth = [i["final"] for i in items]
    said = [v["verdict"] for v in verdicts]
    usable = [(t, s) for t, s in zip(truth, said) if s != "error"]
    cm = confusion([t for t, _ in usable], [s for _, s in usable], POSITIVE)
    segments = {}
    for seg in sorted({i["segment"] for i in items}):
        pairs = [(t, s) for i, t, s in zip(items, truth, said) if i["segment"] == seg and s != "error"]
        segments[seg] = {"n": len(pairs), **confusion([t for t, _ in pairs], [s for _, s in pairs], POSITIVE)}
    low = [(t, s) for t, s, v in zip(truth, said, verdicts)
           if s != "error" and v["confidence"] is not None and v["confidence"] < LOW_CONFIDENCE]
    high = [(t, s) for t, s, v in zip(truth, said, verdicts)
            if s != "error" and v["confidence"] is not None and v["confidence"] >= LOW_CONFIDENCE]
    return {
        "n": len(items), "errors": said.count("error"), "cm": cm, "rates": rates(cm),
        "agree": sum(t == s for t, s in usable), "kappa": cohen_kappa([t for t, _ in usable], [s for _, s in usable]),
        "segments": segments,
        "low": (sum(t == s for t, s in low), len(low)), "high": (sum(t == s for t, s in high), len(high)),
        "no_confidence": sum(v["confidence"] is None for v in verdicts if v["verdict"] != "error"),
        "wrong": [(i["item_id"], i["segment"], v["verdict"], i["final"], v["reason"])
                  for i, v in zip(items, verdicts) if v["verdict"] != i["final"]],
    }


def _range(k: int, n: int) -> str:
    if not n:
        return "n/a"
    lo, hi = wilson(k, n)
    return f"{lo:.0%} to {hi:.0%}"


def report_lines(named: dict[str, dict[str, Any]], split: str, label_count: int, criterion: str = "tone") -> list[str]:
    names = list(named)
    col = max(20, *(len(n) + 4 for n in names))
    s0 = named[names[0]]
    out = [f"Judge calibration: '{criterion}' on the {split} split ({label_count} drafts labeled by people)",
           "ILLUSTRATIVE labels. SIMULATED judges are scripts, not language models.",
           "'problem' is what the judge looks for. Each number compares the judge with the people's final label.", ""]
    out.append(f"{'':<36}" + "".join(f"{n:>{col}}" for n in names))

    def row(label: str, fn) -> None:
        out.append(f"{label:<36}" + "".join(f"{fn(named[n]):>{col}}" for n in names))

    row("agreed with people", lambda s: frac(s["agree"], s["n"] - s["errors"]))
    row("  95% range for that agreement", lambda s: _range(s["agree"], s["n"] - s["errors"]))
    row("agreement beyond chance (kappa)", lambda s: "n/a" if s["kappa"] is None else f"{s['kappa']:.2f}")
    out.append("")
    row("problems caught (recall)", lambda s: frac(s["cm"]["tp"], s["cm"]["tp"] + s["cm"]["fn"]))
    row("  95% range", lambda s: _range(s["cm"]["tp"], s["cm"]["tp"] + s["cm"]["fn"]))
    row("flags that were real (precision)", lambda s: frac(s["cm"]["tp"], s["cm"]["tp"] + s["cm"]["fp"]))
    row("ok drafts passed (specificity)", lambda s: frac(s["cm"]["tn"], s["cm"]["tn"] + s["cm"]["fp"]))
    row("F1 (one number for both)", lambda s: "n/a" if s["rates"]["f1"] is None else f"{s['rates']['f1']:.2f}")
    out.append("")
    row("missed problems (false acceptance)", lambda s: str(s["cm"]["fn"]))
    row("false alarms (false rejection)", lambda s: str(s["cm"]["fp"]))
    row("unreadable answers (judge errors)", lambda s: str(s["errors"]))

    out += ["", "By segment (the draft's next step): missed / false alarms, of drafts in the segment"]
    for seg in s0["segments"]:
        n_problem = s0["segments"][seg]["tp"] + s0["segments"][seg]["fn"]
        label = f"  {seg} ({s0['segments'][seg]['n']}, {n_problem} problem)"
        out.append(f"{label:<36}" + "".join(
            f"{str(named[n]['segments'][seg]['fn']) + ' missed / ' + str(named[n]['segments'][seg]['fp']) + ' false':>{col}}"
            for n in names))

    out += ["", f"By the judge's own confidence (low = below {LOW_CONFIDENCE}): agreed with people"]
    row("  high confidence", lambda s: frac(*s["high"]))
    row("  low confidence", lambda s: frac(*s["low"]))
    if any(named[n]["no_confidence"] for n in names):
        row("  no confidence given", lambda s: str(s["no_confidence"]))

    for n in names:
        if named[n]["wrong"]:
            out += ["", f"Where {n} disagreed with people"]
            for item_id, seg, said, truth, reason in named[n]["wrong"]:
                kind = "error" if said == "error" else ("missed" if truth == POSITIVE else "false alarm")
                out += _wrap(f"{item_id} {seg:<15}{kind:<12}judge: {reason}", indent="  ", hang="      ")
    out += ["", "How to read this"]
    out += _wrap("Agreement can be the same for two judges that fail in opposite ways. Decide which mistake "
                 "costs more where you'll use the judge: a missed problem reaches a customer unless a person "
                 "catches it; a false alarm costs a person's time. There's no universal 'good enough' number.",
                 indent="  ", hang="  ")
    if split != "holdout":
        out += _wrap("Tune and decide on the calibration split. Run the holdout split once, at the end, to "
                     "check the decision. If you keep adjusting until the holdout looks good, it stops being a fair test.",
                     indent="  ", hang="  ")
    return out
