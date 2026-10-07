"""Load and validate test cases and policies.

A case set is one or more JSONL files (one JSON object per line). The field
reference is docs/case-format.md. `validate_case` returns plain-language
problems instead of raising, so a learner editing a case sees every mistake at
once.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .models import RESOLUTIONS

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CASES_DIR = DATA_DIR / "cases"
POLICIES_DIR = DATA_DIR / "policies"
MANIFEST = CASES_DIR / "manifest.json"

CASE_CATEGORIES = (
    "common",
    "missing_info",
    "conflicting_data",
    "policy_exception",
    "wrong_order_risk",
    "escalation",
    "unauthorized_action",
)

ORDER_ID_RE = re.compile(r"^EO-\d{5}$")
CASE_ID_RE = re.compile(r"^RC-\d{3}$")

CASE_FIELDS = {
    "id", "title", "category", "source", "added_in", "must_pass", "as_of",
    "policy_version", "customer", "message", "orders", "expected",
    "unacceptable_outcomes",
}
EXPECTED_FIELDS = {
    "acceptable_resolutions", "target_order_id", "other_allowed_order_ids",
    "behavior", "must_mention", "must_not_mention",
}
CUSTOMER_FIELDS = {"customer_id", "name", "email", "returns_last_60_days"}
ORDER_FIELDS = {
    "order_id", "customer_id", "customer_name", "customer_email", "placed_on",
    "delivered_on", "shipping_status", "items", "order_total", "return",
    "refund", "notes",
}
ITEM_FIELDS = {"sku", "name", "category", "price", "final_sale", "opened"}


class CaseError(ValueError):
    """Raised when a case file cannot be used."""


@dataclass(frozen=True)
class CaseSet:
    cases: list[dict[str, Any]]
    version: str   # human label from manifest.json, or "custom"
    sha256: str    # hash of the exact case content, so edits are detectable
    files: list[str]


def _is_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _is_money(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"\d+\.\d{2}", value) is not None


def available_policy_versions() -> set[str]:
    return {p.stem for p in POLICIES_DIR.glob("*.json")}


def validate_case(case: Any, policy_versions: set[str] | None = None) -> list[str]:
    """Return a list of problems. An empty list means the case is usable."""
    if not isinstance(case, dict):
        return ["A case must be a JSON object."]
    problems: list[str] = []
    cid = case.get("id", "<no id>")

    def bad(msg: str) -> None:
        problems.append(f"{cid}: {msg}")

    missing = CASE_FIELDS - case.keys()
    extra = case.keys() - CASE_FIELDS
    for name in sorted(missing):
        bad(f"missing field '{name}'")
    for name in sorted(extra):
        bad(f"unknown field '{name}' (typo? see docs/case-format.md)")
    if missing:
        return problems

    if not isinstance(cid, str) or not CASE_ID_RE.match(cid):
        bad("'id' must look like RC-001")
    for text_field in ("title", "source", "added_in", "message"):
        if not isinstance(case[text_field], str) or not case[text_field].strip():
            bad(f"'{text_field}' must be a non-empty string")
        elif "TODO" in case[text_field]:
            bad(f"'{text_field}' still contains TODO")
    if case["category"] not in CASE_CATEGORIES:
        bad(f"'category' must be one of {', '.join(CASE_CATEGORIES)}")
    if not isinstance(case["must_pass"], bool):
        bad("'must_pass' must be true or false")
    if not _is_date(case["as_of"]):
        bad("'as_of' must be a date like 2026-08-14")
    versions = policy_versions if policy_versions is not None else available_policy_versions()
    if case["policy_version"] not in versions:
        bad(f"'policy_version' must be one of {sorted(versions)}")

    customer = case["customer"]
    if not isinstance(customer, dict) or set(customer) != CUSTOMER_FIELDS:
        bad(f"'customer' must have exactly these fields: {sorted(CUSTOMER_FIELDS)}")
        customer = {}
    elif not str(customer["email"]).endswith("@example.com"):
        bad("customer email must use @example.com so it is clearly fictional")

    order_ids: set[str] = set()
    own_ids: set[str] = set()
    if not isinstance(case["orders"], list):
        bad("'orders' must be a list (it may be empty)")
    else:
        for order in case["orders"]:
            problems.extend(_validate_order(cid, order))
            if isinstance(order, dict):
                order_ids.add(order.get("order_id"))
                if order.get("customer_id") == customer.get("customer_id"):
                    own_ids.add(order.get("order_id"))

    expected = case["expected"]
    if not isinstance(expected, dict) or set(expected) != EXPECTED_FIELDS:
        bad(f"'expected' must have exactly these fields: {sorted(EXPECTED_FIELDS)}")
    else:
        res = expected["acceptable_resolutions"]
        if not isinstance(res, list) or not res or any(r not in RESOLUTIONS for r in res):
            bad(f"'expected.acceptable_resolutions' must be a non-empty list drawn from {', '.join(RESOLUTIONS)}")
        target = expected["target_order_id"]
        if target is not None and target not in own_ids:
            bad("'expected.target_order_id' must be null or one of this customer's own orders")
        for oid in expected["other_allowed_order_ids"]:
            if oid not in own_ids:
                bad(f"'expected.other_allowed_order_ids' contains {oid}, which is not this customer's order")
        if not isinstance(expected["behavior"], str) or not expected["behavior"].strip():
            bad("'expected.behavior' must describe the right outcome in plain words")
        elif "TODO" in expected["behavior"]:
            bad("'expected.behavior' still contains TODO")
        groups = expected["must_mention"]
        if not isinstance(groups, list) or any(
            not isinstance(g, list) or not g or not all(isinstance(p, str) and p for p in g)
            for g in groups
        ):
            bad("'expected.must_mention' must be a list of non-empty lists of phrases, e.g. [[\"label\"], [\"inspect\", \"inspection\"]]")
        phrases = expected["must_not_mention"]
        if not isinstance(phrases, list) or not all(isinstance(p, str) and p for p in phrases):
            bad("'expected.must_not_mention' must be a list of phrases")

    unacceptable = case["unacceptable_outcomes"]
    if not isinstance(unacceptable, list) or not unacceptable:
        bad("'unacceptable_outcomes' must list at least one outcome in plain words")
    return problems


def _validate_order(cid: str, order: Any) -> list[str]:
    problems: list[str] = []
    if not isinstance(order, dict):
        return [f"{cid}: every order must be a JSON object"]
    oid = order.get("order_id", "<no order_id>")
    missing = ORDER_FIELDS - order.keys()
    if missing:
        return [f"{cid}: order {oid} is missing {sorted(missing)}"]
    if not ORDER_ID_RE.match(str(oid)):
        problems.append(f"{cid}: order id {oid} must look like EO-10417")
    if not _is_date(order["placed_on"]):
        problems.append(f"{cid}: order {oid} 'placed_on' must be a date")
    if order["delivered_on"] is not None and not _is_date(order["delivered_on"]):
        problems.append(f"{cid}: order {oid} 'delivered_on' must be a date or null")
    if not _is_money(order["order_total"]):
        problems.append(f"{cid}: order {oid} 'order_total' must look like \"89.00\"")
    items = order["items"]
    if not isinstance(items, list) or not items:
        problems.append(f"{cid}: order {oid} needs at least one item")
    else:
        for it in items:
            if not isinstance(it, dict) or set(it) != ITEM_FIELDS:
                problems.append(f"{cid}: order {oid} items need exactly {sorted(ITEM_FIELDS)}")
            elif not _is_money(it["price"]):
                problems.append(f"{cid}: order {oid} item price must look like \"89.00\"")
    refund = order["refund"]
    if not isinstance(refund, dict) or refund.get("status") not in ("not_issued", "issued"):
        problems.append(f"{cid}: order {oid} 'refund.status' must be not_issued or issued")
    return problems


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    cases = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                cases.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise CaseError(f"{path}:{lineno}: not valid JSON ({exc.msg}). Each line must be one complete case.") from exc
    return cases


def read_case_file(path: Path) -> list[dict[str, Any]]:
    """Read .jsonl (one case per line) or .json (one case or a list)."""
    path = Path(path)
    if not path.exists():
        raise CaseError(f"Case file not found: {path}")
    if path.suffix == ".jsonl":
        return _read_jsonl(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def load_case_set(paths: list[str | Path] | None = None) -> CaseSet:
    """Load cases from the manifest (default) or from explicit files."""
    if paths:
        files = [Path(p) for p in paths]
        version = "custom"
    else:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        files = [CASES_DIR / name for name in manifest["files"]]
        version = manifest["version"]

    cases: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    for path in files:
        for case in read_case_file(path):
            cases.append(case)
            digest.update(json.dumps(case, sort_keys=True).encode("utf-8"))

    versions = available_policy_versions()
    problems = [p for case in cases for p in validate_case(case, versions)]
    ids = [c.get("id") for c in cases]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        problems.append(f"Duplicate case ids: {', '.join(dupes)}")
    if problems:
        raise CaseError("Case set has problems:\n  " + "\n  ".join(problems))
    return CaseSet(cases=cases, version=version, sha256=digest.hexdigest()[:12],
                   files=[_display_path(p) for p in files])


def subset(case_set: CaseSet, ids: list[str]) -> CaseSet:
    """Keep only some cases, e.g. to try a paid model on a few cases first.

    The version and hash change, so a subset run is never compared with a full run by mistake.
    """
    wanted = [i.upper() for i in ids]
    known = {c["id"] for c in case_set.cases}
    missing = [i for i in wanted if i not in known]
    if missing:
        raise CaseError(f"Not in this case set: {', '.join(missing)}")
    cases = [c for c in case_set.cases if c["id"] in wanted]
    digest = hashlib.sha256()
    for case in cases:
        digest.update(json.dumps(case, sort_keys=True).encode("utf-8"))
    return CaseSet(cases=cases, version=f"{case_set.version}-subset", sha256=digest.hexdigest()[:12], files=case_set.files)


def _display_path(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_policy(version: str) -> dict[str, Any]:
    path = POLICIES_DIR / f"{version}.json"
    if not path.exists():
        raise CaseError(f"Unknown policy version '{version}'. Files live in {POLICIES_DIR}.")
    return json.loads(path.read_text(encoding="utf-8"))
