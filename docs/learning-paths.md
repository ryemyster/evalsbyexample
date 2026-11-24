# Learning paths

The same lessons and exercises serve different people. Pick a path; nothing is duplicated between them, they just take a different route. Lesson numbers refer to [TUTOR.md](../TUTOR.md) (Part 1, Lessons 1-9) and [TUTOR-PART2.md](../TUTOR-PART2.md) (Part 2, Lessons 10-15). With a coding agent, say which path you want; without one, the [README](../README.md) has every command.

## Beginner (students, curious people, anyone new to this): about 1 hour

The goal is the core idea: an eval is test situations, checks that grade each answer, and a rule that one serious mistake outweighs a good average; and a second AI marking the first one's work needs checking too.

1. Part 1 quick tour: Lessons 1-3 and "Your turn: break it" (no exercises).
2. Lesson 10, first half: one run of a model is one roll of the dice (`variance`).
3. Lesson 12, first half: a judge catches the rude assistant (`judge judge-a --run latest:sound-annoyed`), and can be fooled (`bias-check judge-a`).
4. Wrap-up from Part 1.

## Product managers: about 3 to 4 hours, over two or three sessions

The goal is owning the decision: what to measure, what blocks release, what evidence is enough, what it costs, and when to roll back.

1. Part 1 quick tour, then the final challenge (candidate-v4).
2. Lessons 10, 11, 13, 14, and 15, with Exercises 10, 14, 15, and 16. You make every call; your agent writes the code.
3. The Part 2 capstone (Exercise 17), scored with the [checklist](check-yourself.md#part-2-capstone).
4. Read the [PM guide](pm-guide.md), especially decision rights, and [techniques.md](techniques.md).

## Engineers: about 3 hours

The goal is building it right: grader independence, structured outputs, seeded reproducibility, statistics, judge prompts, calibration, and traces.

1. Skim Part 1's README walkthrough; do Exercises 3, 6, and 9.
2. All of Part 2, Exercises 10-16, writing the code yourself.
3. Read `returns_eval/grading/output_format.py`, `returns_eval/judging/`, `returns_eval/variance.py`, and `returns_eval/production.py`.
4. Bring a real model and a real judge ([extending.md](extending.md#bring-your-own-model), [add a judge](extending.md#add-a-judge)): calibrate your judge on the calibration split before running anything else.

## Advanced practitioners: about 2 hours plus your own data

The goal is applying the method to your own system and knowing where it's thin.

1. Lessons 12-15 and the capstone, quickly.
2. Read [sources.md](sources.md), especially the "Disputed or unsettled" list, and the limitations in [design/extended-curriculum.md](design/extended-curriculum.md#7-changed-files-test-results-and-limitations).
3. Replace the illustrative data with yours: your own labeled drafts (split by case or by conversation, never by item), your prices and volumes, your traces, your rollback triggers. Keep thresholds in files agreed before you look.
4. Extend: a weighted kappa for ordinal labels, a cascade of judges, prediction-powered estimates from a small labeled sample plus many judge verdicts. None of these are built in.
