# Evaluation techniques: what each one can and can't tell you

Every technique in this course answers some questions and is blind to others. This page gives each one the same card, so you can pick the right mix for a decision. Where to practise each one is in the last line of its card. Research behind them: [sources.md](sources.md).

## Code checks (deterministic)

- **Measures:** facts a record can settle: an action taken, another customer's data shown, a refund promised, a price or date not in the record, a required phrase missing.
- **Can't measure:** tone, whether a policy reading is sensible, whether different wording means the same thing, anything nobody wrote a check for.
- **Use when:** the answer is in the data, and a mistake is serious. Run them on every draft; they cost almost nothing.
- **Don't use when:** the check would need judgment. A brittle check that fails good drafts trains people to ignore it.
- **You'll need:** the record the check compares with, written evidence for every failure, and checks run against known-good drafts before trusting them.
- **Common failure modes:** new phrasings slip past (Lesson 3); correct paraphrases fail exact-phrase checks (Lesson 10, RC-002); "in the record" isn't "correct" (the pilot's order total).
- **Changes decisions by:** enforcing the critical gate. One critical failure blocks release, whatever the average.
- **Practise:** Lessons 3 and 8, Exercise 3. `run`, `report --case`.

## Human review with a rubric

- **Measures:** what people who do the job think: usability, tone, policy reading, whether the test case itself is right.
- **Can't measure:** anything at the scale of every draft (it's slow and costly), or anything the rubric doesn't define clearly.
- **Use when:** the criterion needs expertise, to settle what code and judges disagree on, and to build the labels a judge is checked against.
- **Don't use when:** code can settle it, or when reviewers would rubber-stamp (seconds per draft, Lesson 15).
- **You'll need:** a rubric that passes `rubric-check`, reviewers blind to automated results, fresh reviews when drafts change, and a way to settle disagreements.
- **Common failure modes:** vague criteria ("is it helpful?"); reviewers anchoring on the code's verdict; stale reviews of old drafts; reporting an average that hides disagreement.
- **Changes decisions by:** gate G6, and by deciding which segments a judge can't be trusted on.
- **Practise:** Lesson 3, Lesson 11, Exercises 4 and 11. `review-sheet`, `review-summary`, `rubric-check`.

## Agreement between people

