# Production traces (ILLUSTRATIVE)

Everything here is **invented for teaching**. It is not from a real system, a real store, or real customers.

| File | What it pretends to be |
|---|---|
| `traces.ILLUSTRATIVE.jsonl` | One week (2026-09-14 to 2026-09-20) of request traces: 24 tickets on candidate-v2 in production, and 12 on candidate-v5 in a canary (a small share of real tickets on the new version) |
| `rollback_triggers.json` | Triggers agreed before the canary started: what to measure, the line that trips it, and the action |

## A trace

| Field | Meaning |
|---|---|
| `trace_id`, `ticket_id`, `date` | Which request |
| `deployment` | `production` or `canary` |
| `candidate`, `candidate_version` | Which version drafted it |
| `request_type`, `message_chars` | What kind of request, and how long the customer's message was |
| `order_placed_on` | Decides which policy version applies |
| `needed_specialist` | Whether, looking back, the request needed a specialist |
| `steps` | Each step in order: `lookup`, `load_policy`, `draft` (status, time, tokens, next step, failed checks), `judge` (status, verdict, and what the pipeline recorded), `route` (queue), `human_review` (action, seconds), `send` (ticket) |
| `outcome` | Whether the customer wrote back within 7 days |
| `note` | Context an investigator would find |

Run `python3 -m returns_eval traces` for the summary and `python3 -m returns_eval traces --trace T-105` for one trace. The trajectory checks are computed from these fields; the policy check works out which policy applies from the policy files themselves.

## What this data cannot tell you

- 36 traces can't show how often anything happens at scale.
- The canary got whatever tickets came in, not a matched sample, so compare like with like (request type, message length).
- `needed_specialist` is hindsight. In a real system it comes from later review, and some cases are never labeled.
