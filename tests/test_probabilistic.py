"""Part 2, Module 1: statistics, simulated models, structured output, and the variance report."""

import json
import unittest

from returns_eval import stats
from returns_eval.candidates import load_candidate
from returns_eval.candidates.simulated import SimModelA
from returns_eval.cases import subset
from returns_eval.grading import grade_case
from returns_eval.grading.output_format import output_problems
from returns_eval.harness import produce, run_eval
from returns_eval.variance import criticals, paired_difference, repeated_runs, report_lines, verdict

from .helpers import CASES, CORE


class TestStats(unittest.TestCase):
    def test_wilson(self):
        lo, hi = stats.wilson(5, 10)
        self.assertAlmostEqual(lo, 0.2366, places=3)
        self.assertAlmostEqual(hi, 0.7634, places=3)
        self.assertEqual(stats.wilson(0, 0), (0.0, 1.0))
        self.assertEqual(stats.wilson(0, 10)[0], 0.0)
        self.assertTrue(stats.frac_range(9, 20).startswith("9 / 20 (45%, likely "))

    def test_kappa(self):
        self.assertAlmostEqual(stats.cohen_kappa([1, 1, 0, 0], [1, 0, 0, 0]), 0.5)
        self.assertEqual(stats.cohen_kappa(["ok"] * 5, ["ok"] * 5), None)  # no variation: undefined
        # High raw agreement on a rare label can still be no better than chance.
        a = ["ok"] * 18 + ["problem", "ok"]
        b = ["ok"] * 18 + ["ok", "problem"]
        self.assertEqual(sum(x == y for x, y in zip(a, b)), 18)
        self.assertLess(stats.cohen_kappa(a, b), 0.01)

    def test_confusion_and_rates(self):
        truth = ["problem", "problem", "ok", "ok", "ok"]
        verdicts = ["problem", "ok", "problem", "ok", "ok"]
        cm = stats.confusion(truth, verdicts, "problem")
        self.assertEqual(cm, {"tp": 1, "fn": 1, "fp": 1, "tn": 2})
        r = stats.rates(cm)
        self.assertEqual((r["precision"], r["recall"], r["accuracy"]), (0.5, 0.5, 0.6))
        self.assertIsNone(stats.rates({"tp": 0, "fn": 0, "fp": 0, "tn": 3})["recall"])

    def test_bootstrap_is_reproducible(self):
        values = [0.1, -0.2, 0.0, 0.3, 0.2, -0.1]
        self.assertEqual(stats.bootstrap_mean(values, seed=3), stats.bootstrap_mean(values, seed=3))


class TestSimulatedModels(unittest.TestCase):
    def test_same_seed_same_results_different_seed_different(self):
        def texts(seed):
            model = load_candidate("sim-model-a")
            model.seed = seed
            return [r["attempts"][0]["draft"]["reply_text"] for r in run_eval(model, CORE)["results"]]
        self.assertEqual(texts(1), texts(1))
        self.assertNotEqual(texts(1), texts(2))

    def test_repeats_vary_within_one_run(self):
        run = run_eval(load_candidate("sim-model-a"), subset(CORE, ["RC-021", "RC-022"]), repeat=10)
        self.assertTrue(any(not r["stable"] for r in run["results"]))

    def test_usage_and_meta_are_recorded_and_labeled(self):
        run = run_eval(load_candidate("candidate-v5"), subset(CORE, ["RC-001"]))
        usage = run["results"][0]["attempts"][0]["usage"]
        self.assertEqual(usage["source"], "simulated")
        self.assertGreater(usage["input_tokens"], 100)
        self.assertEqual((run["meta"]["simulated"], run["meta"]["seed"]), (True, 1))
        scripted = run_eval(load_candidate("candidate-v2"), subset(CORE, ["RC-001"]))
        self.assertNotIn("usage", scripted["results"][0]["attempts"][0])
        self.assertNotIn("seed", scripted["meta"])

    def test_v5_timeout_on_long_messages(self):
        case = json.loads(json.dumps(CASES["RC-021"]))
        case["message"] = case["message"] + " " + "It has been a terrible week. " * 50
        attempt = produce(load_candidate("candidate-v5"), case)
        self.assertIsNone(attempt["draft"])
        self.assertIn("simulated: no reply within", attempt["error"])


class TestStructuredOutput(unittest.TestCase):
    def test_grader_validates_raw_output_itself(self):
        good = '```json\n{"resolution": "inform", "order_id": null, "reply_text": "Hi"}\n```'
        self.assertEqual(output_problems(good), [])
        self.assertIn("approve_return", output_problems('{"resolution": "approve_return", "order_id": null, "reply_text": "Hi"}')[0])
        self.assertTrue(output_problems("Sure! Here's my reply."))
        self.assertTrue(output_problems('{"resolution": "inform", "reply_text": ""}'))

    def test_bad_format_is_a_major_failure_even_though_the_adapter_repaired_it(self):
        class AlwaysBadFormat(SimModelA):
            name = "always-bad-format"
            chance = {**SimModelA.chance, "bad_format": 1.0, "skip_specialist": 0.0, "paraphrase": 0.0}

        result = grade_case(CASES["RC-021"], [produce(AlwaysBadFormat(), CASES["RC-021"])])
        self.assertEqual(result["attempts"][0]["draft"]["resolution"], "escalate", "the adapter turned 'transfer' into escalate")
        self.assertIn("structured_output", result["failed_checks"])
        self.assertFalse(result["passed"])

    def test_scripted_candidates_have_no_structured_output_check(self):
        result = grade_case(CASES["RC-001"], [produce(load_candidate("candidate-v2"), CASES["RC-001"])])
        self.assertNotIn("structured_output", [c["check"] for c in result["attempts"][0]["checks"]])


class TestVariance(unittest.TestCase):
    """TUTOR-PART2.md and Exercise 10 rely on these exact stories."""

    @classmethod
    def setUpClass(cls):
        cls.a = repeated_runs("sim-model-a", CORE, 10)
        cls.b = repeated_runs("sim-model-b", CORE, 10)
        cls.c = repeated_runs("sim-model-c", CORE, 10)

    def test_one_run_says_b_is_better_but_ten_runs_cant_tell(self):
        score = lambda run: sum(r["passed"] for r in run["results"])  # noqa: E731
        self.assertEqual((score(self.a[0]), score(self.b[0])), (22, 24))
        self.assertEqual(verdict(paired_difference(self.a, self.b)), "can't tell")

    def test_prompt_3_is_a_real_improvement(self):
        self.assertEqual(verdict(paired_difference(self.a, self.c)), "better")

    def test_report_names_the_simulation_and_the_verdicts(self):
        text = "\n".join(report_lines({"sim-model-a": self.a, "sim-model-b": self.b, "sim-model-c": self.c}))
        for part in ("SIMULATED:", "lowest to highest", "The range includes 0", "The whole range is above 0"):
            self.assertIn(part, text)

    def test_v5_looks_perfect_once_but_not_over_ten_runs(self):
        v5 = repeated_runs("candidate-v5", CORE, 10)
        first = v5[0]["results"]
        self.assertEqual((sum(r["passed"] for r in first), len(first)), (26, 26))
        self.assertTrue(criticals(v5))

    def test_scripts_do_not_vary(self):
        runs = repeated_runs("candidate-v2", subset(CORE, ["RC-001", "RC-002"]), 3)
        self.assertEqual(len({json.dumps(r["results"][0]["attempts"][0]["draft"]) for r in runs}), 1)


if __name__ == "__main__":
    unittest.main()
