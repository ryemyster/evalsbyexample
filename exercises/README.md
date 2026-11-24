# Exercises

Seventeen short exercises. Exercises 1 to 9 follow Part 1, one or two per step of the eval process. Exercises 10 to 17 follow Part 2 ([TUTOR-PART2.md](../TUTOR-PART2.md)). Each one asks you to fill in a small piece of code or data and make a decision, and each has focused tests.

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

### Part 2

| # | Module | You edit | What you practise |
|---|---|---|---|
| 10 | Probabilistic evals | `ex10_luck_or_real.py` | Telling a real improvement from luck across repeated runs |
| 11 | Rubrics | `ex11_rubric.json` | Turning vague criteria into ones a rater can apply |
| 12 | Agreement | `ex12_agreement_beyond_chance.py` | Agreement beyond chance before trusting labels |
| 13 | Judges | `ex13_judge_prompt.txt`, `ex13_judge_findings.py` | Probing a judge for bias and fixing its prompt |
| 14 | Calibration | `ex14_judge_fitness.py` | Deciding whether, where, and how to use a judge |
| 15 | Economics | `ex15_eval_budget.json` | Spending a fixed budget on code, a judge, and people |
| 16 | Production | `ex16_failure_attribution.py` | Working out which layer caused a production failure |
| 17 | Capstone | `ex17_capstone_decision.md` | A ship, hold, or rollback decision, defended with evidence |

## Part 2 exercise cards

Each Part 2 exercise has the same nine parts. Every number mentioned comes from a command in the course; models and judges are SIMULATED and data is ILLUSTRATIVE.

### Exercise 10: Luck or a real improvement?

- **Learning objective:** tell a real improvement from run-to-run noise, and a model's mistake from a check's.
- **Scenario:** the team tried two new prompts. One run each says prompt 2 beats prompt 1 by two cases.
- **Concept:** a model can answer the same input differently. Compare versions over several runs, case by case, and look at the 95% range for the difference. A word-matching check can fail a correct paraphrase.
- **Task:** write `per_attempt_rate` and `every_attempt_rate`; then read the evidence.
- **Evidence:** `run --candidate sim-model-a` and `sim-model-b`; `report latest:sim-model-a --case RC-002`; `variance sim-model-a sim-model-b sim-model-c --runs 10`.
- **Expected failure modes:** switching prompts on one run; blaming the model for the check's literalness; reading "can't tell" as "they're the same".
- **Your decision:** is prompt 2 better? Is prompt 3? Who was wrong on RC-002?
- **Done when:** `python3 -m exercises 10` passes; the test checks your answers against freshly computed evidence.
- **Reflection:** how many runs would you want before switching a prompt in your product? What would you check that the case set doesn't cover?

### Exercise 11: Fix a vague rubric

- **Learning objective:** write criteria that two people would apply the same way.
- **Scenario:** the team's first rubric asks "Is the reply helpful?" and "Is the tone good and professional?". Labels made with it disagree.
- **Concept:** a criterion says what a rater sees in the reply, defines each value, gives examples, says what it's compared with (reference-based or reference-free), and says whether code, a judge, or a person grades it. Binary, ordinal, and continuous scales each fit different questions.
- **Task:** rewrite `ex11_rubric.json` until `rubric-check` says Ready.
- **Evidence:** `rubric-check data/rubrics/draft-quality.v0.json`, `rubric-check exercises/ex11_rubric.json`, `labels`.
- **Expected failure modes:** swapping one vague word for another ("appropriate" for "good"); two questions in one; giving a judge something code can settle.
- **Your decision:** what grades each criterion, and against what.
- **Done when:** `python3 -m exercises 11` passes: no rubric-check errors, at least five criteria, tone stays binary, and code, a judge, and people each grade something.
- **Reflection:** which criterion would people still argue about? How would you find out?

### Exercise 12: Agreement beyond chance

- **Learning objective:** check that labels are reliable before using them as an answer key.
- **Scenario:** two annotators labeled 64 drafts for tone, with the first rubric and then the clear one.
- **Concept:** percent agreement includes agreement by chance; kappa removes it. High agreement on a rare label can be no better than chance.
- **Task:** implement `cohen_kappa`; record the kappas and which labels to calibrate against.
- **Evidence:** `labels`; `review-summary latest:candidate-v2 data/human_review/*.csv` (tone: 25 of 26, kappa 0.00).
- **Expected failure modes:** trusting 78% agreement; treating a kappa band as a pass mark; forgetting that agreement isn't correctness.
- **Your decision:** which labels a judge should be measured against.
- **Done when:** `python3 -m exercises 12` passes.
- **Reflection:** your team agrees 95% of the time on something. What would you check before believing that means much?

### Exercise 13: Diagnose a judge and fix its prompt

