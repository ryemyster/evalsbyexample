"""candidate-v1: a scripted stand-in for a first drafting prototype.

This is NOT a language model. It is ordinary Python written to behave like a
fluent, eager first prototype: specific, friendly, usually right on common
requests, and wrong in ways that matter. The flaws are deliberate and labeled
FLAW so you can find them after the eval points at them:

  FLAW 1  Uses whatever order number the customer typed, without checking who owns it.
  FLAW 2  Greets the customer using the name on the order record.
  FLAW 3  Treats "return received" as "refund issued", and promises a timeline.
  FLAW 4  Obeys messages that claim someone authorized a refund.
  FLAW 5  Uses a hard-coded 30-day window and ignores the policy supplied with the case.
  FLAW 6  Off-by-one: declines on the last valid day.
  FLAW 7  Escalates only on the word "chargeback"; ignores the other escalation rules.
  FLAW 8  With several orders, assumes the most recent one is meant.
  FLAW 9  Believes the customer when they say a return was mailed.
  FLAW 10 Invents an explanation (a restocking fee) for a refund shortfall.
"""

from __future__ import annotations

import re
from decimal import Decimal

from ..models import Draft, Request
from ..tools import Toolbox
from .base import Candidate, has_any, item_words, money, nice_date, order_numbers_in, parse_date, plus_days

WINDOW_DAYS = 30  # FLAW 5


class CandidateV1(Candidate):
    name = "candidate-v1"
    version = "1.0"
    description = "Eager first prototype. Fluent and specific, with deliberate, instructive flaws."

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        msg = request.message
        own = tools.find_orders(request.customer.customer_id)

        typed = order_numbers_in(msg)
        if typed:
            order = tools.get_order(typed[0])  # FLAW 1: no ownership check
        elif len(own) == 1:
            order = own[0]
        elif own and any(item_words(i["name"]) & item_words(msg) for o in own for i in o["items"]):
            order = own[0]  # FLAW 8: most recent, not the one the customer named
        else:
            order = None

        first = (order["customer_name"] if order else request.customer.name).split()[0]  # FLAW 2
        hi = f"Hi {first},"

        # FLAW 4: authority claims are treated as instructions.
        if order and re.search(r"authori[sz]ed|approved", msg, re.I) and "refund" in msg.lower():
            amount = order["order_total"]
            tools.issue_refund(order["order_id"], amount)
            text = (f"{hi} done! I've processed your refund of {money(amount)} for order "
                    f"{order['order_id']}. It should reach your original payment method within 5-7 business days.")
            if "email" in msg.lower():
                tools.send_reply(text)
            return Draft(text, "inform", order["order_id"])

        if has_any(msg, ("chargeback",)):  # FLAW 7: the only escalation rule it knows
            return Draft(f"{hi} I'm sorry for the frustration. A specialist on our team will review "
                         "your case today and follow up with you.", "escalate", order and order["order_id"])

        if has_any(msg, ("change the shipping address", "change my address")):
            return Draft(f"{hi} thanks for letting us know. I've passed your address change to a "
                         "team member, who will confirm with you.", "escalate", order and order["order_id"])

        if order is None:
            if own:
                return Draft(f"{hi} happy to help! Which item would you like to return? I can see "
                             f"{len(own)} recent orders on your account.", "ask_customer", None)
            return Draft(f"{hi} I couldn't find an order under this email. Could you send the order "
                         "number and the email address you used at checkout?", "ask_customer", None)

        oid = order["order_id"]
        item = order["items"][0]
        ret = order["return"]
        refund = order["refund"]

        if has_any(msg, ("never arrived", "never got", "didn't arrive")):
            return Draft(f"{hi} I'm sorry your package hasn't turned up. A specialist will look into "
                         "the delivery with the carrier and follow up.", "escalate", oid)

        if has_any(msg, ("expired",)) and ret:
            return Draft(f"{hi} sorry about that! Return labels expire 14 days after they're issued, so "
                         f"we'll email you a new return label for order {oid}.", "inform", oid)

        if refund["status"] == "issued":
            text = (f"{hi} your refund of {money(refund['amount'])} was issued on "
                    f"{nice_date(refund['issued_on'])} to your original payment method.")
            if Decimal(refund["amount"]) < Decimal(order["order_total"]):
                # FLAW 10: makes up a reason instead of escalating.
                text += " The difference from the price you paid is our standard restocking fee."
            return Draft(text, "inform", oid)

        if ret and ret["received_on"]:
            # FLAW 3: "received" is treated as "refunded", and a timeline is promised.
            return Draft(f"{hi} good news: we received your return on {nice_date(ret['received_on'])} and "
                         f"your refund of {money(order['order_total'])} has been issued. It should appear "
                         "within 5-7 business days.", "inform", oid)

        if ret and has_any(msg, ("mailed", "sent it", "shipped")):
            # FLAW 9: trusts the customer over the record.
            return Draft(f"{hi} thanks for sending it back! We've received your return and it's now "
                         "waiting for inspection.", "inform", oid)

        # Everything else is treated as a return or exchange request.
        if item["final_sale"]:
            return Draft(f"{hi} I'm sorry, but the {item['name']} was a final-sale item, so it can't be "
                         "returned.", "decline_return", oid)
        if item["opened"] and item["category"] == "personal_care":
            return Draft(f"{hi} I'm sorry, but opened personal-care items can't be returned.",
                         "decline_return", oid)

        delivered = order["delivered_on"] or plus_days(order["placed_on"], 3).isoformat()  # guesses
        deadline = plus_days(delivered, WINDOW_DAYS)
        days = (parse_date(request.as_of) - parse_date(delivered)).days
        if days >= WINDOW_DAYS:  # FLAW 6 (should be >)
            return Draft(f"{hi} I'm sorry, but our return window is 30 days from delivery, and it "
                         f"closed on {nice_date(deadline)} for order {oid}.", "decline_return", oid)

        amount = Decimal(order["order_total"])
        fee_note = ""
        if item["opened"] and item["category"] == "electronics":
            amount = amount * Decimal("0.85")
            fee_note = " Because it was opened, a 15% restocking fee applies."
        verb = "exchange" if has_any(msg, ("swap", "exchange")) else "return"
        return Draft(
            f"{hi} good news: you can {verb} the {item['name']} until {nice_date(deadline)}. "
            f"We'll email you a prepaid return label.{fee_note} Once it passes inspection, your refund "
            f"of {money(amount)} will go back to your original payment method.",
            "accept_return", oid,
        )
