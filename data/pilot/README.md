# Pilot data (ILLUSTRATIVE)

Everything in this folder is **invented for teaching**. It is not from a real pilot, a real store, or real customers. The numbers were chosen to illustrate how pilot evidence differs from offline eval results, not to suggest what any real assistant would achieve.

| File | What it pretends to be |
|---|---|
| `pilot_tickets.ILLUSTRATIVE.csv` | 40 return tickets from a two-week supervised pilot (2026-08-24 to 2026-09-04). 20 handled by agents without the assistant (`manual`), 20 by agents reviewing `candidate-v2` drafts (`assisted`). A human approved every reply. |
| `incidents.ILLUSTRATIVE.jsonl` | One failure an agent caught during the pilot, which becomes regression case RC-027 in Exercise 8. |

## Columns in `pilot_tickets.ILLUSTRATIVE.csv`

| Column | Meaning |
|---|---|
| `ticket_id` | `M-` for manual, `A-` for assisted |
| `date` | Day the ticket was handled |
| `arm` | `manual` (today's workflow) or `assisted` (agent reviews a draft) |
| `request_type` | `refund_status`, `start_return`, `exchange`, `label`, `policy_question`, `escalation` |
| `handling_minutes` | Minutes from opening the ticket to sending the reply |
| `draft_outcome` | Assisted only: `used_as_is`, `edited`, or `discarded`. `n/a` for manual |
| `agent_caught_error` | Assisted only: an error the agent fixed before sending (`wrong_amount`, `wrong_tone`, ...) or `none` |
| `reopened_within_7_days` | `yes` if the customer wrote back about the same issue within 7 days |

Run `python3 -m returns_eval pilot` to see a summary, with every rate shown as numerator / denominator.

## What this data cannot tell you

- Tickets were not randomly assigned, and the request mix differs between arms. Compare within a request type, not just overall.
- 20 tickets per arm is far too few to detect a change in repeat contacts or to rule out rare, serious failures.
- Handling time was self-reported in this imagined pilot. In a real pilot, pull it from the helpdesk.
