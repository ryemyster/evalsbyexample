"""Reference solution for Exercise 13."""

FINDINGS = {
    "judge_a_biases": ["position", "length", "self-preference", "wording", "repeat"],
    "judge_for_sim_model_drafts": "judge-b",
    "why_that_judge": ("judge-a is from the same family as sim-model-a and passed every problem reply once the family's "
                       "sign-off was added. judge-b is from a different family and didn't move."),
    "pairwise_rule": "Ask both orders and count a win only when both orders pick the same reply; otherwise call it a tie.",
}
