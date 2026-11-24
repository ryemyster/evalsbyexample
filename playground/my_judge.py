"""Bring your own judge model. OPTIONAL: nothing else in the course needs this file.

A judge grades drafts; it doesn't write them. These classes reuse the provider
connections in playground/my_model.py (same base URLs and key variables) but send
the judge prompt instead, with their own model setting:

    export EVALS_JUDGE_MODEL=<a model name from your provider's docs>
    python3 -m returns_eval calibrate playground.my_judge:OpenAIJudge --split calibration
    python3 -m returns_eval bias-check playground.my_judge:OpenAIJudge

Calibrate on the calibration split first: it's 24 judge calls. The bias check makes
a few hundred calls, so check the cost before running it on a paid model.

Pick a judge from a different model family than the model whose drafts it grades,
so self-preference can't inflate the results (Lesson 12). Optional for every judge:
EVALS_JUDGE_TEMPERATURE (otherwise the provider's default, or EVALS_TEMPERATURE).
"""

from __future__ import annotations

import os

from playground.my_model import (
    ClaudeModel, DeepSeekModel, GeminiModel, KimiModel, OllamaModel, OpenAICompatibleModel, OpenAIModel,
)
from returns_eval.judging import LLMJudge


class ProviderJudge(LLMJudge):
    """A judge that sends its prompt through one of the candidate adapters' connections."""

    transport_class = OpenAICompatibleModel
    description = "A judge model behind an OpenAI-compatible endpoint."

    def __init__(self, prompt=None) -> None:
        super().__init__(prompt)
        self.transport = self.transport_class()
        model = os.environ.get("EVALS_JUDGE_MODEL")
        if model:
            self.transport.model = model
        if os.environ.get("EVALS_JUDGE_TEMPERATURE") is not None and hasattr(self.transport, "temperature"):
            self.transport.temperature = os.environ["EVALS_JUDGE_TEMPERATURE"]
        self.name = f"{getattr(self.transport, 'name', 'judge')}-judge"
        self.version = self.transport.model or "unset"   # the judge model is recorded like a candidate's
        self.family = self.version

    def complete(self, prompt: str) -> str:
        text = self.transport.complete(prompt)
        self.last_usage = getattr(self.transport, "last_usage", None)
        return text


class OpenAICompatibleJudge(ProviderJudge):
    transport_class = OpenAICompatibleModel


class OpenAIJudge(ProviderJudge):
    transport_class = OpenAIModel


class GeminiJudge(ProviderJudge):
    transport_class = GeminiModel


class DeepSeekJudge(ProviderJudge):
    transport_class = DeepSeekModel


class KimiJudge(ProviderJudge):
    transport_class = KimiModel


class OllamaJudge(ProviderJudge):
    transport_class = OllamaModel


class ClaudeJudge(ProviderJudge):
    """Claude via Anthropic's official SDK (pip install anthropic). Uses EVALS_JUDGE_MODEL, else ClaudeModel's default."""

    transport_class = ClaudeModel
