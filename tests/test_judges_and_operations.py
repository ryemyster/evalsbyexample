"""Part 2, Modules 2-6: rubrics, labels, judges, calibration, economics, and production traces.

TUTOR-PART2.md, the exercises, and the docs quote several of these results; if one
changes on purpose, update them together.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from returns_eval import economics, labels, production, rubric
from returns_eval.cases import REPO_ROOT, load_case_set
from returns_eval.judging import LLMJudge, load_judge, prompt_problems, with_case_context
from returns_eval.judging.base import parse_verdict
from returns_eval.judging.calibration import judge_items, summarize
from .helpers import model_env
from returns_eval.judging.probes import INJECT, _flips, run_probes

CASES = {c["id"]: c for c in load_case_set().cases}
ITEMS = with_case_context(labels.load_items(), CASES)
TUNE = [i for i in ITEMS if i["split"] in ("train", "calibration")]
HOLDOUT = [i for i in ITEMS if i["split"] == "holdout"]


def cli(*args):
    proc = subprocess.run([sys.executable, "-m", "returns_eval", *args], cwd=REPO_ROOT, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


class TestRubricAndLabels(unittest.TestCase):
    def test_vague_rubric_fails_and_clear_rubric_passes(self):
        errors, _ = rubric.lint(rubric.load(REPO_ROOT / "data/rubrics/draft-quality.v0.json"))
        self.assertTrue(any('"helpful"' in e for e in errors))
        errors, _ = rubric.lint(rubric.load(REPO_ROOT / "data/rubrics/draft-quality.v1.json"))
        self.assertEqual(errors, [])

    def test_code_criteria_must_name_a_real_check(self):
        r = rubric.load(REPO_ROOT / "data/rubrics/draft-quality.v1.json")
        rubric.criterion(r, "grounded")["check"] = "made_up_check"
        self.assertTrue(any("existing check" in e for e in rubric.lint(r)[0]))

    def test_labels_split_by_case_with_no_leakage(self):
        text = "\n".join(labels.health(labels.load_items()))
        for part in ("ok: no case appears in two splits", "ok: no near-identical drafts",
                     "same label  50 / 64 (78%)   beyond chance (kappa) 0.46",
                     "same label  60 / 64 (94%)   beyond chance (kappa) 0.85"):
            self.assertIn(part, text)

    def test_contamination_is_detected(self):
        holdout = next(i for i in labels.load_items() if i["split"] == "holdout")
        with tempfile.TemporaryDirectory() as tmp:
            prompt = Path(tmp) / "leaky.txt"
            prompt.write_text("Example of a bad reply: " + holdout["reply_text"], encoding="utf-8")
            leaks = labels.prompt_contamination(labels.load_items(), [prompt])
        self.assertIn((holdout["item_id"], "leaky.txt"), leaks)
        self.assertEqual(labels.prompt_contamination(labels.load_items(), sorted((REPO_ROOT / "data/judges").glob("*.txt"))), [])


class TestJudges(unittest.TestCase):
    def test_unreadable_answers_are_errors_never_passes(self):
        self.assertEqual(parse_verdict("Looks fine to me!")["verdict"], "error")
        self.assertEqual(parse_verdict('{"verdict": "pass"}')["verdict"], "error")
        self.assertIsNone(parse_verdict('{"verdict": "ok", "confidence": 7}')["confidence"])

        class Broken(LLMJudge):
            name = "broken"

            def complete(self, prompt):
                raise TimeoutError("judge service timed out")

        s = summarize(HOLDOUT, judge_items(Broken(), HOLDOUT))
        self.assertEqual((s["errors"], s["agree"], s["cm"]["tn"]), (30, 0, 0))

    def test_prompt_rules(self):
        self.assertEqual(prompt_problems((REPO_ROOT / "data/judges/tone.v1.txt").read_text(encoding="utf-8")), [])
        self.assertEqual(prompt_problems((REPO_ROOT / "data/judges/pairwise-tone.v1.txt").read_text(encoding="utf-8"), "pairwise"), [])
        self.assertEqual(len(prompt_problems((REPO_ROOT / "exercises/ex13_judge_prompt.txt").read_text(encoding="utf-8"))), 6)

    def test_same_agreement_different_failures_on_holdout(self):
        a = summarize(HOLDOUT, judge_items(load_judge("judge-a"), HOLDOUT))
        b = summarize(HOLDOUT, judge_items(load_judge("judge-b"), HOLDOUT))
        self.assertEqual((a["agree"], b["agree"]), (24, 24))
        self.assertEqual((a["cm"]["tp"], a["cm"]["fn"], a["cm"]["fp"]), (3, 6, 0))
        self.assertEqual((b["cm"]["tp"], b["cm"]["fn"], b["cm"]["fp"]), (8, 1, 5))
        self.assertEqual((a["low"], b["low"]), ((0, 5), (0, 5)), "each judge's unsure verdicts are exactly its errors")

    def test_bias_probes(self):
        def probes(name, prompt=None):
            results = run_probes(lambda: load_judge(name, prompt), TUNE, prompt, lambda p: load_judge(name, p))
            return {r["probe"]: len(r["flipped"]) for r in results}

        a, b = probes("judge-a"), probes("judge-b")
        self.assertEqual((a["self-preference"], b["self-preference"]), (4, 0))
        self.assertGreater(a["length"], 0)
        self.assertEqual((a["injection"], a["format"], b["injection"]), (0, 0, 0))
        self.assertGreater(b["position"], 0)
        self.assertEqual(probes("judge-a", str(REPO_ROOT / "exercises/ex13_judge_prompt.txt"))["format"], len(TUNE))
        with tempfile.TemporaryDirectory() as tmp:
            unfenced = Path(tmp) / "unfenced.txt"
            unfenced.write_text('{criterion}\nReply: {reply}\nJSON: {"verdict": "ok" or "problem", "confidence": 0.5}', encoding="utf-8")
            flipped, of = _flips(lambda: load_judge("judge-a", str(unfenced)), TUNE, INJECT)
        self.assertEqual(len(flipped), of)

    def test_pairwise_counts_a_win_only_when_both_orders_agree(self):
        x, y = TUNE[0], TUNE[2]
        result = load_judge("judge-b").pairwise_both_orders({**x, "reply_text": "Hi, thanks."},
                                                            {**y, "reply_text": "Hi, thank you."})
        self.assertEqual((result["order_dependent"], result["winner"]), (True, "tie"))


class _Handler(BaseHTTPRequestHandler):
    reply = {}

    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        payload = json.dumps({"choices": [{"message": {"content": json.dumps(_Handler.reply)}}],
                              "usage": {"prompt_tokens": 321, "completion_tokens": 12}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


class TestLiveAdaptersOffline(unittest.TestCase):
    def setUp(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.url = f"http://127.0.0.1:{server.server_port}/v1"

    def test_provider_judge_round_trip(self):
        from playground.my_judge import OpenAICompatibleJudge

        _Handler.reply = {"verdict": "problem", "reason": "It says 'honestly'.", "confidence": 0.9}
        env = {"EVALS_JUDGE_MODEL": "judge-model", "EVALS_BASE_URL": self.url, "EVALS_API_KEY": "k"}
        with model_env(env):
            judge = OpenAICompatibleJudge()
            verdict = judge.pointwise(TUNE[1])
        self.assertEqual((verdict["verdict"], judge.version), ("problem", "judge-model"))
        self.assertEqual(judge.last_usage["input_tokens"], 321)

    def test_candidate_usage_is_recorded(self):
        from playground.my_model import OpenAICompatibleModel
        from returns_eval.harness import produce

        _Handler.reply = {"resolution": "inform", "order_id": "EO-10417",
                          "reply_text": "Hi Ana, we received your return on August 7, and it's waiting for inspection."}
        with model_env({"EVALS_MODEL": "m", "EVALS_BASE_URL": self.url, "EVALS_API_KEY": "k"}):
            attempt = produce(OpenAICompatibleModel(), CASES["RC-001"])
        self.assertEqual((attempt["usage"]["input_tokens"], attempt["usage"]["source"]), (321, "provider"))


class TestEconomics(unittest.TestCase):
    def test_reference_plans_and_the_solution(self):
        costs = economics.load_costs()
        everyone = economics.evaluate({"judge": None, "people_random_share": {s: 1.0 for s in costs["segment_share"]}},
                                      costs, None, None)
        nobody = economics.evaluate({"judge": None}, costs, None, None)
        self.assertEqual((round(everyone["eval_usd"], 2), round(everyone["totals"]["missed"], 1)), (750.0, 0.0))
        self.assertEqual(round(nobody["totals"]["missed"], 1), 46.6)
        plan = json.loads((REPO_ROOT / "solutions/ex15_eval_budget.json").read_text(encoding="utf-8"))
        rates, usage = economics.judge_rates(plan["judge"], plan["measured_on"], CASES, plan["people_check_unsure_below"])
        result = economics.evaluate(plan, costs, rates, usage)
        self.assertLessEqual(result["eval_usd"], costs["weekly_budget_usd"])
        self.assertLessEqual(result["totals"]["missed"], costs["team_max_missed_per_week"])

    def test_plan_problems(self):
        problems = economics.plan_problems({"code_checks_share": 0.5, "judge": "judge-z", "evidence": []}, {"calibrate"})
        self.assertEqual(len(problems), 5)


class TestProduction(unittest.TestCase):
    def setUp(self):
        self.traces = {t["trace_id"]: t for t in production.load_traces()}

    def test_policy_comes_from_the_policy_files(self):
        self.assertEqual(production.policy_for("2026-06-30"), "returns-2026-04")
        self.assertEqual(production.policy_for("2026-07-01"), "returns-2026-07")

    def test_each_symptom_is_found(self):
        expect = {"T-105": "right_ticket", "T-109": "right_policy", "T-112": "complete_record",
                  "T-115": "judge_errors_not_counted_as_pass", "T-120": "real_review", "T-124": "specialist_routed",
                  "T-203": "specialist_routed"}
        for tid, check in expect.items():
            self.assertIn(check, production.check_trace(self.traces[tid]), tid)
        self.assertEqual(production.check_trace(self.traces["T-122"]), {}, "the critical check blocked the draft: the system worked")

    def test_canary_triggers_rollback(self):
        fired = {t["id"] for t, _ in production.triggers_fired(list(self.traces.values()), "canary")}
        self.assertEqual(fired, {"R1", "R5"})


class TestPart2Commands(unittest.TestCase):
    def test_commands_run(self):
        for args, code, part in (
            (["variance", "sim-model-a", "sim-model-b", "--runs", "2", "--only", "RC-021", "RC-022"], 0, "Luck or a real"),
            (["rubric-check", "data/rubrics/draft-quality.v0.json"], 1, "Not ready"),
            (["rubric-check", "data/rubrics/draft-quality.v1.json"], 0, "Ready:"),
            (["labels"], 0, "beyond chance"),
            (["calibrate", "judge-a", "judge-b", "--split", "holdout"], 0, "24 / 30 (80%)"),
            (["bias-check", "judge-b"], 0, "self-preference"),
            (["budget", "solutions/ex15_eval_budget.json"], 0, "PLAN: WITHIN BUDGET AND LIMIT"),
            (["budget", "exercises/ex15_eval_budget.json"], 1, "PLAN: NOT YET"),
            (["traces"], 0, "R1 FIRED"),
            (["traces", "--trace", "T-203"], 0, "TRAJECTORY CHECKS"),
            (["run", "--candidate", "candidate-v2", "--seed", "3", "--only", "RC-001"], 1, "has no randomness"),
        ):
            got, text = cli(*args)
            self.assertEqual(got, code, f"{args}: {text[-400:]}")
            self.assertIn(part, text, args)

    def test_judge_command_on_a_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, text = cli("run", "--candidate", "playground.break_it:SoundAnnoyed", "--out", tmp,
                             "--cases", "data/cases/core.jsonl")
            run = next(Path(tmp).glob("*.json"))
            code, text = cli("judge", "judge-a", "--run", str(run))
        self.assertEqual(code, 0, text)
        self.assertIn("problem     26 / 26 (100%)", text)


if __name__ == "__main__":
    unittest.main()
