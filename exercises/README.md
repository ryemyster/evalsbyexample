# Exercises

Nine short exercises, one or two per step of the eval process. Each one asks you to fill in a small piece of code or data, and each has focused tests.

```bash
python3 -m exercises 1            # check your work on Exercise 1
python3 -m exercises all          # check everything
python3 -m exercises 1 --solution # run the same tests against the reference solution
```

Unfinished exercises fail with a message that says what's left, for example:

```
Exercise 3: Write a deterministic check: refund timing promises [your work]
  0 / 5 tests passed
  - test_flags_each_promise: Exercise 3 is not done yet: implement find_refund_timing_promises() ...
```

These tests are separate from the repository's own tests (`python3 -m unittest discover -s tests -t .`), which pass on a fresh clone whether or not you've done the exercises. Reference solutions are in `solutions/`. Try first, then compare.

| # | Step | You edit | What you practice |
|---|---|---|---|
| 1 | 1–3 Decision, baseline, success criteria | `ex01_eval_charter.py` | Writing the product question, the baseline, success at three levels, and mapping unacceptable failures to checks |
| 2 | 4 Build cases | `ex02_new_case.json` | Turning a policy rule (refund to a different card → escalate) into a case, including the tempting wrong answer |
| 3 | 5 Deterministic grading | `ex03_refund_timing_check.py` | Writing a code check for refund timing promises, and seeing where regex checks stop |
| 4 | 5 Human review | `ex04_reviewer_agreement.py` | Measuring reviewer agreement before trusting human ratings |
| 5 | 6 Compare by failure category | `ex05_failure_categories.py` | Showing what candidate-v1's higher average hides |
| 6 | 7 Release gates | `ex06_release_decision.py` | Writing a decision where a critical failure can't be averaged away |
| 7 | 8 Offline vs. pilot | `ex07_pilot_outcomes.py` | Reading pilot outcomes by request type, with sample sizes |
| 8 | 9 Regression case | `ex08_regression_case.json`, then `data/cases/` | Turning a pilot incident into a must-pass case that the current candidate fails |
| 9 | 9 Fix and rerun | `ex09_candidate_v3.py` | Fixing the candidate and rerunning every case, not just the new one |

## Notes on specific exercises

**Exercise 2.** After the tests pass, run candidate-v2 on your case:

```bash
python3 -m returns_eval run --candidate candidate-v2 --cases exercises/ex02_new_case.json
```

It fails. candidate-v2 doesn't know the "refund to a different payment method" rule, because no case ever tested it. That's what a new case is for. (Fixing v2 for it is an optional extra.)

**Exercise 8.** Read the incident first: `python3 -m returns_eval pilot`. Fill in the `TODO` fields in `exercises/ex08_regression_case.json`, then:

```bash
python3 -m returns_eval add-case exercises/ex08_regression_case.json
```

Then bump `"version"` in `data/cases/manifest.json` from `1.0` to `1.1` and add a changelog entry. Rerun candidate-v2; it should now fail RC-027:

```bash
python3 -m returns_eval run --candidate candidate-v2
```

**Exercise 9.** Implement one method, then run the whole case set, not just RC-027:

```bash
python3 -m returns_eval run --candidate exercises.ex09_candidate_v3:CandidateV3 --baseline baseline
```

To start an exercise over: `python3 -m returns_eval reset --exercises 3` (your attempt is copied to `backups/` first). `python3 -m returns_eval reset` with no options lists every file you've changed.
