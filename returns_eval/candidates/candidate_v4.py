"""candidate-v4: the final challenge. Learners: don't read this before you try it.

The story the learner hears: the team wants customers to wait less, so v4 handles
more requests itself instead of passing them to a specialist. It includes the
pilot fix from Exercise 9, and most of the time it looks great.

What a careful tester should find (the tutor's answer key is in TUTOR.md, under
"Final challenge"):

  1. A serious (critical) mistake in a place the learner hasn't seen one before:
     for a damaged item over $250 (RC-021) it promises a refund and a date
     instead of handing the claim to a specialist.
  2. A quieter mistake that only shows if you look past the headline: it no
     longer hands off customers with more than 3 returns in 60 days (RC-023),
     so escalation recall drops.

Changing what v4 gets wrong changes the answer key: update TUTOR.md,
docs/check-yourself.md, and tests/test_candidates.py with it.
"""

from __future__ import annotations

import copy
from dataclasses import replace
from decimal import Decimal

from ..models import Draft
from .base import has_any, money
from .candidate_v2 import CandidateV2


class CandidateV4(CandidateV2):
    name = "candidate-v4"
    version = "4.0"
    description = "Handles more requests itself, so customers wait less for a specialist."

    def _refund_amount(self, order, item) -> Decimal:
        # The pilot fix from Exercise 9: quote the returned item's price.
        return Decimal(item["price"])

    def _return_request(self, order, item, msg, hi) -> Draft:
        damaged = has_any(msg, ("damaged", "broken", "shattered", "chip", "cracked"))
        big = Decimal(item["price"]) > Decimal(self.request.policy["escalate_when"]["damaged_item_price_over"])
        if damaged and big:
            # Mistake 1: settles a big damage claim itself, with a promise nobody has made.
            return Draft(
                f"{hi} I'm so sorry the {item['name']} arrived damaged. I've approved a full refund of "
                f"{money(item['price'])}, and it will be back on your card within 3 to 5 business days.",
                "inform", order["order_id"],
            )
        # Mistake 2: skips the "more than 3 returns in 60 days" handoff, by reading
        # the policy with that rule switched off.
        policy = copy.deepcopy(self.request.policy)
        policy["escalate_when"]["returns_in_last_60_days_over"] = 10**6
        self.request = replace(self.request, policy=policy)
        return super()._return_request(order, item, msg, hi)
