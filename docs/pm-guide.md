# Who owns what

A short guide for the product manager running an eval like this one. Adapt the names to your organization; the split of responsibilities is the point.

## What does the PM own?

The PM owns making the eval useful for a product decision.

- **The decision.** Write the yes/no question the eval informs. Here: *Should we offer the draft assistant to support agents handling return requests?*
- **The baseline.** Name how the job gets done today and make sure the comparison is against that, not against nothing.
- **What counts as unacceptable.** Decide, with support leadership, which failures are inconvenient and which block release. Write them down before results arrive.
- **Representative cases.** Secure real (de-identified) examples and domain reviewers' time. Make sure every category of risk has cases.
- **The release criteria.** Get the gates in `data/gates.json` agreed and signed off before the first run.
- **Reading failures.** Read failures by category and by case, not just the average. Open every critical failure yourself.
- **The call.** Decide whether to improve, narrow the scope, pilot, roll back, or stop.
- **Outcomes.** Check whether measured draft quality turns into faster handling and better resolution for customers.

## What does engineering own?

- The candidate: prompts, model, tools, permissions, and the code that produces drafts.
- The harness and deterministic checks, including keeping grading code separate from candidate code.
- Reproducibility: every run records the candidate version, case-set version and hash, grader version, and run time.
- Enforcing the action boundary in the system itself (permissions), not only in the eval. The eval proves the boundary holds on the cases; permissions make it hold everywhere.
- Running the full case set on every change, and the optional repeated runs for nondeterministic candidates.

## Who defines policy correctness?

The owner of the policy, usually support operations or the returns policy owner, not the PM and not engineering. They:

- confirm the expected behavior for every case that involves a policy judgment,
- settle `debatable` ratings from the scorecard (for example RC-017: decline, or escalate because of a skin reaction?),
- approve policy version changes, which then need new or updated cases.

When the written policy is ambiguous, fix the policy, not just the case.

## Who reviews failures?

| Failure | Reviewed by | Within |
|---|---|---|
| Any critical failure in an offline run | PM and engineering lead, together | Before the next run is used for any decision |
| Major failures | Engineering, with the PM reading the category summary | Before the next comparison |
| Scorecard disagreements and `debatable` ratings | Policy owner with the two reviewers | Before the human-review gate counts |
| Errors agents catch during a pilot | The agent logs it; PM triages; it becomes a regression case | Same week |

## What evidence is required before launch?

Before a **supervised pilot** (human approves every reply):

1. Zero critical failures on the full case set, including all regression cases.
2. Every must-pass case passes.
3. Pass rate at or above the agreed threshold, and no case category worse than the baseline.
4. A complete, current human review: every draft reviewed, reviewer disagreements discussed, no `incorrect` policy ratings.
5. The action boundary enforced by permissions in the product, not only observed in the eval.

Before **wider rollout**, add pilot evidence:

6. Handling time, rework, escalations, and repeat contacts compared with agents working without the tool, **within each request type**.
7. Every error agents caught during the pilot turned into a case, fixed, and the full set rerun.
8. A sample of approved drafts audited after the fact, because a high "used as-is" rate can hide errors agents didn't notice.

An offline eval can't prove that a rare, serious failure will never happen, and a few weeks of pilot data can't either. Size your rollout to what the evidence can support.

## What would trigger rollback?

Agree these before the pilot starts, as a measure, a threshold, and an action. The thresholds below are illustrative.

| Trigger | Measure and threshold | Action |
|---|---|---|
| Unauthorized action | Any refund, sent message, or order change by the assistant. Threshold: one. | Turn drafts off. Investigate permissions. |
| Another customer's data | Any exposure. Threshold: one. | Turn drafts off. |
| False refund commitment reaches a customer | Any. Threshold: one. | Stop. Review the case and the policy source. |
| Missed escalation | Escalation recall = correct escalations / required escalations. Below 100%. | Send that request type to people only. |
| Agent rework rises | Share of drafts edited heavily or discarded, above the manual baseline for two review periods. | Reduce traffic. Inspect prompt, model, and workflow. |
| Repeat contacts rise | Reopened within 7 days, above the manual group for the same request type. | Pause and investigate. |
| Model, prompt, or policy change | Drift = current eval results vs. the pinned baseline run. Any material regression. | Freeze expansion. Rerun every case. |

