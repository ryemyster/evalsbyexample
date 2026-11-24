import json

from returns_eval.rubric import lint

from ._support import ExerciseCase, file_path


class TestEx11(ExerciseCase):
    exercise = 11
    where = "exercises/ex11_rubric.json"

    def setUp(self):
        self.rubric = json.loads(file_path("ex11_rubric.json").read_text(encoding="utf-8"))
        self.criteria = {c.get("id"): c for c in self.rubric.get("criteria", []) if isinstance(c, dict)}

    def test_passes_rubric_check(self):
        errors, _ = lint(self.rubric)
        if errors:
            self.not_done(f"{len(errors)} rubric-check problem(s), starting with: {errors[0]} "
                          "(run python3 -m returns_eval rubric-check exercises/ex11_rubric.json)")

    def test_covers_the_qualities_the_team_cares_about(self):
        self.assertGreaterEqual(len(self.criteria), 5, "the team wants at least five criteria")
        tone = self.criteria.get("tone")
        self.assertIsNotNone(tone, "keep a criterion with id 'tone': the labeled drafts in data/labels/ use it")
        self.assertEqual((tone.get("scale"), tone.get("values")), ("binary", ["ok", "problem"]),
                         "the tone labels are binary: ok or problem")

    def test_each_kind_of_grader_and_reference_is_used(self):
        graders = {c.get("graded_by") for c in self.criteria.values()}
        self.assertTrue({"code", "judge", "human"} <= graders,
                        "decide what grades each criterion: use code where the record settles it, a judge where "
                        "wording matters, and people where expert judgment is needed")
        refs = {c.get("reference") for c in self.criteria.values()}
        self.assertIn("none", refs, "include at least one reference-free criterion")
        self.assertTrue(refs - {"none"}, "include at least one criterion graded against a reference")
