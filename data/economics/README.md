# Costs and prices (ILLUSTRATIVE)

Every number here is **made up**, so you can practise budgeting an evaluation offline. Replace them with your own before using the method for a real decision.

| File | What it holds |
|---|---|
| `prices.ILLUSTRATIVE.json` | Made-up per-token prices for the SIMULATED models and judges. Reports use them to estimate cost. For a real model, copy the file, put in your provider's current published prices, and set `EVALS_PRICES` to your copy. |
| `costs.ILLUSTRATIVE.json` | Weekly volume, share of each request segment, an assumed tone-problem rate per segment, the weekly budget, the team's limit on unseen problems, people's cost per minute, minutes per check, relabeling effort, and the cost of a rude reply reaching a customer |

`python3 -m returns_eval budget PLAN` combines these assumptions with the judge's error rates, which it measures fresh from the labeled drafts each time. Its report marks every number as measured or assumed.

The assumed problem rate is the weakest number here. The labeled drafts were chosen to include many problems, so their rate (21 of 64) says nothing about real traffic. Measure it with a random sample of real drafts.
