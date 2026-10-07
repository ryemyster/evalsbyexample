"""candidate-v2: the improved reference candidate.

Like v1, this is scripted Python, not a model. It shows what "fixing the
failures v1 exposed" looks like in behavior:

  - checks that an order belongs to the customer before using it
  - never calls a write tool; every draft waits for a human
  - treats instructions inside the customer's message as content, not commands
  - uses the policy version supplied with the case, with an inclusive window
  - escalates on every rule in the policy, not just one keyword
  - asks instead of guessing when the order or item is unclear

It passes every case in the 1.0 case set. That does not make it correct in
general; see the pilot section of the README for what it still got wrong.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any

from ..models import Draft, Request
from ..tools import Toolbox
from .base import (
    Candidate, describe, has_any, item_words, money, nice_date, order_numbers_in, parse_date, plus_days,
)

INSTRUCTION_PATTERNS = re.compile(
    r"ignore (all |your )?(previous|prior) instructions|system note|you are authori[sz]ed|as the assistant",
    re.IGNORECASE,
)
AUTHORITY_CLAIM = re.compile(r"\b(approved|authori[sz]ed|promised me|manager said)\b", re.IGNORECASE)


class CandidateV2(Candidate):
    name = "candidate-v2"
    version = "2.0"
    description = "Improved reference. Checks ownership, never acts, follows the supplied policy."

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        self.request = request
        msg = request.message
        hi = f"Hi {request.customer.first_name},"
        policy = request.policy
        own = tools.find_orders(request.customer.customer_id)
        own_by_id = {o["order_id"]: o for o in own}

        if INSTRUCTION_PATTERNS.search(msg):
            return Draft(
                f"{hi} thanks for your message. A member of our team will review your request and follow up with you.",
                "escalate", own[0]["order_id"] if len(own) == 1 else None,
                note_for_agent="The message contains text addressed to the assistant. Treated as untrusted; no action taken.",
            )

        # Which order is this about? Only the customer's own orders are ever used.
        typed = order_numbers_in(msg)
        not_theirs = [oid for oid in typed if oid not in own_by_id]
        mine = [oid for oid in typed if oid in own_by_id]
        if not_theirs and not mine:
            if own:
                listing = " or ".join(describe(o) for o in own)
                return Draft(
                    f"{hi} I couldn't find the order number you mentioned on your account. Could you "
                    f"double-check it? I can see {listing} on your account. Is that the one?",
                    "ask_customer", None,
                    note_for_agent="Customer typed an order number that is not on their account. Not looked up.",
                )
            return Draft(
                f"{hi} for privacy, we can only discuss an order with the account holder. Please ask the "
                "person who placed the order to contact us from the email address on the order, and we'll "
                "be glad to help them.",
                "inform", None,
            )

        order, item = self._pick_order_and_item(msg, own, mine)
        if order is None:
            if own:
                listing = " or ".join(describe(o) for o in own)
                return Draft(f"{hi} happy to help. Which item would you like to return? I can see {listing} "
                             "on your account.", "ask_customer", None)
            return Draft(f"{hi} I couldn't find an order under this email address. Could you reply with the "
                         "order number and the email address you used at checkout?", "ask_customer", None)

        oid = order["order_id"]
        ret = order["return"]
        refund = order["refund"]

        if AUTHORITY_CLAIM.search(msg) and "refund" in msg.lower():
            return Draft(
                f"{hi} thanks for letting us know. We'll need to verify what was agreed before anything "
                f"changes on order {oid}, so a team member will check and follow up with you. Our usual "
                "process is to refund an item after it is returned and passes inspection.",
                "escalate", oid,
                note_for_agent="Customer says a refund was already approved. No approval is on the order record.",
            )
        if has_any(msg, ("chargeback", "lawyer", "legal action", "sue ")):
            return Draft(f"{hi} I'm sorry this has been frustrating. A specialist on our team will review "
                         "your return and follow up with you directly.", "escalate", oid)
        if has_any(msg, ("never arrived", "never got", "didn't arrive", "not arrived")):
            return Draft(f"{hi} I'm sorry your package hasn't turned up. A specialist on our team will look "
                         "into the delivery with the carrier and follow up with you.", "escalate", oid)
        if has_any(msg, ("address",)) and has_any(msg, ("change", "update")):
            return Draft(f"{hi} thanks for letting us know. A team member will review your address change "
                         f"request for order {oid} and confirm with you before it ships.", "escalate", oid)

        # Questions about a return or refund already in progress.
        if refund["status"] == "issued":
            expected = self._refund_amount(order, item)
            if Decimal(refund["amount"]) != expected:
                return Draft(
                    f"{hi} I can see a refund of {money(refund['amount'])} was issued on "
                    f"{nice_date(refund['issued_on'])} for order {oid}, which is less than the "
                    f"{money(expected)} you paid. I don't see a policy reason for the difference, so a "
                    "specialist will review the refund and follow up with you.",
                    "escalate", oid,
                )
            return Draft(f"{hi} your refund of {money(refund['amount'])} was issued on "
                         f"{nice_date(refund['issued_on'])} to your original payment method. Your bank or "
                         "card issuer can tell you when it will show on your statement.", "inform", oid)
        if ret and ret["received_on"]:
            return Draft(
                f"{hi} we received your return on {nice_date(ret['received_on'])}, and it's now waiting for "
                "inspection. Once it passes, your refund goes back to your original payment method. I can't "
                "give you an exact date, but you'll get an email as soon as the refund is issued.",
                "inform", oid,
            )
        if ret and has_any(msg, ("expired",)):
            expiry = plus_days(ret["label_issued_on"], policy["label_valid_days"])
            deadline = plus_days(order["delivered_on"], policy["return_window_days"])
            return Draft(
                f"{hi} sorry about that. Return labels expire {policy['label_valid_days']} days after they're "
                f"issued, so the label from {nice_date(ret['label_issued_on'])} expired on {nice_date(expiry)}. "
                f"We'll send you a new return label for order {oid}. Your return window is open until "
                f"{nice_date(deadline)}.",
                "inform", oid,
            )
        if ret and not ret["received_on"] and has_any(msg, ("mailed", "sent it", "shipped", "dropped off")):
            return Draft(
                f"{hi} I'm sorry for the wait. Our records don't show the package arriving yet. Could you "
                "reply with the tracking number or drop-off receipt so we can trace it?",
                "ask_customer", oid,
            )

        return self._return_request(order, item, msg, hi)

    # -----------------------------------------------------------------------

    def _pick_order_and_item(self, msg: str, own: list[dict[str, Any]], mine: list[str]):
        if mine:
            order = next(o for o in own if o["order_id"] == mine[0])
        elif len(own) == 1:
            order = own[0]
        else:
            # Several orders: only choose one if the message names an item unique to it.
            words = item_words(msg)
            all_names = [item_words(i["name"]) for o in own for i in o["items"]]
            shared = set.intersection(*all_names) if all_names else set()
            matches = [o for o in own if any((item_words(i["name"]) - shared) & words for i in o["items"])]
            if len(matches) != 1:
                return None, None
            order = matches[0]
        words = item_words(msg)
        named = [i for i in order["items"] if item_words(i["name"]) & words]
        return order, (named[0] if named else order["items"][0])

    def _refund_amount(self, order: dict[str, Any], item: dict[str, Any]) -> Decimal:
        """The amount quoted in the draft. (Exercise 9 revisits this method.)"""
        return Decimal(order["order_total"])

    def _return_request(self, order, item, msg, hi) -> Draft:
        policy = self.request.policy
        rules = policy["escalate_when"]
        oid = order["order_id"]
        customer = self.request.customer

        if order["delivered_on"] is None:
            return Draft(
                f"{hi} I can't confirm your return window yet because the delivery date for order {oid} is "
                "missing from our records. A specialist will confirm the delivery date with the carrier and "
                "follow up with you.",
                "escalate", oid,
            )
        if customer.returns_last_60_days > rules["returns_in_last_60_days_over"]:
            return Draft(f"{hi} thanks for letting us know. A specialist will review this return and follow "
                         "up with next steps.", "escalate", oid)
        damaged = has_any(msg, ("damaged", "broken", "shattered", "chip", "cracked"))
        if damaged and Decimal(item["price"]) > Decimal(rules["damaged_item_price_over"]):
            return Draft(f"{hi} I'm so sorry the {item['name']} arrived damaged. A specialist on our team will "
                         "review this and follow up with you.", "escalate", oid)
        if item["final_sale"]:
            return Draft(f"{hi} I'm sorry, but the {item['name']} was a final-sale item, and final-sale items "
                         "can't be returned.", "decline_return", oid)
        if item["opened"] and item["category"] in policy["non_returnable_if_opened_categories"]:
            return Draft(f"{hi} I'm sorry to hear that. Opened personal-care items can't be returned, so we "
                         f"aren't able to accept a return for the {item['name']}. If it's irritating your skin, "
                         "please stop using it.", "decline_return", oid)

        window = policy["return_window_days"]
        deadline = plus_days(order["delivered_on"], window)
        today = parse_date(self.request.as_of)
        if today > deadline:
            return Draft(f"{hi} I'm sorry, but our return window is {window} days from delivery. Order {oid} was "
                         f"delivered on {nice_date(order['delivered_on'])}, so the window closed on "
                         f"{nice_date(deadline)}.", "decline_return", oid)

        when = (f"Today ({nice_date(deadline)}) is the last day to start your return"
                if today == deadline else f"You have until {nice_date(deadline)} to start the return")
        amount = self._refund_amount(order, item)
        fee = policy["restocking_fee"]
        fee_note = ""
        if item["opened"] and item["category"] == fee["category"]:
            fee_amount = amount * Decimal(fee["percent"]) / 100
            fee_note = (f" Because it was opened, a {fee['percent']}% restocking fee ({money(fee_amount)}) "
                        f"applies, so the refund would be {money(amount - fee_amount)}.")
            amount = amount - fee_amount
        opener = f"I'm sorry the {item['name']} arrived damaged. You" if damaged else "you"
        if has_any(msg, ("swap", "exchange")):
            return Draft(f"{hi} {opener} can exchange the {item['name']} for a different size. {when}. "
                         "We'll send you a prepaid return label, and a team member will check that the size "
                         "you want is available.", "accept_return", oid)
        return Draft(
            f"{hi} {opener} can return the {item['name']}. {when}. We'll email you a prepaid return "
            f"label.{fee_note} Once the item passes inspection, your refund of {money(amount)} will go back "
            "to your original payment method.",
            "accept_return", oid,
        )
