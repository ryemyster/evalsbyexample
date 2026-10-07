"""Baseline: saved reply templates picked by keyword.

This stands in for today's workflow, where agents paste a saved reply and
adjust it. It never takes an action, never states order-specific facts, and
never checks policy exceptions. It is safe but generic, which is exactly what
the candidates have to beat.

(In the pilot, the baseline is the real thing: agents drafting by hand. Offline,
templates are the closest runnable approximation.)
"""

from __future__ import annotations

from ..models import Draft, Request
from ..tools import Toolbox
from .base import Candidate, has_any, order_numbers_in

ESCALATE = (
    "Hi {first}, I'm sorry for the trouble. A specialist on our team will review your "
    "case and follow up with you."
)
LABEL = (
    "Hi {first}, sorry about that. Return labels expire 14 days after they're issued. "
    "We'll send you a new return label by email."
)
EXCHANGE = (
    "Hi {first}, thanks for reaching out. You can exchange items for a different size "
    "or color within 30 days of delivery. We'll send you a prepaid return label, and "
    "we'll ship the new item once your return is on its way."
)
DAMAGED = (
    "Hi {first}, we're sorry your item arrived damaged. Could you reply with a photo of "
    "the damage so we can sort this out?"
)
REFUND_STATUS = (
    "Hi {first}, thanks for checking in. Refunds go back to your original payment "
    "method after we receive and inspect your return. We'll email you to confirm "
    "when your refund is issued."
)
RETURN = (
    "Hi {first}, thanks for reaching out about order {order_id}. You can return items "
    "within 30 days of delivery. We'll send you a prepaid return label, and your refund "
    "goes back to your original payment method after we inspect the item."
)
ASK = (
    "Hi {first}, happy to help. Could you reply with the order number, or tell us "
    "which order or item you'd like to return? If you checked out with a different "
    "email address, please include that too."
)
FALLBACK = (
    "Hi {first}, thanks for reaching out. A member of our team will look into this "
    "and follow up with you."
)


class TemplateBaseline(Candidate):
    name = "baseline"
    version = "1.0"
    description = "Saved reply templates chosen by keyword. Safe, generic, never takes actions."

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        first = request.customer.first_name
        msg = request.message
        own = tools.find_orders(request.customer.customer_id)
        own_ids = {o["order_id"] for o in own}

        typed = [oid for oid in order_numbers_in(msg) if oid in own_ids]
        if typed:
            order_id = typed[0]
        elif len(own) == 1:
            order_id = own[0]["order_id"]
        else:
            order_id = None

        def reply(template: str, resolution: str, oid: str | None = order_id) -> Draft:
            return Draft(template.format(first=first, order_id=oid), resolution, oid)

        if has_any(msg, ("chargeback", "lawyer", "legal")):
            return reply(ESCALATE, "escalate")
        if has_any(msg, ("expired",)) and has_any(msg, ("label",)):
            return reply(LABEL, "inform")
        if has_any(msg, ("swap", "exchange")):
            return reply(EXCHANGE, "accept_return")
        if has_any(msg, ("broken", "shattered", "damaged")):
            return reply(DAMAGED, "ask_customer")
        if has_any(msg, ("refund", "money", "paid")):
            return reply(REFUND_STATUS, "inform")
        if has_any(msg, ("return", "send it back", "send back")):
            if order_id is None:
                return reply(ASK, "ask_customer", None)
            return reply(RETURN, "accept_return")
        return reply(FALLBACK, "escalate")
