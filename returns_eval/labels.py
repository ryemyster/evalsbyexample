"""Human-labeled drafts: the answer key for checking an automated judge.

The labels live in data/labels/ (ILLUSTRATIVE: invented for teaching). Each item is
one draft reply, labeled for one criterion (tone) by two annotators, first with the
team's vague first rubric and then with the clear one. Where the two disagreed under
the clear rubric, the team settled it ("adjudicated") and wrote why in the note.

`health()` checks the things that quietly ruin a calibration set:
  - the rubric: do the annotators agree, beyond what chance would give?
  - leakage: does any case, or any near-identical draft, appear in two splits?
  - contamination: has any holdout draft been pasted into a judge prompt?
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .cases import DATA_DIR
from .report import frac
from .stats import cohen_kappa

LABELS_DIR = DATA_DIR / "labels"
LABELS_MANIFEST = LABELS_DIR / "manifest.json"
JUDGE_PROMPTS_DIR = DATA_DIR / "judges"
SPLITS = ("train", "calibration", "holdout")
LABEL_VALUES = ("ok", "problem")
ITEM_FIELDS = {"item_id", "split", "case_id", "segment", "source", "family", "reply_text",
               "first_rubric_labels", "labels", "final", "note"}


def manifest() -> dict[str, Any]:
    return json.loads(LABELS_MANIFEST.read_text(encoding="utf-8"))


def default_file() -> Path:
    return LABELS_DIR / manifest()["file"]


def load_items(path: str | Path | None = None, split: str | None = None) -> list[dict[str, Any]]:
    path = Path(path or default_file())
    items = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    problems = []
    for item in items:
        missing = ITEM_FIELDS - item.keys()
        if missing:
            problems.append(f"{item.get('item_id', '?')}: missing {sorted(missing)}")
        elif item["split"] not in SPLITS or item["final"] not in LABEL_VALUES:
            problems.append(f"{item['item_id']}: split must be one of {SPLITS} and final one of {LABEL_VALUES}")
    if problems:
        raise SystemExit("Label file has problems:\n  " + "\n  ".join(problems))
    if split and split != "all":
        if split not in SPLITS:
            raise SystemExit(f"Unknown split '{split}'. Use one of: {', '.join(SPLITS)}, or all.")
        items = [i for i in items if i["split"] == split]
    return items


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.lower()))


def near_duplicates(items: list[dict[str, Any]], threshold: float = 0.8) -> list[tuple[str, str, float]]:
    """Pairs of drafts in DIFFERENT splits whose words overlap a lot (Jaccard similarity)."""
    out = []
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if a["split"] == b["split"]:
                continue
            wa, wb = _words(a["reply_text"]), _words(b["reply_text"])
            sim = len(wa & wb) / len(wa | wb) if wa | wb else 0
            if sim >= threshold:
                out.append((a["item_id"], b["item_id"], sim))
    return out


def prompt_contamination(items: list[dict[str, Any]], prompt_files: list[Path]) -> list[tuple[str, str]]:
    """(holdout item id, prompt file) wherever a holdout draft's text appears in a judge prompt."""
    out = []
    for path in prompt_files:
        text = path.read_text(encoding="utf-8")
        for item in items:
            if item["split"] == "holdout" and item["reply_text"][:60] in text:
                out.append((item["item_id"], path.name))
    return out


def health(items: list[dict[str, Any]], prompt_files: list[Path] | None = None) -> list[str]:
    m = manifest()
    prompt_files = prompt_files if prompt_files is not None else sorted(JUDGE_PROMPTS_DIR.glob("*.txt"))
    out = [f"Human labels for '{m['criterion']}': {len(items)} drafts (dataset {m['dataset']} {m['version']})",
           "ILLUSTRATIVE: the drafts' labels and annotators are invented for teaching.", ""]
    out.append(f"{'split':<14}{'drafts':>8}{'problem':>10}{'cases':>8}   what it's for")
    for split in SPLITS:
        rows = [i for i in items if i["split"] == split]
        if rows:
            out.append(f"{split:<14}{len(rows):>8}{sum(i['final'] == 'problem' for i in rows):>10}"
                       f"{len({i['case_id'] for i in rows}):>8}   {m['splits'][split]}")
    segments = sorted({i["segment"] for i in items})
    out += ["", "Drafts per segment (the draft's next step), and how many have a tone problem"]
    for seg in segments:
        rows = [i for i in items if i["segment"] == seg]
        out.append(f"  {seg:<18}{len(rows):>4} drafts, {sum(i['final'] == 'problem' for i in rows)} problem")

    out += ["", "Do the two annotators agree? (the same drafts, rated separately)"]
    for key, name in (("first_rubric_labels", f"first rubric ({m['first_rubric']})"), ("labels", f"clear rubric ({m['rubric']})")):
        a = [i[key]["annotator-a"] for i in items]
        b = [i[key]["annotator-b"] for i in items]
        agree = sum(x == y for x, y in zip(a, b))
        kappa = cohen_kappa(a, b)
        kappa_text = "n/a" if kappa is None else f"{kappa:.2f}"
        out.append(f"  {name:<32} same label {frac(agree, len(a)):>14}   beyond chance (kappa) {kappa_text}")
    out.append("  kappa: 1 = always agree; 0 = no better than chance. Same-label % alone looks better than it is,")
    out.append("  because two people who both say 'ok' to most drafts agree often by chance.")
    split_disagree = [i["item_id"] for i in items if i["labels"]["annotator-a"] != i["labels"]["annotator-b"]]
    if split_disagree:
        out.append(f"  Settled by discussion (clear rubric): {', '.join(split_disagree)}. Each item's note says why.")

    out += ["", "Leakage and contamination checks"]
    by_case: dict[str, set[str]] = {}
    for i in items:
        by_case.setdefault(i["case_id"], set()).add(i["split"])
    shared = sorted(c for c, s in by_case.items() if len(s) > 1)
    out.append("  ok: no case appears in two splits" if not shared else
               f"  PROBLEM: these cases appear in more than one split: {', '.join(shared)}")
    dupes = near_duplicates(items)
    out.append("  ok: no near-identical drafts in different splits" if not dupes else
               "  PROBLEM: near-identical drafts in different splits: "
               + ", ".join(f"{a}~{b} ({s:.0%})" for a, b, s in dupes))
    leaks = prompt_contamination(items, prompt_files)
    out.append(f"  ok: no holdout draft appears in the {len(prompt_files)} judge prompt file(s)" if not leaks else
               "  PROBLEM: holdout drafts appear in judge prompts: " + ", ".join(f"{i} in {f}" for i, f in leaks))
    return out
