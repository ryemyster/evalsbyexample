# Check yourself: the final challenge

You've watched the course test an AI assistant. Now you do it on your own.

## The challenge

The team built a new version, **candidate-v4**. Customers were waiting too long for a specialist, so v4 answers more requests itself. The team lead wants to switch it on next week.

You're the tester. **Should it go out?**

Your coding agent runs any command you ask for, but it won't tell you where to look. Ask in plain words, for example:

- "Run the tests on candidate-v4."
- "Compare v4 with v2 and the old approach."
- "Show me case RC-007 in full."

When you're ready, write down three things:

1. **Your call:** switch it on, don't, or try it carefully first.
2. **Your reason**, pointing at something you saw: a case, a number, or a check.
3. **What should happen next.**

## The checklist

After you've made your call, go through this list with your agent. Each item is something you either did or didn't do, with no partial credit. Be honest: nobody else sees this unless you share it.

You'll notice this is graded the same way the course grades the AI: a list of checks, and two of them are **must-pass**. Get those wrong and the rest doesn't save you.

| # | Did you... | Must pass? |
|---|---|---|
| 1 | Look past the overall score, instead of stopping there? | |
| 2 | Check whether any mistake was serious (critical)? | |
| 3 | Find the draft that would have hurt a customer, and read what it actually said? | yes |
| 4 | Look at results by type of request, or compare v4 with another version? | |
| 5 | Make the right call? | yes |
| 6 | Give a reason that points at evidence (a case, a number, a check), not just a feeling? | |
| 7 | Say what should happen next? | |
| bonus | Spot the second, quieter problem? | |

**How did you do?**

- **Both must-pass items, and 4 or more of the rest:** you can do this. You tested an AI the way a careful team would.
- **Missed a must-pass item:** that's useful to know, and it's exactly the mistake the course is about. Ask your agent to show you the case you missed, then try the challenge again in a week.

## Make it stick

Before you close the session, answer these in your own words. Your agent saves them in `playground/my_notes.md`, which is yours to keep.

- What would you check before trusting an AI feature?
- What did you get wrong at first, and what changed your mind?
- Where else could you use this? Think of an AI tool you use, at school or work or anywhere else.

Come back in a week and try answering the first question without looking. If you can, it stuck.

## Part 2 capstone

The Part 2 capstone ([TUTOR-PART2.md](../TUTOR-PART2.md#capstone-candidate-v5-exercise-17)) asks whether candidate-v5 should ship, hold, or roll back. `python3 -m exercises 17` checks that your decision record is complete and points at evidence that exists. This checklist scores the reasoning. Go through it with your agent after you've written your decision; each item is yes or no.

| # | Did you... | Must pass? |
|---|---|---|
| 1 | Write requirements before looking at v5's results, including one about operations (time, cost, or getting a draft at all)? | |
| 2 | Compare v5 with the version in use (v2), on the same cases, including RC-027? | |
| 3 | Run v5 more than once, and say whether its advantage is bigger than run-to-run noise? | |
| 4 | Find the critical failure that a single run can miss, and name the cases? | yes |
| 5 | Check the labels' agreement before relying on a judge measured against them? | |
| 6 | Notice that a judge from v5's own family can't be trusted to compare v5 with v2, or ask the comparison in both orders? | |
| 7 | Use the canary traces, and find the tickets that needed a specialist and didn't reach one? | yes |
| 8 | Attribute that failure to the right layers (the model timed out, and the fallback dropped the escalation)? | |
| 9 | Act on the rollback trigger agreed in advance, or say who agreed to override it and why? | yes |
| 10 | Say how drafts would be checked after launch, what it costs, and what would trigger a rollback? | |
| 11 | Name what would change your mind, and who does what next? | |
| 12 | Keep simulated and illustrative evidence labeled as such, instead of presenting it as real results? | |

**How did you do?** All three must-pass items and at least 6 of the rest: you can run an evaluation of a real model, not just read a score. Missed a must-pass item? Ask your agent to show you the evidence you skipped (`variance`, or `traces --trace T-203`), then write down what you'd look at first next time.

## Share your result (optional)

The course author would love to know how it went. On the course's GitHub page, open a new issue and pick **My final challenge result**. Share your checklist and anything that was confusing. Leave out your name, email, and anything else personal.
