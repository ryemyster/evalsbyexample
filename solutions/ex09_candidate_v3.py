"""Reference solution for Exercise 9."""

from decimal import Decimal

from returns_eval.candidates.candidate_v2 import CandidateV2


class CandidateV3(CandidateV2):
    name = "candidate-v3"
    version = "3.0"
    description = "candidate-v2 plus the pilot fix: quote the returned item's price, not the order total."

    def _refund_amount(self, order: dict, item: dict) -> Decimal:
        return Decimal(item["price"])
