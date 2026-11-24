import json

from returns_eval import economics
from returns_eval.cases import load_case_set
from returns_eval.cli import build_parser

from ._support import ExerciseCase, file_path

COSTS = economics.load_costs()
COMMANDS = set(build_parser()._subparsers._group_actions[0].choices)
CASES = {c["id"]: c for c in load_case_set().cases}


class TestEx15(ExerciseCase):
    exercise = 15
    where = "exercises/ex15_eval_budget.json"

    def setUp(self):
        self.plan = json.loads(file_path("ex15_eval_budget.json").read_text(encoding="utf-8"))

    def _result(self):
        rates = usage = None
        if self.plan.get("judge"):
            rates, usage = economics.judge_rates(self.plan["judge"], self.plan["measured_on"], CASES,
                                                 self.plan.get("people_check_unsure_below"))
        return economics.evaluate(self.plan, COSTS, rates, usage)

    def test_plan_is_filled_in(self):
        problems = economics.plan_problems(self.plan, COMMANDS)
        if problems:
            self.not_done(problems[0])

    def test_within_budget(self):
        cost = self._result()["eval_usd"]
        if cost > COSTS["weekly_budget_usd"]:
            self.not_done(f"the plan costs ${cost:.2f} a week; the budget is ${COSTS['weekly_budget_usd']}")

    def test_within_the_teams_limit(self):
        missed = self._result()["totals"]["missed"]
        self.assertLessEqual(missed, COSTS["team_max_missed_per_week"],
                             f"about {missed:.1f} problems a week would reach customers unseen; the team's limit is "
                             f"{COSTS['team_max_missed_per_week']}")

    def test_reasons_point_at_numbers(self):
        if "TODO" in self.plan.get("why", "TODO"):
            self.not_done("write why")
        self.assertTrue(any(ch.isdigit() for ch in self.plan["why"]), "point at a number you measured or computed")
