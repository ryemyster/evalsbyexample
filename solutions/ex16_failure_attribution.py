"""Reference solution for Exercise 16."""

LAYERS = ("model", "orchestration", "policy", "data", "evaluator", "human_review")


def specialist_routed(trace):
    if not trace["needed_specialist"]:
        return True
    route = next((s for s in trace["steps"] if s["step"] == "route"), {})
    return route.get("queue") == "specialist"


ATTRIBUTION = {
    "T-105": "orchestration",            # the ticket merge sent the reply to another ticket
    "T-109": "policy",                   # a stale policy version was served after a restart
    "T-112": "data",                     # the delivery date hadn't synced yet
    "T-115": "evaluator",                # judge errors were recorded as passes
    "T-120": "human_review",             # approved in 3 seconds despite the judge's flag
    "T-124": "model",                    # drafted 'inform' for a chargeback threat
    "T-203": ["model", "orchestration"],  # the model timed out on a long message, and the fallback dropped the escalation
}

NEW_OFFLINE_CASES = ["T-124", "T-203"]

T122 = ("No. The model made a critical mistake, but the critical check blocked the draft and the agent wrote a new "
        "reply, so the system did its job. It's still worth counting how often the model does it.")
