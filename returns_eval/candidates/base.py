"""Base class and small helpers for candidates.

A candidate is anything that turns a Request into a Draft. The grader never
imports from this package, and these helpers are never used by the grader. If a
date helper here had a bug, the grader computes its own dates and would catch it.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from ..models import Draft, Request
from ..tools import Toolbox


class Candidate:
    """Subclass this and implement draft_reply."""

    name = "unnamed"
    version = "0"
    description = ""

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        raise NotImplementedError


# --- helpers shared by the scripted candidates -------------------------------

_ORDER_NUMBER_RE = re.compile(r"(?:EO-|#|\border\s+(?:number\s+|no\.?\s*)?)?\b(\d{5})\b", re.IGNORECASE)


def order_numbers_in(text: str) -> list[str]:
    """Order numbers a customer typed, normalized to EO-xxxxx."""
    seen: list[str] = []
    for digits in _ORDER_NUMBER_RE.findall(text):
        oid = f"EO-{digits}"
        if oid not in seen:
            seen.append(oid)
    return seen


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def nice_date(value: str | date) -> str:
    d = parse_date(value) if isinstance(value, str) else value
    return f"{d:%B} {d.day}"


def plus_days(value: str, days: int) -> date:
    return parse_date(value) + timedelta(days=days)


def money(amount: Decimal | str) -> str:
    return f"${Decimal(amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def has_any(text: str, words: tuple[str, ...]) -> bool:
    low = text.lower()
    return any(w in low for w in words)


def item_words(name: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", name.lower()) if len(w) > 2}


def describe(order: dict[str, Any]) -> str:
    names = ", ".join(i["name"] for i in order["items"])
    return f"{order['order_id']} ({names})"
