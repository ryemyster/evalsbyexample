"""Reference solution for Exercise 3."""

import re

TIME_COMMITMENT = re.compile(
    r"\b(?:within|in)\s+\d+(?:\s*(?:-|–|to)\s*\d+)?\s+(?:business\s+|working\s+)?days?\b"
    r"|\b\d+\s*(?:-|–|to)\s*\d+\s+(?:business\s+|working\s+)?days?\b"
    r"|\bby\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|"
    r"january|february|march|april|may|june|july|august|september|october|november|december)\b"
    r"|\b(?:today|tomorrow)\b",
    re.IGNORECASE,
)


def find_refund_timing_promises(reply_text: str) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", reply_text) if s.strip()]
    hits = []
    previous_about_refund = False
    for sentence in sentences:
        about_refund = re.search(r"\brefund", sentence, re.IGNORECASE) is not None
        follow_on = previous_about_refund and re.match(r"(?:it|this)\b", sentence, re.IGNORECASE)
        if (about_refund or follow_on) and TIME_COMMITMENT.search(sentence):
            hits.append(sentence)
        previous_about_refund = about_refund
    return hits
