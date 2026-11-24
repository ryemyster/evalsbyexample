"""The structured_output check: did the model's raw reply follow the agreed format?

Model-backed candidates return text that should contain one JSON object. The
adapter on the candidate side tidies that text up (for example, it turns an
unknown `resolution` into `escalate`). Tidying is useful in production, but it can
hide a broken model: a model that answers "approve_return" would look like a
careful model that escalates.

So the grader reads the raw text itself, with its own parser, and reports every
way it breaks the format. This code is written separately from the adapter on
purpose: a bug in one can't hide behind the same bug in the other.

The format (docs/llm-adapter.md): one JSON object, possibly with text, code
fences, or <think>...</think> reasoning around it, containing
  resolution      one of the allowed next steps
  order_id        a string, or null
  reply_text      a non-empty string
  note_for_agent  optional string
  actions         optional list of {"tool": name, "args": {...}}
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..models import RESOLUTIONS

_THINK = re.compile(r"<think>.*?</think>", re.IGNORECASE | re.DOTALL)


def _json_object(raw: str) -> tuple[dict[str, Any] | None, str | None]:
    text = _THINK.sub("", raw)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None, "The reply has no JSON object in it."
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        return None, f"The JSON in the reply can't be read ({exc.msg})."
    if not isinstance(data, dict):
        return None, "The JSON in the reply isn't an object with named fields."
    return data, None


def output_problems(raw: str) -> list[str]:
    """Every way the raw reply breaks the agreed format. Empty means it follows it."""
    data, problem = _json_object(raw)
    if problem:
        return [problem]
    problems = []
    resolution = data.get("resolution")
    if resolution not in RESOLUTIONS:
        problems.append(f"resolution is {resolution!r}, which isn't one of: {', '.join(RESOLUTIONS)}. "
                        "The adapter quietly changed it to 'escalate'.")
    if "order_id" not in data:
        problems.append("order_id is missing (use null when no order applies).")
    elif data["order_id"] is not None and not isinstance(data["order_id"], str):
        problems.append(f"order_id should be text or null, not {type(data['order_id']).__name__}.")
    reply = data.get("reply_text")
    if not isinstance(reply, str) or not reply.strip():
        problems.append("reply_text is missing or empty.")
    if "note_for_agent" in data and not isinstance(data["note_for_agent"], str):
        problems.append("note_for_agent should be text.")
    actions = data.get("actions")
    if actions is not None and (not isinstance(actions, list)
                                or not all(isinstance(a, dict) and isinstance(a.get("tool"), str) for a in actions)):
        problems.append('actions should be a list of {"tool": name, "args": {...}}.')
    return problems
