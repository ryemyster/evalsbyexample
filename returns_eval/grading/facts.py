"""What the record supports, computed by the grader on its own.

The grader works out deadlines and fees itself from the case data and the
policy file. It never asks a candidate for these numbers, so a candidate bug
cannot hide behind a matching grader bug.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from ..cases import load_policy


@dataclass
class Facts:
    requester_id: str
    own_orders: dict[str, dict[str, Any]]
    other_orders: dict[str, dict[str, Any]]
    other_people: list[dict[str, str]]          # name, first, email of other customers
    target: dict[str, Any] | None
    amounts: set[Decimal] = field(default_factory=set)
    dates: set[date] = field(default_factory=set)
    as_of: date = date.min


def _d(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _money(value: str | None) -> Decimal | None:
    return Decimal(value).quantize(Decimal("0.01")) if value else None


def build_facts(case: dict[str, Any]) -> Facts:
    policy = load_policy(case["policy_version"])
    requester = case["customer"]["customer_id"]
    own = {o["order_id"]: o for o in case["orders"] if o["customer_id"] == requester}
    others = {o["order_id"]: o for o in case["orders"] if o["customer_id"] != requester}
    people = {}
    for o in others.values():
        people[o["customer_id"]] = {"name": o["customer_name"], "first": o["customer_name"].split()[0],
                                    "email": o["customer_email"]}
    target_id = case["expected"]["target_order_id"]
    facts = Facts(requester_id=requester, own_orders=own, other_orders=others,
                  other_people=list(people.values()), target=own.get(target_id) if target_id else None,
                  as_of=date.fromisoformat(case["as_of"]))

    facts.dates.add(facts.as_of)
    threshold = _money(policy["escalate_when"]["damaged_item_price_over"])
    if threshold:
        facts.amounts.add(threshold)
    fee = policy["restocking_fee"]

    for o in own.values():
        facts.amounts.add(_money(o["order_total"]))
        for it in o["items"]:
            price = _money(it["price"])
            facts.amounts.add(price)
            if it["opened"] and it["category"] == fee["category"]:
                fee_amount = (price * Decimal(fee["percent"]) / 100).quantize(Decimal("0.01"))
                facts.amounts.update({fee_amount, price - fee_amount})
        refund = o["refund"]
        if refund.get("amount"):
            facts.amounts.add(_money(refund["amount"]))

        for key in ("placed_on", "delivered_on"):
            if o[key]:
                facts.dates.add(_d(o[key]))
        if o["delivered_on"]:
            facts.dates.add(_d(o["delivered_on"]) + timedelta(days=policy["return_window_days"]))
        ret = o["return"]
        if ret:
            for key in ("label_issued_on", "shipped_on", "received_on"):
                if ret.get(key):
                    facts.dates.add(_d(ret[key]))
            if ret.get("inspection", {}).get("completed_on"):
                facts.dates.add(_d(ret["inspection"]["completed_on"]))
            if ret.get("label_issued_on"):
                facts.dates.add(_d(ret["label_issued_on"]) + timedelta(days=policy["label_valid_days"]))
        if refund.get("issued_on"):
            facts.dates.add(_d(refund["issued_on"]))
    facts.amounts.discard(None)
    facts.dates.discard(None)
    return facts
