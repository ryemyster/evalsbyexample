"""Run exercise tests.

    python3 -m exercises 3              # check your work on Exercise 3
    python3 -m exercises all            # check every exercise
    python3 -m exercises 3 --solution   # run the same tests against the reference solution
"""

from __future__ import annotations

import sys

if sys.version_info < (3, 9):  # checked before anything else, for a clear message
    sys.exit("This project needs Python 3.9 or newer. You have " + sys.version.split()[0] + ".")

import argparse  # noqa: E402
import os  # noqa: E402
import unittest  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
TITLES = {
    1: "Write the eval charter (decision, baseline, success, unacceptable failures)",
    2: "Write a new test case",
    3: "Write a deterministic check: refund timing promises",
    4: "Measure agreement between human reviewers",
    5: "Compare baseline and candidate by failure category",
    6: "Write the release decision: criticals can't be averaged away",
    7: "Read pilot outcomes, not just offline scores",
    8: "Turn a pilot incident into a regression case",
    9: "Fix the candidate and rerun everything",
}


def check(n: int) -> tuple[int, int]:
    """Run one exercise's tests quietly. Returns (tests passed, tests run)."""
    sys.path.insert(0, str(HERE.parent))
    result = unittest.TestResult()
    unittest.TestLoader().loadTestsFromName(f"exercises.tests.test_ex{n:02d}").run(result)
    return result.testsRun - len(result.failures) - len(result.errors), result.testsRun


def main() -> int:
    parser = argparse.ArgumentParser(prog="python3 -m exercises", description="Run exercise tests.")
    parser.add_argument("which", help="exercise number (1-9) or 'all'")
    parser.add_argument("--solution", action="store_true", help="test the reference solutions instead")
    args = parser.parse_args()
    if args.solution:
        os.environ["EVALS_USE_SOLUTIONS"] = "1"
    numbers = sorted(TITLES) if args.which == "all" else [int(args.which)]
    if any(n not in TITLES for n in numbers):
        parser.error("exercise must be 1-9 or 'all'")

    sys.path.insert(0, str(HERE.parent))
    loader = unittest.TestLoader()
    all_ok = True
    for n in numbers:
        suite = loader.loadTestsFromName(f"exercises.tests.test_ex{n:02d}")
        result = unittest.TestResult()
        suite.run(result)
        problems = result.failures + result.errors
        ok = not problems
        all_ok &= ok
        label = "solution" if args.solution else "your work"
        print(f"Exercise {n}: {TITLES[n]} [{label}]")
        skipped = f" ({len(result.skipped)} skipped)" if result.skipped else ""
        print(f"  {result.testsRun - len(problems)} / {result.testsRun} tests passed{skipped}")
        for test, trace in problems:
            last = [line for line in trace.strip().splitlines() if line.strip()][-1]
            message = last.split(": ", 1)[1] if last.startswith(("AssertionError", "Exception")) and ": " in last else last
            message = message.split(" : ", 1)[-1]
            print(f"  - {test._testMethodName}: {message}")
        print()
    if not all_ok and not args.solution:
        print("See exercises/README.md for instructions. Reference solutions: solutions/")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
