# Capstone decision record: candidate-v5

Reference answer for Exercise 17. Yours can differ in wording and in what you looked at; what matters is that each claim points at evidence and the decision follows from it. Numbers come from SIMULATED models and judges and ILLUSTRATIVE labels and traces.

## 1. Quality and operational requirements

Safety: zero critical failures, including across repeated runs, because one bad refund promise at real volume is a real customer. Quality: every must-pass case passes and no segment does worse than v2. Operations: every ticket that needs a specialist reaches one, at least 97% of tickets get a draft, and automated steps finish within 8 seconds (rollback triggers R1 and R5, agreed on 2026-09-11).

## 2. Baseline

The baseline is candidate-v2, the version agents use today. On the 27 cases (core plus RC-027) it passes 26 of 27 and fails RC-027, the pilot's wrong-amount case. In production traces it routed every specialist ticket correctly except T-124.

## 3. Dataset and segments

I ran the 26 core cases plus RC-027. The segments that matter most are escalation and anything involving refunds. The case set has no customer message longer than 175 characters, while 3 of 12 canary tickets were over 1,000 characters (python3 -m returns_eval traces), so long messages are an untested segment and need new cases.

## 4. Deterministic and probabilistic criteria

Code checks grade every draft, including the critical refund_commitment check. Because v5 varies from run to run, I compared 10 runs of each version (python3 -m returns_eval variance candidate-v2 candidate-v5 --runs 10 with RC-027 included). A single run is not enough for a model that varies.

## 5. Expert-labeled reference data

I used the clear-rubric tone labels. The annotators agree on 60 of 64 drafts with kappa 0.85, against 0.46 under the first rubric (python3 -m returns_eval labels), so the clear labels are worth calibrating against. They are ILLUSTRATIVE and come mostly from script-written drafts, which matters for section 8.

## 6. The judge

judge-b with data/judges/tone.v1.txt grades tone. It's from a different model family than v5. Pairwise comparisons always ask both orders and count a win only when both agree.

## 7. Judge calibration

On the holdout split, judge-b agreed with people on 24 of 30 drafts, caught 8 of 9 problems, and raised 5 false alarms, all on polite refusals and escalations (python3 -m returns_eval calibrate judge-a judge-b --split holdout). judge-a also agreed on 24 of 30 but caught only 3 of 9. judge-b's misses were sarcasm with no telltale words (L-034 in ask_customer on calibration, L-044 in inform on holdout), so people spot-check those segments.

## 8. Grader biases and critical failure modes

judge-a prefers its own family: adding the sim family's sign-off turned all 4 caught problems into passes (python3 -m returns_eval bias-check judge-a), and in a pairwise comparison judge-a picked v5 in 27 of 27 cases while judge-b's choices were 100% decided by position, so 27 ties once both orders were asked. So "the judge prefers v5" is not evidence. The critical failure mode is v5 promising refund timing: RC-002 and RC-019 failed refund_commitment in one of 10 runs, and the canary trace T-207 shows the same promise in production, blocked by the check.

## 9. Comparison across repeated runs

Over 10 runs, v5 averaged 26.8 of 27 against v2's 26.0. The 95% range for the difference is -0.4 to +2.9 cases, which includes 0, and the gain comes from one case, RC-027. So v5 is not shown to be better overall; it's shown to fix RC-027 and to add a rare critical failure.

## 10. Release criteria

G1 (no critical failures) fails for v5 once repeated runs are counted. In the canary, R1 fired: T-203, T-206, and T-210 needed a specialist and went to the general queue. R5 fired too: only 9 of 12 canary tickets got a draft. Both triggers were agreed before the canary.

## 11. Production evaluation plan and cost

Keep code checks on every draft. Use judge-b on tone, with people reviewing its flags and 30% of inform drafts: about $375 a week and about 4 problems a week nobody sees, under the limit of 5 (python3 -m returns_eval budget). Also reviewing every ask_customer draft would cost about $471, over the $400 budget, so that's a choice for the support lead: more budget, or accept the risk. Fix the evaluator so a judge error is never recorded as a pass (T-115, T-116, T-117), relabel 40 drafts a month, and keep R1 to R6 in force (python3 -m returns_eval traces).

## 12. Decision

Decision: rollback

Roll the canary back to candidate-v2 now, as R1 requires, and don't expand v5. The aggregate looks better (27 of 27 on one run, faster and cheaper), but v5 has a rare critical refund promise and, in the canary, sent three long specialist tickets to the general queue after timing out. Next: engineering makes the timeout fallback keep the escalation flag and adds long-message cases (owner: engineering lead); the team ships the Exercise 9 fix to v2 so RC-027 passes without v5 (owner: PM); v5 returns to a canary only after 10 clean repeated runs and a clean long-message case set. What would change my mind: 10 runs with no critical failure, and a week of canary traces with every specialist ticket routed correctly.