- **Learning objective:** find a judge's biases by experiment, and reduce the ones a prompt can fix.
- **Scenario:** a judge prompt written in a hurry, and two simulated judges.
- **Concept:** judges can favor the first reply, longer replies, or their own model family; react to wording; obey instructions hidden in a reply; vary between asks; and answer in an unreadable format. Probes change one irrelevant thing and count flips.
- **Task:** fix `ex13_judge_prompt.txt`; record findings in `ex13_judge_findings.py`.
- **Evidence:** `bias-check judge-a`, `bias-check judge-b`, `calibrate judge-a --prompt exercises/ex13_judge_prompt.txt`.
- **Expected failure modes:** assuming the judge is right because it sounds confident; counting unreadable answers as passes; using a judge from the same family as the drafts.
- **Your decision:** which judge to use for sim-model drafts, and how to count pairwise wins.
- **Done when:** `python3 -m exercises 13` passes: no prompt problems, no injection or format flips with your prompt, findings match the probes.
- **Reflection:** which bias would a prompt never fix? What procedure would you add instead?

### Exercise 14: Is this judge fit for the job?

- **Learning objective:** decide whether, where, and how to use a judge from its error pattern, not its headline agreement.
- **Scenario:** judge-a and judge-b each agree with people on 24 of 30 holdout drafts.
- **Concept:** confusion matrix, recall, precision, false acceptance, false rejection, results by segment and by confidence; tune on calibration, confirm once on holdout; the bar comes from what each mistake costs.
- **Task:** implement `confusion` and `recall_precision`; record your decision.
- **Evidence:** `calibrate judge-a judge-b --split calibration`, then once `--split holdout`.
- **Expected failure modes:** picking by agreement alone; setting the bar after seeing the holdout; a segment where the judge misses problems and no person looks.
- **Your decision:** auto-pass or triage; which judge; which segments people always review; when to escalate; the recall you need.
- **Done when:** `python3 -m exercises 14` passes: your setup reaches your required recall on calibration, and your holdout answer matches what the holdout shows. Other decisions than the reference can pass.
- **Reflection:** what would make you recalibrate? Who should own that?

### Exercise 15: Spend an evaluation budget

- **Learning objective:** design a sustainable checking plan from measured error rates and stated assumptions.
- **Scenario:** people check every draft's tone today; that's $750 a week against a $400 budget, and the support lead allows at most 5 unseen rude replies a week.
- **Concept:** code checks on everything; a judge where it's reliable; people where it isn't; escalation on low confidence; spot checks; recalibration costs; cost per problem caught and per resolved ticket.
- **Task:** edit `ex15_eval_budget.json`.
- **Evidence:** `budget exercises/ex15_eval_budget.json`, `calibrate`, `bias-check`.
- **Expected failure modes:** cutting cost by dropping review where the judge is blind; using the labeled set's problem rate as real traffic's; forgetting relabeling.
- **Your decision:** which judge, where people look, and why.
- **Done when:** `python3 -m exercises 15` passes: within budget, within the limit, evidence that points at real commands, and reasons with numbers.
- **Reflection:** which assumption, if wrong, would break your plan? How would you measure it?

### Exercise 16: Which layer failed?

- **Learning objective:** attribute production failures to the layer that caused them, and route each fix to the right place.
- **Scenario:** a week of production and canary traces.
- **Concept:** a trace records every step; trajectory checks name symptoms; model, orchestration, policy, data, evaluator, and human-review failures need different owners and fixes; only model failures belong in the offline case set.
- **Task:** implement `specialist_routed`; attribute seven traces; choose which become offline cases; explain T-122.
- **Evidence:** `traces`, `traces --trace T-105` (and the others).
- **Expected failure modes:** blaming the model for everything; adding a test case for a routing bug; counting a failure the system caught as a system failure.
- **Your decision:** the layer for each trace, and where each fix goes.
- **Done when:** `python3 -m exercises 16` passes.
- **Reflection:** who owns each layer at your company? Who would notice an evaluator failure?

### Exercise 17: Capstone: ship, hold, or roll back candidate-v5

- **Learning objective:** run the whole evaluation and defend a decision with evidence.
- **Scenario:** candidate-v5 is faster, cheaper, fixes the pilot's wrong-amount case, and has been on 10% of tickets for a week. The team lead wants to move everyone to it.
- **Concept:** everything in Parts 1 and 2: requirements, baseline, segments, deterministic and repeated checks, labels, a calibrated judge and its biases, release criteria, a budget, and production triggers.
- **Task:** fill in the 12 sections of `ex17_capstone_decision.md`.
- **Evidence:** whatever you ask for. `run`, `variance`, `judge --versus`, `calibrate`, `bias-check`, `budget`, and `traces` all apply.
- **Expected failure modes:** deciding from one run; trusting a judge's preference without checking its family; ignoring the canary; overriding an agreed trigger without saying who agreed.
- **Your decision:** ship, hold, or roll back, with next steps and owners.
- **Done when:** `python3 -m exercises 17` passes (complete, evidence that exists, not "ship"), and you've scored your reasoning with the [Part 2 checklist](../docs/check-yourself.md#part-2-capstone).
- **Reflection:** what would change your mind? What would you do first on Monday?

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
