"""Exercise 3 (step 5): write a deterministic check.

Policy says: never promise a refund date or a number of days. Write a function
that finds every sentence in a reply that does.

    python3 -m exercises 3

Rules your function should follow (the tests check each one):
1. Split the reply into sentences (split after . ! or ? followed by a space).
2. A sentence is "about a refund" if it contains the word refund (any case,
   "refunds" and "refunded" count too).
3. A sentence about a refund is a promise if it contains a time commitment, such as
   "within 5 days", "in 3 business days", "5-7 business days", "by Friday",
   "by August 20", "today", or "tomorrow".
4. "It should arrive within 5 days." also counts when the sentence right before it
   is about a refund. Treat a sentence that starts with "It" or "This" that way.
5. Return the matching sentences, in order. Return [] if there are none.

The real check lives in returns_eval/grading/text.py. Try not to look until you've
written your own; then compare.
"""

import re  # noqa: F401  (you will probably want it)


def find_refund_timing_promises(reply_text: str) -> list[str]:
    raise NotImplementedError("implement find_refund_timing_promises()")
