"""Exercise 13 (Part 2, Module 3): diagnose a judge, then fix its prompt.

The team wrote a judge prompt in a hurry: exercises/ex13_judge_prompt.txt. Your
job: find out how the SIMULATED judges misbehave, decide what that means for
using them, and fix the prompt. Full card: exercises/README.md, Exercise 13.

    python3 -m returns_eval bias-check judge-a
    python3 -m returns_eval bias-check judge-b
    python3 -m returns_eval calibrate judge-a --prompt exercises/ex13_judge_prompt.txt
    python3 -m returns_eval bias-check judge-a --prompt exercises/ex13_judge_prompt.txt
    python3 -m exercises 13

Part 1: fix exercises/ex13_judge_prompt.txt until calibrate prints no "Prompt problem"
lines and bias-check shows no injection or format flips with it.

Part 2: your findings.
"""

FINDINGS = {
    # Which probes flipped at least one verdict for judge-a with the default prompt (data/judges/tone.v1.txt)?
    # Use the probe names: position, length, self-preference, wording, injection, repeat, format.
    "judge_a_biases": ["TODO"],
    # The drafts you need graded come from sim-model-a. Which judge would you trust more for them, and why?
    "judge_for_sim_model_drafts": "TODO",   # "judge-a" or "judge-b"
    "why_that_judge": "TODO",
    # How will you count a win when comparing two versions' replies pairwise?
    "pairwise_rule": "TODO",
}
