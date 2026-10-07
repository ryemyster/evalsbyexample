"""Your candidate. Edit freely; nothing else in the repository depends on this file.

Run it:
    python3 -m returns_eval run --candidate playground.my_candidate:MyCandidate --baseline baseline

It starts as candidate-v2 plus one "improvement": a friendly sign-off. Run it and
it passes all 26 original cases. Now read the sign-off below carefully. The template field
is never filled in, so every customer would get "Best, {agent_name}". No check
looks for that, so the eval can't see it.

That's the first lesson of the playground: an eval only catches what someone
wrote a check for. docs/extending.md walks you through adding the check that
catches this (section "Add a deterministic check").

Ideas to try next:
- Override a method of CandidateV2 (see returns_eval/candidates/candidate_v2.py).
- Start from scratch: subclass Candidate and write draft_reply yourself.
- Break something on purpose (call tools.issue_refund) and watch the gate block it.
"""

from returns_eval.candidates.base import Candidate  # noqa: F401  (for starting from scratch)
from returns_eval.candidates.candidate_v2 import CandidateV2
from returns_eval.models import Draft, Request
from returns_eval.tools import Toolbox

SIGN_OFF = "\n\nBest, {agent_name}\nExample Outfitters Support"


class MyCandidate(CandidateV2):
    name = "my-candidate"
    version = "0.1"
    description = "Playground: candidate-v2 plus a sign-off. Edit me."

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        draft = super().draft_reply(request, tools)
        draft.reply_text += SIGN_OFF
        return draft
