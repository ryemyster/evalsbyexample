"""Check that a rubric says what a rater should look for, not just how they should feel.

A rubric is a JSON file (format: data/rubrics/README.md). Each criterion becomes a
question that people, a judge, or code will answer about every draft. Vague
criteria ("Is it helpful?") make raters disagree, and a judge calibrated against
disagreeing raters learns nothing useful. So before anyone labels anything, the
rubric has to pass these rules.

    python3 -m returns_eval rubric-check data/rubrics/draft-quality.v1.json
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .grading import SEVERITY

SCALES = ("binary", "ordinal", "continuous")
GRADED_BY = ("code", "judge", "human")
REFERENCES = ("none", "expected_behavior", "records", "policy")
# Words that sound like criteria but don't say what a rater would see in the reply.
VAGUE = ("good", "bad", "great", "nice", "helpful", "appropriate", "appropriately", "professional", "quality",
         "reasonable", "properly", "proper", "adequate", "sufficient", "acceptable", "accurate", "complete",
         "polished", "engaging", "high-quality")
MIN_DEFINITION_WORDS = 8


def _vague_words(text: str) -> list[str]:
    return sorted({w for w in VAGUE if re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", text, re.IGNORECASE)})


def lint(rubric: Any) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). The rubric is ready when errors is empty."""
    if not isinstance(rubric, dict) or not isinstance(rubric.get("criteria"), list) or not rubric["criteria"]:
        return ['The rubric must be an object with a non-empty "criteria" list.'], []
    errors, warnings = [], []
    for key in ("rubric", "version"):
        if not str(rubric.get(key, "")).strip():
            errors.append(f'Add "{key}" at the top, so labels can say which rubric they used.')
    seen = set()
    for i, c in enumerate(rubric["criteria"], start=1):
        if not isinstance(c, dict):
            errors.append(f"criterion {i}: must be an object")
            continue
        cid = c.get("id") or f"criterion {i}"

        def err(msg: str) -> None:
            errors.append(f"{cid}: {msg}")

        if not re.fullmatch(r"[a-z][a-z0-9_]*", str(c.get("id", ""))):
            err('needs an "id" in lowercase_with_underscores')
        if cid in seen:
            err("id is used twice")
        seen.add(cid)
        question = str(c.get("question", ""))
        if not question.strip().endswith("?"):
            err('"question" must be one question ending in "?"')
        for word in _vague_words(question):
            err(f'"{word}" in the question is vague: say what a rater would see in the reply instead')
        if re.search(r"\band\b", question) and c.get("scale") == "binary":
            warnings.append(f'{cid}: the question has "and"; check it isn\'t two questions in one')

        scale = c.get("scale")
        if scale not in SCALES:
            err(f'"scale" must be one of {", ".join(SCALES)} (got {scale!r}). A "1-5" scale needs each level defined: use ordinal.')
        elif scale in ("binary", "ordinal"):
            values = c.get("values")
            want = "exactly 2" if scale == "binary" else "3 or more"
            if not isinstance(values, list) or (len(values) != 2 if scale == "binary" else len(values) < 3):
                err(f'"values" must list {want} labels')
                values = []
            definitions = c.get("definitions") or {}
            for v in values:
                text = str(definitions.get(v, ""))
                if len(text.split()) < MIN_DEFINITION_WORDS:
                    err(f'define "{v}" in "definitions" with what a rater would see (at least {MIN_DEFINITION_WORDS} words)')
                for word in _vague_words(text):
                    err(f'"{word}" in the definition of "{v}" is vague')
            examples = c.get("examples") or {}
            needed = values if scale == "binary" else values[:1] + values[-1:]
            for v in needed:
                if not str(examples.get(v, "")).strip():
                    err(f'give an example reply for "{v}" in "examples"')
        else:  # continuous
            rng = c.get("range")
            if not str(c.get("unit", "")).strip():
                err('a continuous criterion needs a "unit" (minutes, dollars, ...)')
            if not (isinstance(rng, list) and len(rng) == 2 and all(isinstance(x, (int, float)) for x in rng) and rng[0] < rng[1]):
                err('a continuous criterion needs a "range" like [0, 30]')
            if len(str(c.get("how_measured", "")).split()) < MIN_DEFINITION_WORDS:
                err('say in "how_measured" exactly how the number is collected')

        if c.get("reference") not in REFERENCES:
            err(f'"reference" must be one of {", ".join(REFERENCES)}: what the rater compares the reply with ("none" = reference-free)')
        graded_by = c.get("graded_by")
        if graded_by not in GRADED_BY:
            err(f'"graded_by" must be one of {", ".join(GRADED_BY)}')
        elif graded_by == "code" and c.get("check") not in SEVERITY:
            err(f'graded_by "code" must name an existing check in "check" (one of {", ".join(sorted(SEVERITY))})')
        elif graded_by == "judge" and scale == "continuous":
            warnings.append(f"{cid}: judges are hard to calibrate on continuous scores; consider binary")
        if not str(c.get("evidence", "")).strip():
            err('say in "evidence" what the rater looks at (the reply only? the record? the policy?)')
    return errors, warnings


def load(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def criterion(rubric: dict[str, Any], cid: str) -> dict[str, Any]:
    for c in rubric["criteria"]:
        if c.get("id") == cid:
            return c
    raise KeyError(f"No criterion '{cid}' in rubric {rubric.get('rubric')} {rubric.get('version')}")
