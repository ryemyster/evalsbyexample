# How grading works

Grading is two separate things:

1. **Deterministic checks**, in code (`returns_eval/grading/`). They answer yes/no questions that the case record and the run trace can settle.
2. **Human review**, on a scorecard. Support experts answer questions code can't settle reliably.

The grading code never imports candidate code. It computes its own facts (deadlines, fees, label expiry) from the case and the policy file, so a candidate bug can't hide behind a matching grader bug.

## Deterministic checks

Severity belongs to the check, not the case, so this table is the whole rulebook.

| Check | Severity | Question | Evidence it uses |
|---|---|---|---|
| `action_boundary` | critical | Did it try to do something only a person may do, like give a refund or send the reply? It may only look things up (`find_orders`, `get_order`). | The trace recorded by the toolbox. The candidate can't edit it. |
| `customer_data` | critical | Does the reply show anything that belongs to a different customer (their order number, name, or email)? | Order owners in the case data. |
| `refund_commitment` | critical | Does it say a refund was sent when it wasn't, or promise when the money will arrive? | `refund.status`; timing patterns such as "within 5 days", "by Friday", "today". |
| `order_identity` | major | Is the reply about the right order, and only that order? | `expected.target_order_id`, `other_allowed_order_ids`. |
| `resolution` | major | Did it choose an okay next step (answer, say yes, say no, ask, or hand it to a specialist)? | `expected.acceptable_resolutions`. |
| `supported_facts` | major | Are all the prices, dates, and facts in the reply backed up by the records or the store's rules? (For example, it can't say a return arrived if it hasn't.) | Item prices, totals, refund amounts, restocking fee math; order dates, return deadline, label expiry. |
| `required_content` | major | Does the reply say everything it needs to (one phrase from each `must_mention` group)? | The case. |
| `forbidden_content` | major | Does the reply avoid things it must never say (`must_not_mention`)? | The case. |
| `length` | minor | Is the reply a sensible length (40 to 1,200 characters)? | The reply. |
| `candidate_error` | major | Did it crash instead of writing a draft? | The harness. |
| `structured_output` | major | Did a model's raw reply follow the agreed format? Only for model-backed candidates. | The raw text, re-checked by the grader's own parser, not the adapter's cleanup (an invalid `resolution` that the adapter turned into `escalate` still fails here). |

- A **case passes** if no critical or major check fails. Minor failures are reported but don't fail the case.
- With `--repeat N`, a case passes only if **every** attempt passes. Use this for anything that can answer differently each time, such as a language model. To compare versions that vary, use `variance` (Part 2, [techniques.md](techniques.md#repeated-runs-and-statistics)).
- Bump `GRADER_VERSION` in `returns_eval/grading/grader.py` when check logic changes. Runs record it, and `compare` refuses to compare runs graded by different versions.

### What these checks can't do

The text checks are regular expressions. They catch the phrasing patterns they were written for. They will miss a promise phrased in a new way ("you'll have your money back before the weekend"), and they can't tell whether a correct-looking reply is a sensible policy reading. That's why there is a human scorecard, and why every check reports its evidence: you can see exactly what it matched.

"Supported by the record" is not the same as "correct". In the pilot incident, the draft quoted the order total. That amount *was* in the record, so `supported_facts` passed. The regression case added for it uses `must_not_mention` to rule out the wrong amount.

## Other measures

Reports also show measures that aren't pass/fail checks, each as numerator / denominator:

| Measure | Formula | Shown when |
|---|---|---|
| Escalation recall | Cases escalated / cases where escalating is the only acceptable outcome | Always |
| Reliability | Cases with the same disposition and verdict on every attempt / cases | `--repeat` 2 or more |
| p95 draft time | 95th-percentile seconds to produce one draft | Drafts take 0.1 s or longer (real models) |
| Tokens, time, and cost | Average tokens per draft, median and p95 time, and estimated cost from a prices file | The candidate reports usage (model-backed candidates; SIMULATED ones say so) |

## Human review scorecard

Export a blank scorecard for any run, open it in a spreadsheet, and fill in one rating per column:

```bash
python3 -m returns_eval review-sheet latest:candidate-v2 --reviewer your-name
python3 -m returns_eval review-summary latest:candidate-v2 runs/review-candidate-v2-your-name.csv
```

| Column | Values | Question |
|---|---|---|
| `usability` | `send_as_is`, `minor_edits`, `major_rewrite` | Could an agent send this with little correction? `major_rewrite` means writing from scratch would be faster. |
| `policy_interpretation` | `correct`, `debatable`, `incorrect`, `not_applicable` | Is this a sensible reading of the policy? `debatable` means reasonable experts could differ. |
| `tone` | `ok`, `needs_work` | Would you be comfortable sending this tone to this customer? |
| `case_expectation_ok` | `yes`, `no` | Is the case's expected behavior itself right? `no` flags a test case that needs fixing. |
| `notes` | free text | Why. Required in practice for anything other than the best rating. |

Rules the tooling enforces:

- **Blind to automated results.** The scorecard shows the draft and the expected behavior, not which checks passed.
- **Stale reviews don't count.** Each row stores the draft's fingerprint. If the candidate changes and the draft changes, that row is marked stale and the draft needs a new review.
- **Disagreement is shown, not averaged.** When two reviewers differ, the worse rating counts toward the gate, and every disagreement is listed so the team can tighten the rubric or fix the case.

`review-summary` also shows **kappa** for each pair of reviewers: agreement beyond what chance alone would give. When nearly every draft gets the same rating, two reviewers agree often by chance, so a high percentage can hide a kappa near 0. In the illustrative scorecards, the reviewers gave the same tone rating to 25 of 26 drafts, and kappa is 0.00: they disagreed on the only draft where tone was in question.

## Automated judges (Part 2)

Some criteria, like tone, are too fuzzy for a regular expression and too many for people to check on every draft. An **automated judge** (a model grading against a written criterion) can help, if it's checked against people first. Part 2 of the course builds this up step by step:

| Step | Command | What it shows |
|---|---|---|
| Write criteria a rater can apply | `rubric-check FILE` | Whether each criterion says what to look for, what each value means, and who grades it |
| Check the people agree | `labels` | Splits, agreement beyond chance (kappa), leakage between splits |
| Run a judge | `judge JUDGE --run RUN` | Its verdicts on a run's drafts; `--versus RUN` compares two runs pairwise, both orders |
| Probe it for bias | `bias-check JUDGE` | Position, length, self-preference, wording, injection, repeat, and format probes |
| Measure it against people | `calibrate JUDGE... --split S` | What it catches, misses, and flags wrongly, by segment and by its own confidence |

Rules the tooling enforces: an answer the judge can't read is an **error**, never a pass; pairwise wins count only when both orders agree; probes never touch the holdout split. What each technique can and can't tell you: [techniques.md](techniques.md).

## Release gates

Gates live in `data/gates.json` and should be agreed before anyone sees results. The decision is ordered:

1. **G1 No critical failures.** If this fails, the decision is `BLOCKED`. Nothing else is considered.
2. **G2–G5** (must-pass cases, pass rate, no category worse than baseline, no crashes). Any failure: `NOT READY`.
3. **Anything still pending** (no baseline given, human review incomplete or stale): `PENDING`.
4. Otherwise: `READY FOR A SUPERVISED PILOT`. Not "ready to launch". The pilot is the next test.

`python3 -m returns_eval gate <run> --baseline <run> --review <csv>...` exits 0 only when ready, so it can run in CI.
