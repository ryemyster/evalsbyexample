"""Grade candidate output against a case.

Input: a case and the attempts the harness recorded (draft + trace + error).
Output: check results per attempt and a pass/fail for the case.

Bump GRADER_VERSION whenever a check's logic changes. Runs graded by different
grader versions should not be compared directly.
"""

from __future__ import annotations

from typing import Any

from .checks import CHECKS, CRITICAL, MAJOR, CheckResult, QUESTION, SEVERITY
from .facts import build_facts

GRADER_VERSION = "1.1"


def grade_attempt(case: dict[str, Any], attempt: dict[str, Any]) -> list[CheckResult]:
    facts = build_facts(case)
    draft, trace = attempt.get("draft"), attempt.get("trace", [])
    results = []
    for name, severity, fn in CHECKS:
        if draft is None and name != "action_boundary":
            continue  # nothing to read; the error is reported below
        problems = fn(case, draft, trace, facts)
        results.append(CheckResult(name, severity, not problems, problems, QUESTION[name]))
    if attempt.get("error"):
        results.append(CheckResult("candidate_error", SEVERITY["candidate_error"], False,
                                   [attempt["error"]], QUESTION["candidate_error"]))
    return results


def attempt_passed(results: list[CheckResult]) -> bool:
    return not any(r for r in results if not r.passed and r.severity in (CRITICAL, MAJOR))


def grade_case(case: dict[str, Any], attempts: list[dict[str, Any]]) -> dict[str, Any]:
    graded = []
    for attempt in attempts:
        results = grade_attempt(case, attempt)
        graded.append({**attempt, "checks": [r.to_dict() for r in results], "passed": attempt_passed(results)})
    failed_checks = sorted({c["check"] for a in graded for c in a["checks"] if not c["passed"]},
                           key=list(SEVERITY).index)
    worst = None
    for level in (CRITICAL, MAJOR, "minor"):
        if any(SEVERITY[name] == level for name in failed_checks):
            worst = level
            break
    resolutions = [(a.get("draft") or {}).get("resolution") for a in graded]
    return {
        "case_id": case["id"],
        "category": case["category"],
        "title": case["title"],
        "must_pass": case["must_pass"],
        # For escalation recall: cases where escalating is the only acceptable outcome.
        "required_escalation": case["expected"]["acceptable_resolutions"] == ["escalate"],
        "escalated": all(r == "escalate" for r in resolutions),
        # For reliability: did every attempt give the same disposition and the same verdict?
        "stable": len({(r, a["passed"]) for r, a in zip(resolutions, graded)}) <= 1,
        "passed": all(a["passed"] for a in graded),
        "attempts_passed": sum(a["passed"] for a in graded),
        "attempts": graded,
        "failed_checks": failed_checks,
        "worst_severity": worst,
    }
