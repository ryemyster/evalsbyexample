# Rubrics

A rubric is the written criteria that people, a judge, or code apply to every draft. Check one with `python3 -m returns_eval rubric-check FILE`.

| File | What it is |
|---|---|
| `draft-quality.v0.json` | The team's first rubric ("Is the reply helpful?"). It fails rubric-check. The first round of tone labels used it. |
| `draft-quality.v1.json` | The clear rubric. The second round of tone labels used it, and the judge prompts include its tone definition. |

## A criterion

| Field | Meaning |
|---|---|
| `id` | lowercase_with_underscores |
| `question` | One question, ending in "?", about something a rater can see |
| `scale` | `binary` (two values), `ordinal` (three or more ordered levels), or `continuous` (a measured number) |
| `values`, `definitions`, `examples` | For binary and ordinal: each value, what it means in observable terms, and an example reply |
| `unit`, `range`, `how_measured` | For continuous |
| `reference` | What the reply is compared with: `none` (reference-free), `expected_behavior`, `records`, or `policy` |
| `graded_by` | `code` (then `check` names the check), `judge`, or `human` |
| `evidence` | What the rater looks at |

When a rubric changes, bump its `version`, and relabel: labels made under another version don't measure the same thing.
