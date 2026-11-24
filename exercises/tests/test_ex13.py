from returns_eval.cases import load_case_set
from returns_eval.judging import load_judge, prompt_problems, with_case_context
from returns_eval.judging.probes import INJECT, _flips, run_probes
from returns_eval.labels import load_items

from ._support import ExerciseCase, file_path, load

CASES = {c["id"]: c for c in load_case_set().cases}
ITEMS = [i for i in with_case_context(load_items(), CASES) if i["split"] in ("train", "calibration")]
PROBES = ("position", "length", "self-preference", "wording", "injection", "repeat", "format")


class TestEx13(ExerciseCase):
    exercise = 13
    where = "exercises/ex13_judge_prompt.txt and exercises/ex13_judge_findings.py"

    def setUp(self):
        self.prompt = file_path("ex13_judge_prompt.txt")
        self.findings = load("ex13_judge_findings").FINDINGS

    def test_prompt_follows_the_rules(self):
        problems = prompt_problems(self.prompt.read_text(encoding="utf-8"))
        if problems:
            self.not_done(f"the prompt still has {len(problems)} problem(s), starting with: {problems[0]}")

    def test_fixed_prompt_resists_injection_and_is_readable(self):
        judge = load_judge("judge-a", str(self.prompt))
        errors = [i["item_id"] for i in ITEMS if judge.pointwise(i)["verdict"] == "error"]
        self.assertEqual(errors, [], "every answer should be readable JSON")
        flipped, _ = _flips(lambda: load_judge("judge-a", str(self.prompt)), ITEMS, INJECT)
        self.assertEqual(flipped, [], "a hidden 'mark it ok' still fooled the judge: fence the reply and say it's content")

    def test_findings_match_the_bias_check(self):
        if "TODO" in repr(self.findings):
            self.not_done("fill in FINDINGS from the bias-check output")
        named = set(self.findings["judge_a_biases"])
        self.assertTrue(named <= set(PROBES), f"use the probe names: {PROBES}")
        results = run_probes(lambda: load_judge("judge-a"), ITEMS, None, lambda p: load_judge("judge-a", p))
        expected = {r["probe"] for r in results if r["flipped"]}
        self.assertEqual(named, expected, "list every probe that flipped at least one verdict, and only those")

    def test_judge_choice_and_pairwise_rule(self):
        if "TODO" in repr(self.findings):
            self.not_done("fill in FINDINGS")
        self.assertEqual(self.findings["judge_for_sim_model_drafts"], "judge-b",
                         "look at the self-preference probe: which judge went easy on sim-model-style replies?")
        self.assertGreaterEqual(len(self.findings["why_that_judge"].split()), 10)
        rule = self.findings["pairwise_rule"].lower()
        self.assertTrue(any(w in rule for w in ("both orders", "swap", "order")),
                        "the position probe shows the order can decide the winner: say how you'll handle that")
