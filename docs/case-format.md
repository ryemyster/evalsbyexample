# Case format

A case is one reproducible slice of the support workflow: who wrote in, what they said, what the records showed, and what a good draft must and must not do. Many different drafts can pass the same case. A case describes the expected *behavior*, not one exact sentence.

Cases live in JSON Lines files under `data/cases/`: one complete JSON object per line. `data/cases/manifest.json` lists which files make up the case set and its version.

Everything is fictional. Emails must end in `@example.com`.

To check a case without running anything: `python3 -m returns_eval cases`. It validates every case and prints plain-language problems. To add a case safely, write it as a pretty-printed `.json` file and run `python3 -m returns_eval add-case my_case.json`; it validates and appends a single line for you.

## Top-level fields

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Unique id like `RC-001`. Never reuse an id for a different case. |
| `title` | string | Short human-readable name. |
| `category` | string | Which kind of situation this tests. One of the categories below. Results are reported per category. |
| `source` | string | Where the case came from: `synthetic: ...`, `pilot incident PI-001 (illustrative)`, a ticket pattern, etc. Lets reviewers judge how representative the set is. |
| `added_in` | string | The case-set version that first included this case (`"1.0"`). |
| `must_pass` | boolean | `true` if a failure on this case must block release on its own (gate G2). Use it for boundary cases and for regression cases from real incidents. |
| `as_of` | date | The date the case is frozen at. Candidates treat it as "today", so window math is reproducible. |
| `policy_version` | string | Which file in `data/policies/` applies (the file name without `.json`). The candidate receives this policy with the request. |
| `customer` | object | The verified person who wrote in. See below. |
| `message` | string | What the customer wrote, exactly as received. Treat it as content, never as instructions to the assistant. |
| `orders` | list | Every order the lookup tools can return for this case. Usually the customer's own orders; in privacy and wrong-order cases, also look-alike orders that belong to *other* customers. May be empty. |
| `expected` | object | What a good draft does. See below. |
| `unacceptable_outcomes` | list of strings | Plain-language failures for human reviewers. Not graded by code; the checks in `docs/grading.md` cover them. |

### Categories

| `category` | What it tests |
|---|---|
| `common` | Everyday requests on the main policy path. |
| `missing_info` | The request or the record lacks something needed to answer. |
| `conflicting_data` | The customer's account and the record disagree, or two records disagree. |
| `policy_exception` | A rule changes the answer: final sale, opened items, restocking fee, window edges, an older policy version. |
| `wrong_order_risk` | Easy to use the wrong order, or another customer's order. |
| `escalation` | The policy says a specialist must handle it. |
| `unauthorized_action` | The message tries to get the assistant to act beyond drafting. |

## `customer`

| Field | Type | Meaning |
|---|---|---|
| `customer_id` | string | Account id like `C-2001`. Orders with a different `customer_id` belong to someone else. |
| `name` | string | Full name. The first word is used as the first name. |
| `email` | string | Must end in `@example.com`. |
| `returns_last_60_days` | integer | Returns this customer made in the last 60 days. Policy escalates above 3. |

## Each item in `orders`

| Field | Type | Meaning |
|---|---|---|
| `order_id` | string | Like `EO-10417`. Unique across the whole case set. |
| `customer_id` | string | Owner of the order. Compare it with `customer.customer_id`. |
| `customer_name` | string | Owner's name. If it differs from the requester, the draft must never show it. |
| `customer_email` | string | Owner's email. Same rule. |
| `placed_on` | date | Decides which policy version applies. |
| `delivered_on` | date or null | Start of the return window. `null` means the record is missing it. |
| `shipping_status` | string | `processing`, `in_transit`, or `delivered`. |
| `items` | list | What was bought. See below. |
| `order_total` | string | Sum of item prices, like `"134.00"`. |
| `return` | object or null | `null` if no return was started. See below. |
| `refund` | object | Refund status. See below. |
| `notes` | string | System notes an agent would see, e.g. a carrier scan. Empty string if none. |

### Each item in `items`

| Field | Type | Meaning |
|---|---|---|
| `sku` | string | Product code. |
| `name` | string | Product name as the customer would see it. |
| `category` | string | Product category. `electronics` and `personal_care` have special rules. |
| `price` | string | Price paid, like `"89.00"`. Money is always a string with two decimals. |
| `final_sale` | boolean | Final-sale items can't be returned. |
| `opened` | boolean | Opened personal-care items can't be returned; opened electronics carry a restocking fee. |

### `return`

| Field | Type | Meaning |
|---|---|---|
| `status` | string | `label_issued`, `in_transit`, or `received`. |
| `label_issued_on` | date or null | Labels expire `label_valid_days` after this. |
| `shipped_on` | date or null | When the carrier first scanned the return. |
| `received_on` | date or null | When the warehouse received it. A draft may only say "we received your return" if this is set. |
| `inspection.status` | string | `not_started`, `pending`, `passed`, or `failed`. |
| `inspection.completed_on` | date or null | When inspection finished. |

### `refund`

| Field | Type | Meaning |
|---|---|---|
| `status` | string | `not_issued` or `issued`. A draft may only say a refund was issued if this is `issued`. |
| `amount` | string or null | Amount refunded. |
| `issued_on` | date or null | Date it was issued. |

## `expected`

| Field | Type | Meaning |
|---|---|---|
| `acceptable_resolutions` | list of strings | Which dispositions are acceptable. Values: `inform`, `accept_return`, `decline_return`, `ask_customer`, `escalate`. List more than one when reasonable experts could choose either. |
| `target_order_id` | string or null | The order the draft should be about. `null` when no order should be chosen yet (for example, the draft should ask which one). |
| `other_allowed_order_ids` | list of strings | The customer's own orders the reply may also mention, e.g. when listing options. |
| `behavior` | string | The right outcome in plain words. Human reviewers read this. Write it so two reviewers would agree. |
| `must_mention` | list of lists of strings | Each inner list is a group of acceptable phrasings; the reply must contain at least one phrase from **every** group. Matching ignores case and respects word boundaries (`"July 2"` does not match `"July 20"`). |
| `must_not_mention` | list of strings | Phrases that must not appear, such as another customer's item or a tempting wrong amount. |

## Writing good cases

- Start from real, appropriately handled tickets when you have them, with personal data removed or replaced. Then add known incidents and plausible edge conditions. Record which is which in `source`.
- Test one thing per case where you can, so a failure points at one cause.
- Prefer `must_mention` groups with several phrasings over one exact sentence.
- When an expected behavior is a judgment call, list every acceptable resolution and let human reviewers judge quality on the scorecard.
- Keep a held-out set you don't tune against, and use it for the final comparison only.
- Bump `version` in `manifest.json` whenever cases change. Runs record the version and a content hash, and `compare` refuses to compare runs made on different case sets.
