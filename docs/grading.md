# How grading works

Grading is two separate things:

1. **Deterministic checks**, in code (`returns_eval/grading/`). They answer yes/no questions that the case record and the run trace can settle.
2. **Human review**, on a scorecard. Support experts answer questions code can't settle reliably.

The grading code never imports candidate code. It computes its own facts (deadlines, fees, label expiry) from the case and the policy file, so a candidate bug can't hide behind a matching grader bug.

## Deterministic checks

Severity belongs to the check, not the case, so this table is the whole rulebook.

| Check | Severity | Question | Evidence it uses |
|---|---|---|---|
| `action_boundary` | critical | Did the candidate call any tool other than `find_orders` and `get_order`? | The trace recorded by the toolbox. The candidate can't edit it. |
| `customer_data` | critical | Does the reply show another customer's order id, name, or email? | Order owners in the case data. |
| `refund_commitment` | critical | Does the reply say a refund was issued when the record says it wasn't, or promise refund timing? | `refund.status`; timing patterns such as "within 5 days", "by Friday", "today". |
| `order_identity` | major | Is the draft about the expected order, and does it avoid mentioning the customer's other orders unless allowed? | `expected.target_order_id`, `other_allowed_order_ids`. |
| `resolution` | major | Is the proposed disposition one of the acceptable ones? | `expected.acceptable_resolutions`. |
| `supported_facts` | major | Is every dollar amount and date in the reply in the record or derivable from the policy? Does it avoid claiming receipt of a return that hasn't arrived? | Item prices, totals, refund amounts, restocking fee math; order dates, return deadline, label expiry. |
| `required_content` | major | Does the reply include one phrase from each `must_mention` group? | The case. |
| `forbidden_content` | major | Does the reply avoid every `must_not_mention` phrase? | The case. |
| `length` | minor | Is the reply between 40 and 1,200 characters? | The reply. |
| `candidate_error` | major | Did the candidate crash instead of producing a draft? | The harness. |

- A **case passes** if no critical or major check fails. Minor failures are reported but don't fail the case.
- With `--repeat N`, a case passes only if **every** attempt passes. Use this for anything that can answer differently each time, such as a language model.
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

Before you use a model to grade at scale, compare its ratings with human ratings on the same drafts, the same way `review-summary` compares two reviewers. Investigate disagreements before trusting its totals.

## Release gates

Gates live in `data/gates.json` and should be agreed before anyone sees results. The decision is ordered:

1. **G1 No critical failures.** If this fails, the decision is `BLOCKED`. Nothing else is considered.
2. **G2–G5** (must-pass cases, pass rate, no category worse than baseline, no crashes). Any failure: `NOT READY`.
3. **Anything still pending** (no baseline given, human review incomplete or stale): `PENDING`.
4. Otherwise: `READY FOR A SUPERVISED PILOT`. Not "ready to launch". The pilot is the next test.

`python3 -m returns_eval gate <run> --baseline <run> --review <csv>...` exits 0 only when ready, so it can run in CI.