- **Measures:** whether two people applying the same rubric to the same drafts reach the same label. Percent agreement, and **kappa** (agreement beyond chance).
- **Can't measure:** whether they're right. Two people can agree on the wrong answer.
- **Use when:** before using labels as an answer key, and whenever the rubric changes.
- **Don't use when:** only one label is ever used (kappa can't be computed), or with one reviewer (there's nothing to compare).
- **You'll need:** two or more people labeling independently, and a written reason for each settled disagreement.
- **Common failure modes:** high percent agreement on a rare label is mostly chance (tone: 25 of 26, kappa 0.00); treating a kappa band like "substantial" as a pass mark ([sources.md](sources.md)).
- **Changes decisions by:** deciding whether labels are fit to calibrate a judge against (clear rubric: kappa 0.85; first rubric: 0.46).
- **Practise:** Lesson 11, Exercises 4 and 12. `labels`, `review-summary`.

## Repeated runs and statistics

- **Measures:** how much a version's score moves on its own from run to run; which cases are unstable; whether a gap between versions is bigger than that wobble; rare failures that only show up in some runs.
- **Can't measure:** behavior on requests the case set doesn't cover. More runs make the estimate tighter, not the case set wider.
- **Use when:** comparing anything that can answer differently each time: models, prompts, temperatures.
- **Don't use when:** the candidate is deterministic (every run is the same; one is enough).
- **You'll need:** the same cases for every version, enough runs (the course uses 10), and paired comparison (case by case, not average against average).
- **Common failure modes:** declaring a winner from one run (Lesson 10: one run says prompt 2 is better by two cases; ten runs can't tell); missing a rare critical failure because the one run you did was lucky (the capstone).
- **Changes decisions by:** turning "B scored higher" into "B is better, by about this much, or we can't tell yet", and by making G1 apply across every run.
- **Practise:** Lesson 10, Exercise 10, the capstone. `variance`, `run --repeat`, `run --seed`.

## Structured output validation

- **Measures:** whether a model's raw reply follows the agreed format (fields, types, allowed values).
- **Can't measure:** whether the content is right.
- **Use when:** code reads the model's output: always, for model-backed candidates and judges.
- **Don't use when:** never skip it; but keep it in the grader, not only in the code that tidies output up.
- **You'll need:** a written format, and a grader that parses the raw text itself.
- **Common failure modes:** cleanup code that turns a broken answer into a safe-looking one (an invalid next step becoming "escalate"); counting a judge's unreadable answer as a pass.
- **Changes decisions by:** making format failures visible as major failures instead of hidden repairs.
- **Practise:** Lesson 10. The `structured_output` check; `bias-check` format probe.

## Judge: grading one reply (pointwise)

- **Measures:** whether a reply meets a written criterion, at the scale of every draft, cheaply.
- **Can't measure:** anything reliably until it's been checked against people for this criterion, these drafts, and this use.
- **Use when:** the criterion needs reading comprehension (tone, completeness in any wording), volume is too high for people, and you have labels to check it against.
- **Don't use when:** code can settle it; or the cost of a missed problem is high and the judge's measured recall in that segment is low.
- **You'll need:** a rubric definition in the prompt; the reply fenced and marked as content; a JSON answer with a verdict, a reason, and a confidence; a judge from a different family than the model it grades; a versioned prompt file.
- **Common failure modes:** grading by its own idea of "good"; obeying instructions hidden in the reply; going easy on long or familiar-sounding text; unreadable answers treated as passes.
- **Changes decisions by:** letting people spend their time on flagged and unsure drafts instead of all drafts, once calibration shows that's safe.
- **Practise:** Lesson 12, Exercise 13. `judge`, `bias-check`.

## Judge: comparing two replies (pairwise)

- **Measures:** which of two versions people would prefer on a criterion, case by case.
- **Can't measure:** whether either one is good enough. Both can be bad.
- **Use when:** choosing between versions or prompts.
- **Don't use when:** you need a pass/fail gate.
- **You'll need:** both orders asked for every pair, with a win counted only when both agree.
- **Common failure modes:** position bias (in the capstone, judge-b's preference was decided by the order every time); self-preference (judge-a preferred its own family's v5 in 27 of 27 cases).
- **Changes decisions by:** adding a preference signal to compare, once position and family effects are ruled out.
- **Practise:** Lesson 12, capstone. `judge --versus`.

## Judge: grading against a reference

- **Measures:** whether a reply does what a reference (the expected behavior) says, in any wording.
- **Can't measure:** anything the reference leaves out, or whether the reference itself is right.
- **Use when:** exact-phrase checks fail correct paraphrases.
- **Don't use when:** there's no trustworthy reference.
- **You'll need:** a reference written so two people would agree on it (`case_expectation_ok` on the scorecard flags bad ones).
- **Common failure modes:** a wrong reference makes the judge confidently wrong.
- **Changes decisions by:** separating "the model was wrong" from "the check was too literal" (RC-002 and RC-021 in Lesson 12).
- **Practise:** Lesson 12. `judge --criterion complete`.

## Judge calibration

- **Measures:** what a judge catches (recall), how often its flags are real (precision), missed problems and false alarms, agreement beyond chance, all compared with people's labels, by segment and by the judge's own confidence.
- **Can't measure:** performance on drafts unlike the labeled ones, or after the prompt, model, or traffic changes (calibration drift). Recalibrate after any change.
- **Use when:** before trusting any judge, and on a schedule after.
- **Don't use when:** the labels themselves aren't reliable (check agreement first).
- **You'll need:** labels split by case into train, calibration, and holdout; tune on calibration; use the holdout once.
- **Common failure modes:** two judges with the same agreement making opposite mistakes (judge-a and judge-b: 24 of 30 each); tuning against the holdout until it stops being a fair test; small samples (the 95% ranges are wide).
- **Changes decisions by:** deciding which segments can be automated, which keep people, and when to escalate. The required recall comes from what a missed problem costs, not from a universal number.
- **Practise:** Lesson 13, Exercise 14. `calibrate`, `labels`.

## Bias probes

- **Measures:** whether a judge's verdict moves when something that shouldn't matter changes: order, length, a family sign-off, the question's wording, hidden instructions, asking again, format.
- **Can't measure:** biases nobody wrote a probe for.
- **Use when:** before adopting a judge, and after changing its prompt or model.
- **Don't use when:** on the holdout split (the course never does).
- **You'll need:** labeled drafts and a list of changes that people agree don't change the answer.
- **Common failure modes:** assuming no flips on your probes means no bias anywhere.
- **Changes decisions by:** choosing the judge, its prompt, and procedures like asking both orders.
- **Practise:** Lesson 12, Exercise 13. `bias-check`.

## Sampling and budgets

- **Measures:** the expected weekly cost of a checking plan and the problems expected to get past it, from measured judge errors and stated assumptions.
- **Can't measure:** the real problem rate in production. That has to be measured with a random sample of real traffic.
- **Use when:** deciding how much of each kind of checking to buy.
- **Don't use when:** the judge hasn't been calibrated (its error rates would be guesses).
- **You'll need:** volumes, rates, and prices written down as assumptions, and a limit on missed problems agreed in advance.
- **Common failure modes:** using the labeled set's problem rate as production's (it was built to include many problems); forgetting the cost of recalibration; ignoring uncertainty in rates measured on a few drafts.
- **Changes decisions by:** showing the trade-off: in the course's assumptions, a judge that's honest about when it's unsure, plus spot checks where it's blind, costs less than a stricter judge whose false alarms all need a person.
- **Practise:** Lesson 14, Exercise 15. `budget`.

## Trace (trajectory) checks

- **Measures:** whether each step around the model did its job: right policy version, right orders, judge errors not counted as passes, specialist routing, a real human review, the right ticket, time limits.
- **Can't measure:** which layer is to blame. A check names a symptom; attribution needs a person reading the trace.
- **Use when:** in production and shadow, on every trace or a sample.
- **Don't use when:** never skip it once real traffic flows.
- **You'll need:** traces that record every step, and owners for each layer.
- **Common failure modes:** blaming the model for an orchestration or data failure (and adding a test case that can never catch it); treating a failure the system caught (T-122) as a system failure.
- **Changes decisions by:** sending each failure to the owner and fix that can stop it, and by firing rollback triggers.
- **Practise:** Lesson 15, Exercise 16. `traces`.

## Shadow and canary deployments

- **Measures:** shadow: a new version's behavior on real requests, with nothing shown to anyone. Canary: its effect on a small share of real tickets.
- **Can't measure:** shadow can't show how people react to drafts; a small canary can't rule out rare failures.
- **Use when:** after offline gates pass, before wider rollout.
- **Don't use when:** offline gates haven't passed.
- **You'll need:** rollback triggers agreed before starting, a simple switch back, and traces.
- **Common failure modes:** moving the goalposts after seeing results; real traffic unlike the case set (long messages in the capstone).
- **Changes decisions by:** a trigger fires, and the agreed action happens: in the capstone, roll back.
- **Practise:** Lesson 15, capstone. `traces`.

## Supervised pilot

- **Measures:** whether the job got easier and customers better served: handling time, rework, repeat contacts, errors agents caught.
- **Can't measure:** rare failures (small numbers), or causes when groups get different request mixes.
- **Use when:** after offline gates and human review pass.
- **You'll need:** a comparison group working without the tool, results by request type, and every caught error turned into a case.
- **Common failure modes:** reading "used as-is" as "good"; comparing overall averages across different request mixes.
- **Changes decisions by:** deciding whether to expand, narrow, or stop.
- **Practise:** Lesson 6, Exercise 7. `pilot`.

## Regression cases and dataset versioning

- **Measures:** whether a known mistake stays fixed.
- **Can't measure:** new kinds of mistake.
- **Use when:** every real failure the model caused becomes a case; every case-set change bumps the version.
- **Don't use when:** the failure was in another layer (routing, data, policy service). Fix and test it there.
- **You'll need:** case-set and label versions, changelogs, and comparisons that refuse to mix versions.
- **Common failure modes:** fixing the new case and breaking an old one (rerun everything); quietly editing cases so old and new runs get compared.
- **Changes decisions by:** must-pass regression cases block release on their own.
- **Practise:** Lesson 7, Exercises 8, 9, and 16. `add-case`, `compare`.
