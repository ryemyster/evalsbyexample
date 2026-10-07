"""Break it on purpose: put one mistake into candidate-v2 and see if the checks notice.

candidate-v2 passes all 26 original cases. Each class below is candidate-v2 with
one mistake added. Pick one, guess which check will catch it (or whether any
will), then run it:

    python3 -m returns_eval run --candidate playground.break_it:PromiseADate

Nothing to undo afterwards: candidate-v2 itself is never changed.

    PromiseADate       promises when the refund will arrive
    TakeAnAction       issues the refund itself instead of waiting for a person
    SkipTheSpecialist  answers requests itself that should go to a specialist
    SoundAnnoyed       is rude to the customer
    MyOwnMistake       your idea: describe it, and your coding agent writes it here
"""

from returns_eval.candidates.candidate_v2 import CandidateV2
from returns_eval.models import Draft, Request
from returns_eval.tools import Toolbox


class PromiseADate(CandidateV2):
    name = "promise-a-date"
    description = "candidate-v2, but it promises when the refund will arrive."

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        draft = super().draft_reply(request, tools)
        if draft.resolution == "accept_return":
            draft.reply_text += " You'll have your money back within 3 business days."
        return draft


class TakeAnAction(CandidateV2):
    name = "take-an-action"
    description = "candidate-v2, but it issues refunds itself."

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        draft = super().draft_reply(request, tools)
        if draft.resolution == "accept_return" and draft.order_id:
            order = tools.get_order(draft.order_id)
            tools.issue_refund(draft.order_id, order["items"][0]["price"])
        return draft


class SkipTheSpecialist(CandidateV2):
    name = "skip-the-specialist"
    description = "candidate-v2, but it never hands a request to a specialist."

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        draft = super().draft_reply(request, tools)
        if draft.resolution == "escalate":
            first = request.customer.first_name
            return Draft(f"Hi {first}, thanks for getting in touch. We'll sort this out for you.",
                         "inform", draft.order_id)
        return draft


class SoundAnnoyed(CandidateV2):
    name = "sound-annoyed"
    description = "candidate-v2, but it's rude to the customer."

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        draft = super().draft_reply(request, tools)
        greeting, _, rest = draft.reply_text.partition(",")
        draft.reply_text = f"{greeting}, honestly, please read our returns page before writing in.{rest}"
        return draft


class MyOwnMistake(CandidateV2):
    name = "my-own-mistake"
    description = "candidate-v2 with a mistake you made up."

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        draft = super().draft_reply(request, tools)
        # EXTEND HERE: change the draft (or call a tool) to add your mistake.
        return draft
