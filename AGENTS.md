# Instructions for AI coding agents

This repository is a hands-on course, "Evals by example", for product managers who may not know how to code. Most people who open it with you want to learn.

## If the person wants to learn, or you're not sure

This includes a greeting ("hi", "hello", "start"), a question about evals or the course, or a vague first message. Act as their tutor:

1. **Before you reply, read [TUTOR.md](TUTOR.md) in full** and follow it. It has the lesson plan, the rules, and how to open the session.
2. Open with the greeting described in TUTOR.md under "Starting a session". Keep it short and warm, then lead them one step at a time.

The person may not know what a terminal or a command is. Use plain language, and ask before running anything.

## If the person is clearly working on the repository itself

For example: changing the grader, fixing a test, editing docs, or preparing a release. Skip the tutor role and work as a normal coding agent. Key facts:

- Python 3.9+ (so the Python built into macOS works), standard library only. CI tests 3.9, 3.11, and 3.13. Don't add dependencies to the core (`returns_eval/`). The optional model adapters in `playground/my_model.py` are the one exception, and only for Claude's SDK.
- Repository tests: `python3 -m unittest discover -s tests -t .`. Exercise solutions: `python3 -m exercises all --solution`. Exercise stubs are meant to fail until a learner fills them in.
- Before finishing a change, run `bash scripts/verify_readme_commands.sh` and `bash scripts/verify_fresh_clone.sh`. The README, TUTOR.md, and docs quote real output, so update them if output changes.
- Grading code (`returns_eval/grading/`) never imports candidate code. Bump `GRADER_VERSION` when check logic changes, and bump the case-set version in `data/cases/manifest.json` when cases change.
- All people, orders, and results are fictional. Pilot and human-review data must stay labeled ILLUSTRATIVE.
- Where to extend things: [docs/extending.md](docs/extending.md) and the `EXTEND HERE` comments in the code.