Rollback means turning the drafts off for agents, not just fixing forward. Keep the previous workflow available, keep the switch simple, and test it before the pilot.

Why this matters outside the lab: in *Moffatt v. Air Canada*, 2024 BCCRT 149, a British Columbia tribunal held Air Canada responsible for incorrect bereavement-fare information its website chatbot gave a customer, and ordered it to pay the difference. Customers treat an assistant's answer as the company's answer. That's why this course treats a false commitment as critical, and why a human approves every draft.

## Comparing models, and choosing a route

This section adapts the method in [Ascendvent](https://ascendvent.life)'s *A PM's Operating Guide to Comparing Models*: start from the product decision, segment the work by risk, screen candidates, choose measures and stop gates before the pilot, and present a decision the team can act on.

Once you can grade one candidate, you can grade several: the scripted ones in this course, or real models through `playground/my_model.py`. The question changes from "is this model good?" to "**which requests should go to which model, and which should stay with people?**"

**1. Build the pool, then screen it.** Start from models your company can actually buy, deploy, and govern. Before any testing, remove candidates that fail your data-residency or retention rules, can't support the tools you need, have no stable version you can pin, or can't meet your speed limit. Keep a candidate only if you can say what you expect it to do better. A small screen (for example `--only` on a handful of cases) removes poor fits before you spend more.

**2. Segment the work.** The case categories are segments with different consequences. Decide a route for each, based on the evidence, not the average:

| Request type | What goes wrong | A reasonable route |
|---|---|---|
| `common` | A wrong fact means rework and a bad promise | A faster, cheaper model, if it clears the quality gate |
| `missing_info`, `conflicting_data` | False confidence instead of asking or escalating | A stronger model, or a model that escalates when unsure |
| `policy_exception` | An unsupported policy claim becomes a concession | The model with the best results here, with human review |
| `wrong_order_risk` | Another customer's data, or the wrong order | Only a candidate with zero failures here; otherwise people |
| `escalation` | A missed escalation leaves the problem with the wrong person | Draft the handoff; a specialist decides |
| High-consequence decisions | The cost of one failure is unacceptable | People only |

`compare` shows results by request type for every candidate side by side; that table is your routing evidence. Routing in production needs something that recognizes the request type at runtime, and that classifier needs its own eval.

**3. Choose measures from the user's action and the cost of failure.** Write each as a formula with a numerator and a denominator:

| Measure | Formula | Where it comes from here |
|---|---|---|
| Correctness | Cases passed / cases | `run`, `compare` |
| Groundedness | Supported claims / claims | The `supported_facts` and `refund_commitment` checks |
| Escalation recall | Correct escalations / required escalations | "Other measures" in `run` and `compare`. Aim for 100%. |
| Reliability | Cases with the same result every attempt / cases | `run --repeat 3` |
| Speed | 95th-percentile seconds per draft | Shown for real models (`p95 draft time`) |
| Edit burden | Drafts edited heavily or discarded / drafts | Human review scorecard; pilot |
| Cost per completion | Total cost (model + review time) / completed tickets | Your provider's billing and the pilot |

Set the threshold for each before testing, and write down what happens when a route misses it: keep it, add a stronger model, or hand the request to a person.

**4. Pilot in stages, each with a gate.**

| Stage | Question | Gate to move on |
|---|---|---|
| Screen | Which candidates deserve more work? | Removes poor fits; a small sample is enough |
| Offline eval | Is each route correct and safe on known cases? | The release gates in `data/gates.json` |
| Shadow | How do routes behave on real requests, with nothing shown to agents? | Zero critical failures; escalation recall 100% |
| Assisted (supervised pilot) | Do drafts reduce agent work? | Rework and handling time better than the manual baseline, per request type |
| Limited launch | Does the product get better? | Every stop condition still holds |

Name the eval owner, policy owner, and rollback owner before the first stage, and rerun every case after any model, prompt, or policy-source change.

**5. Present the decision on one page.** `python3 -m returns_eval brief baseline candidate-v2 --review data/human_review/*.csv` writes a decision brief with the evidence, sample sizes, gates, and stop conditions filled in. You add the parts only you can write: why now, what you're asking the team to approve, and who owns what.
