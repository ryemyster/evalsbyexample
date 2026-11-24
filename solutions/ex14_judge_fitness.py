"""Reference solution for Exercise 14. Other decisions can be right too; the test checks
that a decision is consistent with the measured evidence, not that it matches this one."""


def confusion(truth, verdicts):
    cm = {"tp": 0, "fn": 0, "fp": 0, "tn": 0}
    for t, v in zip(truth, verdicts):
        if t == "problem":
            cm["tp" if v == "problem" else "fn"] += 1
        else:
            cm["fp" if v == "problem" else "tn"] += 1
    return cm


def recall_precision(cm):
    recall = cm["tp"] / (cm["tp"] + cm["fn"]) if cm["tp"] + cm["fn"] else None
    precision = cm["tp"] / (cm["tp"] + cm["fp"]) if cm["tp"] + cm["fp"] else None
    return recall, precision


DECISION = {
    "use": "auto-pass",
    "judge": "judge-b",
    "worse_mistake": "missed problem",
    "min_recall": 0.85,
    "send_to_people_below_confidence": None,
    "people_always_review": ["ask_customer"],
    "holdout_confirms": "yes",
    "why": ("If drafts the judge passes skip a person, a missed rude reply goes straight to a customer, so misses cost "
            "more than false alarms. On calibration, judge-b caught 7 of 8 problems; its only miss was sarcasm with no "
            "telltale words, in ask_customer, so people keep reviewing that segment. On holdout it missed one more, in "
            "inform, which still leaves 8 of 9 reaching a person. Its false alarms on polite refusals cost reviewer "
            "time, which the budget has to cover."),
}
