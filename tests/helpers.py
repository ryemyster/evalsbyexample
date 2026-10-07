from returns_eval.cases import CASES_DIR, load_case_set

CORE = load_case_set([CASES_DIR / "core.jsonl"])
CASES = {c["id"]: c for c in CORE.cases}


def draft(text, resolution="inform", order_id=None):
    return {"reply_text": text, "resolution": resolution, "order_id": order_id, "note_for_agent": "", "fingerprint": "x"}


def attempt(text, resolution="inform", order_id=None, trace=None):
    return {"draft": draft(text, resolution, order_id), "trace": trace or [], "error": None}
