# Human labels for tone (ILLUSTRATIVE)

Everything here is **invented for teaching**. "annotator-a" and "annotator-b" are fictional support leads. The drafts were written for the course (some by the course's scripted candidates, some by hand) and labeled by the course author applying the tone rubric in `data/rubrics/draft-quality.v1.json`. The same author also wrote the simulated judges, so the labels and judges aren't independent the way two separate teams would be. With a real system, labels come from domain experts who never see a judge's output.

| File | What it is |
|---|---|
| `tone.ILLUSTRATIVE.jsonl` | 64 drafts, one per line, each labeled "ok" or "problem" for tone by two annotators: first with the team's vague first rubric, then with the clear one |
| `manifest.json` | Version, rubric versions, what each split is for, and a changelog |

## Fields

| Field | Meaning |
|---|---|
| `item_id` | `L-001` to `L-064` |
| `split` | `train` (examples you may show a judge), `calibration` (tune and decide here), or `holdout` (use once, at the end) |
| `case_id` | The case the draft answers. Splits are by case, so near-identical drafts never land in two splits. |
| `segment` | The draft's next step (`accept_return`, `decline_return`, `escalate`, `inform`, `ask_customer`). Tone problems aren't spread evenly across them. |
| `source`, `family` | Who wrote the draft. `family` is `sim` for drafts from the simulated model family, which matters for self-preference. |
| `reply_text` | The draft |
| `first_rubric_labels` | Each annotator's label under the first rubric (0.1) |
| `labels` | Each annotator's label under the clear rubric (1.0) |
| `final` | The label used as the answer key: the annotators' shared label, or the settled one when they disagreed |
| `note` | Why, for settled disagreements and tricky drafts |

Check the dataset with `python3 -m returns_eval labels`. It reports agreement beyond chance and checks the splits for leakage and the judge prompts for contamination. When the rubric changes, relabel: labels made under an old rubric don't measure the same thing.
