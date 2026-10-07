"""Deterministic text extraction used by the checks.

These are deliberately simple regular expressions. They work for the phrasing
in this repo and for plain English replies generally, but they are not a
language model. When a judgment cannot be made reliably this way (is the tone
right? is this policy reading sensible?), it belongs on the human review
scorecard instead. See docs/grading.md.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december")
_MONTH_ALT = "|".join(MONTHS)

ORDER_ID_RES = (
    re.compile(r"\bEO-(\d{5})\b", re.IGNORECASE),
    re.compile(r"#(\d{5})\b"),
    re.compile(r"\border\s+(?:number\s+|no\.?\s*)?(\d{5})\b", re.IGNORECASE),
)
MONEY_RE = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+(?:\.\d{2})?)")
ISO_DATE_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
MONTH_DAY_RE = re.compile(rf"\b({_MONTH_ALT})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(\d{{4}}))?\b", re.IGNORECASE)

REFUND_ISSUED_RES = (
    re.compile(r"\brefund\b(?:[^.!?\n]|\.(?=\d)){0,40}?\b(?:has been|was|got|is now)\s+(?:issued|processed|sent|completed|approved)\b", re.IGNORECASE),
    re.compile(r"\b(?:we|i)(?:'ve|\s+have)\s+(?:issued|processed|sent|completed|approved)\s+(?:your|the|a)\s+(?:full\s+)?refund\b", re.IGNORECASE),
    re.compile(r"\byou(?:'ve|\s+have)\s+been\s+refunded\b", re.IGNORECASE),
)

_DAYS = r"(?:business\s+|working\s+)?days?"
_RANGE = r"\d+(?:\s*(?:-|–|to)\s*\d+)?"
TIMING_RES = (
    re.compile(rf"\bwithin\s+{_RANGE}\s+{_DAYS}\b", re.IGNORECASE),
    re.compile(rf"\bin\s+{_RANGE}\s+{_DAYS}\b", re.IGNORECASE),
    re.compile(rf"\b\d+\s*(?:-|–|to)\s*\d+\s+{_DAYS}\b", re.IGNORECASE),
    re.compile(r"\bwithin\s+(?:a|one|two|a few)\s+(?:days?|weeks?)\b", re.IGNORECASE),
    re.compile(rf"\bby\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|tonight|"
               rf"the end of (?:the )?(?:day|week)|end of (?:day|week)|{_MONTH_ALT}|\d{{4}}-\d{{2}}-\d{{2}})\b", re.IGNORECASE),
    re.compile(r"\b(?:today|tomorrow|tonight)\b", re.IGNORECASE),
)

RECEIPT_CLAIM_RE = re.compile(
    r"\b(?:we(?:'ve|\s+have)?\s+(?:received|got)\s+your\s+return|your\s+return\s+(?:has\s+)?"
    r"(?:arrived|been\s+received|was\s+received))\b",
    re.IGNORECASE,
)


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def contains_phrase(text: str, phrase: str, case_sensitive: bool = False) -> bool:
    """True if `phrase` appears in `text` as a whole word or words.

    "July 2" does not match "July 20", and "check" does not match "checking".
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text, flags) is not None


def order_ids_in(text: str) -> set[str]:
    found: set[str] = set()
    for pattern in ORDER_ID_RES:
        found.update(f"EO-{digits}" for digits in pattern.findall(text))
    return found


def amounts_in(text: str) -> list[Decimal]:
    return [Decimal(m.replace(",", "")).quantize(Decimal("0.01")) for m in MONEY_RE.findall(text)]


def dates_in(text: str, default_year: int) -> list[date]:
    found: list[date] = []
    for y, m, d in ISO_DATE_RE.findall(text):
        found.append(date(int(y), int(m), int(d)))
    for month, day, year in MONTH_DAY_RE.findall(text):
        try:
            found.append(date(int(year) if year else default_year, MONTHS.index(month.lower()) + 1, int(day)))
        except ValueError:
            continue  # "May 45" is not a date; ignore it
    return found


def refund_issued_claims(text: str) -> list[str]:
    hits = []
    for pattern in REFUND_ISSUED_RES:
        hits.extend(m.group(0) for m in pattern.finditer(text))
    return hits


FOLLOW_ON_RE = re.compile(r"^(?:it|this|that|the money|the funds|you'll see it|you will see it)\b", re.IGNORECASE)


def refund_timing_promises(text: str) -> list[str]:
    """Sentences that attach a time commitment to a refund.

    A sentence counts if it mentions a refund, or if it starts with "It"/"This"/
    "The money" right after a sentence that does ("Your refund is on its way.
    It should arrive within 5 days.").
    """
    hits = []
    previous_mentions_refund = False
    for sentence in sentences(text):
        mentions_refund = re.search(r"\brefund", sentence, re.IGNORECASE) is not None
        about_refund = mentions_refund or (previous_mentions_refund and FOLLOW_ON_RE.search(sentence))
        if about_refund and any(p.search(sentence) for p in TIMING_RES):
            hits.append(sentence)
        previous_mentions_refund = mentions_refund
    return hits


def receipt_claims(text: str) -> list[str]:
    return [m.group(0) for m in RECEIPT_CLAIM_RE.finditer(text)]
