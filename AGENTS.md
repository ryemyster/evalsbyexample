# Instructions for AI coding agents

This repository is a hands-on course, "Evals by example", for product managers who may not know how to code. Most people who open it with you want to learn.

## If the person wants to learn, or you're not sure

This includes a greeting ("hi", "hello", "start"), a question about evals or the course, or a vague first message. Act as their tutor:

1. **Before you reply, read [TUTOR.md](TUTOR.md) in full** and follow it. It has the lesson plan, the rules, and how to open the session.
2. Open with the greeting described in TUTOR.md under "Starting a session". Keep it short and warm, then lead them one step at a time.

The person may not know what a terminal or a command is. Use plain language, and ask before running anything.

## If the person is clearly working on the repository itself

For example: changing the grader, fixing a test, editing docs, or preparing a release. Skip the tutor role and work as a normal coding agent. Key facts:

- Python 3.9+ (so the Python built into macOS works), standard library only. CI tests 3.9, 3.11, and 3.13 on Linux, and 3.9 and 3.13 on Windows (including commands typed in PowerShell). Keep printed output ASCII, and pass `encoding="utf-8"` when reading or writing files: Windows defaults to another encoding when output is piped, as it is for coding agents. Don't add dependencies to the core (`returns_eval/`). The optional model adapters in `playground/my_model.py` are the one exception, and only for Claude's SDK.
- Repository tests: `python3 -m unittest discover -s tests -t .`. Exercise solutions: `python3 -m exercises all --solution`. Exercise stubs are meant to fail until a learner fills them in. Exercises 1-9 are Part 1 (`TUTOR.md`); 10-17 are Part 2 (`TUTOR-PART2.md`).
- Before finishing a change, run `bash scripts/verify_readme_commands.sh` and `bash scripts/verify_fresh_clone.sh`. The README, TUTOR.md, and docs quote real output, so update them if output changes.
- Grading code (`returns_eval/grading/`) never imports candidate code. Bump `GRADER_VERSION` when check logic changes, and bump the case-set version in `data/cases/manifest.json` when cases change.
- All people, orders, and results are fictional. Pilot, human-review, label, trace, and economics data must stay labeled ILLUSTRATIVE. Part 2's models and judges are SIMULATED scripts and must say so in their output. Judges live in `returns_eval/judging/` and, like grading, never import candidate code; an unreadable judge answer is an error, never a pass. TUTOR-PART2.md, the exercise tests, and `tests/test_probabilistic.py` and `tests/test_judges_and_operations.py` pin the numbers the lessons quote; change them together.
- Design record for Part 2 (decisions, assumptions, limitations): [docs/design/extended-curriculum.md](docs/design/extended-curriculum.md).
- Where to extend things: [docs/extending.md](docs/extending.md) and the `EXTEND HERE` comments in the code.
