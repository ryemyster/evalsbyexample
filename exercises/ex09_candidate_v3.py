"""Exercise 9 (step 9): fix the candidate, then rerun EVERY case.

The pilot found that candidate-v2 quotes the order total as the refund even when
the customer returns only one item (incident PI-001, case RC-027). Fix it here,
without editing candidate-v2 itself, by overriding one method.

`item` is the item the customer is returning (candidate-v2 already picks it from
the message). Return the amount to quote, as a Decimal.

    python3 -m exercises 9
    python3 -m returns_eval run --candidate exercises.ex09_candidate_v3:CandidateV3

The second command runs the full case set, including RC-027 if you added it in
Exercise 8. A fix that passes RC-027 but breaks another case is not a fix.
"""

from decimal import Decimal

from returns_eval.candidates.candidate_v2 import CandidateV2


class CandidateV3(CandidateV2):
    name = "candidate-v3"
    version = "3.0"
    description = "candidate-v2 plus the pilot fix: quote the returned item's price, not the order total."

    def _refund_amount(self, order: dict, item: dict) -> Decimal:
        raise NotImplementedError("implement CandidateV3._refund_amount()")
