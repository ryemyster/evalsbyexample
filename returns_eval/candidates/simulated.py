"""SIMULATED models: scripts with built-in randomness that behave like a language model.

These are NOT language models. Each one starts from candidate-v2's behavior and then,
like a real model, sometimes does something different on the same input. They exist
so you can learn how evals change when answers vary, without an API key or any cost.

How they work, so you can check every result:

  - Each attempt rolls dice that depend on the model's name, a seed, the case, and the
    attempt number. Same seed, same results; a different seed is a different roll,
    like asking a real model again. Set the seed with --seed, or EVALS_SEED.
  - The "model" writes raw JSON text, which goes through the same parser as a real
    model's reply (LLMCandidate.draft_from_raw). So a badly formatted reply really is
    handled the way a real one would be, and the grader's structured_output check sees it.
  - Tokens are estimated (characters / 4) and time is drawn from a made-up
    distribution. Reports label both as simulated.

What each one tends to get wrong (the chance per attempt, where it applies):

                      hands off less   rewords required phrases   breaks the format   promises a date
  sim-model-a              25%                 15%                       4%                  -
  sim-model-b              25%                 12%                       4%                  -
  sim-model-c               3%                 15%                       4%                  -
  candidate-v5              -                   -                        -                  5%

sim-model-b is prompt 2 of the same model: a shorter, friendlier prompt that doesn't
change much. sim-model-c is prompt 3: it lists every escalation rule, which really
does help. candidate-v5 (the Part 2 capstone) is a smaller, faster model with the
Exercise 9 fix built in. Learners: try the capstone before reading its settings.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
from decimal import Decimal
from typing import Any

from ..models import Draft, Request
from ..tools import Toolbox
from .candidate_v2 import CandidateV2
from .llm_adapter import LLMCandidate

# Correct rewordings that a word-matching check doesn't recognize. The meaning is the
# same, so a failure caused by one of these is the CHECK's mistake, not the model's.
PARAPHRASES = (
    ("we received your return", "your return made it back to our warehouse"),
    ("waiting for inspection", "waiting for our quality check"),
    ("passes inspection", "passes our quality check"),
    ("new return label", "fresh prepaid label"),
    ("you can return", "you're welcome to send back"),
    ("original payment method", "card or account you paid with"),
    ("A specialist on our team", "A senior agent"),
    ("a specialist", "a senior agent"),
)
SIGNATURE = " Let me know if there's anything else I can help with!"  # this model family's habit
PADDING = (" We really appreciate your patience and understanding while we look after this, and we're "
           "always glad to hear from you.")
DATE_PROMISE = " You'll usually see the refund within 5 business days."


class _V2WithFix(CandidateV2):
    """candidate-v2 plus the Exercise 9 fix: quote the returned item's price, not the order total."""

    def _refund_amount(self, order: dict[str, Any], item: dict[str, Any]) -> Decimal:
        return Decimal(item["price"])


class SimulatedModel(LLMCandidate):
    """Base class. Subclasses set the chances below."""

    simulated = True
    family = "sim"            # judges in Part 2 can be told which family wrote a draft
    seed = 1
    base_behavior = CandidateV2
    price_key = "sim-large"   # looked up in data/economics/prices.ILLUSTRATIVE.json
    median_seconds = 3.0
    timeout_chars: int | None = None   # messages longer than this time out (None = never)
    timeout_seconds = 8
    chance = {"skip_specialist": 0.0, "paraphrase": 0.0, "bad_format": 0.0, "promise_date": 0.0, "padding": 0.0}

    def __init__(self) -> None:
        if os.environ.get("EVALS_SEED"):
            self.seed = int(os.environ["EVALS_SEED"])
        self._attempts: dict[str, int] = {}
        self.last_usage: dict[str, Any] | None = None

    def _dice(self, request: Request) -> random.Random:
        key = hashlib.sha256(f"{request.customer.customer_id}|{request.message}".encode()).hexdigest()[:16]
        n = self._attempts.get(key, 0)
        self._attempts[key] = n + 1
        # A string seed is hashed with SHA-512 by Python's random module, so it's stable everywhere.
        return random.Random(f"{self.name}|{self.seed}|{key}|{n}")

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        rng = self._dice(request)
        prompt = self.build_prompt(request, tools)   # what a real model would be sent (counted as tokens)
        if self.timeout_chars is not None and len(request.message) > self.timeout_chars:
            raise TimeoutError(f"simulated: no reply within the {self.timeout_seconds}-second limit "
                               f"(the customer's message was {len(request.message)} characters)")
        base = self.base_behavior().draft_reply(request, tools)
        reply, resolution = base.reply_text, base.resolution

        if resolution == "escalate" and rng.random() < self.chance["skip_specialist"]:
            resolution = "inform"
            reply = (f"Hi {request.customer.first_name}, thanks for getting in touch. I've looked at your "
                     "request, and we'll sort it out for you.")
        if rng.random() < self.chance["paraphrase"]:
            for old, new in PARAPHRASES:
                reply = reply.replace(old, new)
        if resolution == "accept_return" and rng.random() < self.chance["promise_date"]:
            reply += DATE_PROMISE
        if rng.random() < self.chance["padding"]:
            reply += PADDING
        reply += SIGNATURE

        payload = {"resolution": resolution, "order_id": base.order_id, "reply_text": reply,
                   "note_for_agent": base.note_for_agent}
        if rng.random() < self.chance["bad_format"]:
            payload["resolution"] = {"accept_return": "approve_return", "decline_return": "deny",
                                     "escalate": "transfer"}.get(resolution, "answer")
        raw = "```json\n" + json.dumps(payload, indent=1) + "\n```"

        self.last_usage = {
            "input_tokens": len(prompt) // 4, "output_tokens": len(raw) // 4,
            "seconds": round(self.median_seconds * math.exp(rng.gauss(0, 0.35)), 2),
            "source": "simulated", "price_key": self.price_key,
        }
        return self.draft_from_raw(raw, tools)


class SimModelA(SimulatedModel):
    name = "sim-model-a"
    version = "sim-large, prompt 1"
    description = "SIMULATED model, prompt 1. Varies from attempt to attempt, like a real model."
    chance = {"skip_specialist": 0.25, "paraphrase": 0.15, "bad_format": 0.04, "promise_date": 0.0, "padding": 0.3}


class SimModelB(SimulatedModel):
    name = "sim-model-b"
    version = "sim-large, prompt 2"
    description = "SIMULATED model, prompt 2 (shorter and friendlier). Is it better than prompt 1?"
    chance = {"skip_specialist": 0.25, "paraphrase": 0.12, "bad_format": 0.04, "promise_date": 0.0, "padding": 0.1}


class SimModelC(SimulatedModel):
    name = "sim-model-c"
    version = "sim-large, prompt 3"
    description = "SIMULATED model, prompt 3 (lists every escalation rule). Is it better than prompt 1?"
    chance = {"skip_specialist": 0.03, "paraphrase": 0.15, "bad_format": 0.04, "promise_date": 0.0, "padding": 0.3}


class CandidateV5(SimulatedModel):
    """The Part 2 capstone (TUTOR-PART2.md). Changing what it gets wrong changes the answer key."""

    name = "candidate-v5"
    version = "5.0, sim-small, prompt 5"
    description = "SIMULATED smaller, faster model with the Exercise 9 fix. The Part 2 capstone."
    base_behavior = _V2WithFix
    price_key = "sim-small"
    median_seconds = 1.1
    timeout_chars = 1200
    chance = {"skip_specialist": 0.0, "paraphrase": 0.0, "bad_format": 0.0, "promise_date": 0.05, "padding": 0.0}
