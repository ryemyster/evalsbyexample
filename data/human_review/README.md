# Human review scorecards (ILLUSTRATIVE)

The two CSV files here are **invented for teaching**. "reviewer-a" and "reviewer-b" are fictional support experts; their ratings were written to show what a scorecard, a disagreement, and a stale review look like. They are not evidence about any real assistant.

Each row rates one `candidate-v2` draft from case set 1.0. The `draft_fingerprint` column ties the rating to the exact draft. If you change candidate-v2 so a draft changes, that rating is marked stale and the human-review gate goes back to pending.

Columns and allowed values are documented in `docs/grading.md`. To try it yourself:

```bash
python3 -m returns_eval review-sheet latest:candidate-v2 --reviewer your-name
```
