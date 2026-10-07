"""Helpers shared by the exercise tests.

Set EVALS_USE_SOLUTIONS=1 (or run `python3 -m exercises N --solution`) to point
the same tests at the reference solutions instead of your work.
"""

from __future__ import annotations

import importlib
import os
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def using_solutions() -> bool:
    return os.environ.get("EVALS_USE_SOLUTIONS") == "1"


def load(module_name: str):
    package = "solutions" if using_solutions() else "exercises"
    return importlib.import_module(f"{package}.{module_name}")


def file_path(name: str, exercise_location: Path | None = None) -> Path:
    if using_solutions():
        return REPO / "solutions" / name
    return exercise_location or REPO / "exercises" / name


class ExerciseCase(unittest.TestCase):
    exercise = 0
    where = ""

    def not_done(self, detail: str) -> None:
        self.fail(f"Exercise {self.exercise} is not done yet: {detail} (edit {self.where})")

    def call(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except NotImplementedError as exc:
            self.not_done(str(exc) or f"{fn.__name__} still raises NotImplementedError")
