"""Candidate registry.

Built-in candidates are listed by name. You can also point at any class with
"module.path:ClassName", for example the Exercise 9 candidate:

    python3 -m returns_eval run --candidate exercises.ex09_candidate_v3:CandidateV3
"""

from __future__ import annotations

import importlib

from .base import Candidate
from .baseline import TemplateBaseline
from .candidate_v1 import CandidateV1
from .candidate_v2 import CandidateV2
from .candidate_v4 import CandidateV4

# EXTEND HERE: register a candidate by name. You don't have to: any class works as
# --candidate module.path:ClassName. Start from playground/my_candidate.py, or for a
# language model, playground/my_model.py. See docs/extending.md.
BUILT_IN: dict[str, type[Candidate]] = {
    TemplateBaseline.name: TemplateBaseline,
    CandidateV1.name: CandidateV1,
    CandidateV2.name: CandidateV2,
    CandidateV4.name: CandidateV4,  # the final challenge (TUTOR.md)
}


def load_candidate(spec: str) -> Candidate:
    if spec in BUILT_IN:
        return BUILT_IN[spec]()
    if ":" in spec:
        module_name, _, attr = spec.partition(":")
        try:
            cls = getattr(importlib.import_module(module_name), attr)
        except (ImportError, AttributeError) as exc:
            raise SystemExit(f"Could not load candidate '{spec}': {exc}") from exc
        candidate = cls()
        if not isinstance(candidate, Candidate):
            raise SystemExit(f"'{spec}' is not a Candidate subclass.")
        return candidate
    names = ", ".join(BUILT_IN)
    raise SystemExit(f"Unknown candidate '{spec}'. Built-in candidates: {names}. "
                     "Or use module.path:ClassName.")


__all__ = ["BUILT_IN", "Candidate", "load_candidate"]
