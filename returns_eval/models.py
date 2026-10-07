"""Shared data shapes.

These are the only types that cross the line between the code that writes
replies (candidates) and the code that judges them (grading). Keeping the
contract small makes it easy to swap in a new candidate without touching the
grader, and vice versa.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any

# The dispositions a draft can propose. An agent sees this next to the draft
# and uses it to route the ticket.
RESOLUTIONS = (
    "inform",          # answer a question; no change to the return
    "accept_return",   # the return (or exchange) is allowed; agent sends a label
    "decline_return",  # policy does not allow the return
    "ask_customer",    # we need information from the customer first
    "escalate",        # a specialist must handle it
)


@dataclass(frozen=True)
class Customer:
    """The person who wrote in. In a real helpdesk this comes from login or email."""

    customer_id: str
    name: str
    email: str
    returns_last_60_days: int = 0

    @property
    def first_name(self) -> str:
        return self.name.split()[0]


@dataclass(frozen=True)
class Request:
    """Everything a candidate is allowed to see up front.

    Order records are NOT included. A candidate has to look them up through the
    toolbox, so every lookup is recorded in the trace.
    """

    customer: Customer
    message: str
    as_of: str              # ISO date the case is frozen at ("today")
    policy: dict[str, Any]  # the policy version supplied with the case


@dataclass
class Draft:
    """What a candidate produces. A human agent approves or edits it."""

    reply_text: str
    resolution: str
    order_id: str | None = None
    note_for_agent: str = ""  # internal note; never shown to the customer

    def fingerprint(self) -> str:
        """Short hash used to tell whether a human review still matches this draft."""
        raw = "\x1f".join([self.resolution, self.order_id or "", self.reply_text])
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["fingerprint"] = self.fingerprint()
        return data


@dataclass
class ToolCall:
    """One call a candidate made through the toolbox."""

    tool: str
    args: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"tool": self.tool, "args": self.args}
