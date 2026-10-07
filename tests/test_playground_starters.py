"""Checks that the shipped playground starters work. The playground is yours to
change; if you rewrite these files, update or delete the matching tests."""

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest import mock

from playground import break_it
from playground.my_candidate import MyCandidate
from playground.my_model import (
    PROVIDERS, ClaudeModel, DeepSeekModel, GeminiModel, KimiModel, OfflineFakeModel, OllamaModel,
    OpenAICompatibleModel, OpenAIModel,
)
from returns_eval.candidates.llm_adapter import parse_model_json
from returns_eval.cases import REPO_ROOT, validate_case
from returns_eval.grading import grade_case
from returns_eval.harness import produce

from .helpers import CASES

GOOD = {"resolution": "inform", "order_id": "EO-10417",
        "reply_text": "Hi Ana, we received your return on August 7, and it's waiting for inspection."}


def graded(candidate, case_id):
    case = CASES[case_id]
    return grade_case(case, [produce(candidate, case)])


class TestStarters(unittest.TestCase):
    def test_my_candidate_runs_and_has_the_hidden_placeholder(self):
        result = graded(MyCandidate(), "RC-002")
        self.assertNotIn("candidate_error", result["failed_checks"])
        self.assertIn("{agent_name}", result["attempts"][0]["draft"]["reply_text"])

    def test_break_it_mistakes_get_the_verdicts_the_tutor_describes(self):
        # TUTOR.md's "Your turn: break it" relies on these exact outcomes.
        cases = [CASES[c] for c in ("RC-002", "RC-021", "RC-024")]

        def worst(cls):
            order = {None: 0, "minor": 1, "major": 2, "critical": 3}
            return max((grade_case(c, [produce(cls(), c)])["worst_severity"] for c in cases), key=order.get)

        self.assertEqual(worst(break_it.PromiseADate), "critical")
        self.assertEqual(worst(break_it.TakeAnAction), "critical")
        self.assertEqual(worst(break_it.SkipTheSpecialist), "major")
        self.assertIn(worst(break_it.SoundAnnoyed), (None, "minor"))  # no check looks for tone
        self.assertIn(worst(break_it.MyOwnMistake), (None, "minor"))

    def test_my_case_is_valid(self):
        case = json.loads((REPO_ROOT / "playground" / "my_case.json").read_text())
        self.assertEqual(validate_case(case), [])

    def test_offline_fake_model_requests_are_caught(self):
        result = graded(OfflineFakeModel(), "RC-024")
        self.assertIn("action_boundary", result["failed_checks"])
        self.assertEqual(result["worst_severity"], "critical")


class _Handler(BaseHTTPRequestHandler):
    seen = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        _Handler.seen.append((self.path, dict(self.headers), body))
        payload = json.dumps({"choices": [{"message": {"role": "assistant", "content": json.dumps(GOOD)}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


class TestOpenAICompatible(unittest.TestCase):
    def _serve(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_port}/v1"

    def test_round_trip_against_a_fake_server(self):
        env = {"EVALS_MODEL": "demo-model", "EVALS_BASE_URL": self._serve(), "EVALS_API_KEY": "k", "EVALS_TEMPERATURE": "0"}
        with mock.patch.dict(os.environ, env):
            result = graded(OpenAICompatibleModel(), "RC-001")
        path, headers, body = _Handler.seen[-1]
        self.assertEqual(path, "/v1/chat/completions")
        self.assertEqual(headers["Authorization"], "Bearer k")
        self.assertEqual((body["model"], body["temperature"], body["messages"][0]["role"]), ("demo-model", 0.0, "user"))
        self.assertTrue(result["passed"], result["failed_checks"])

    def test_presets_use_their_base_url_and_key_variable(self):
        for cls, provider in ((OpenAIModel, "openai"), (GeminiModel, "gemini"), (DeepSeekModel, "deepseek"),
                              (KimiModel, "kimi"), (OllamaModel, "ollama")):
            key_env = PROVIDERS[provider]["key_env"]
            with mock.patch.dict(os.environ, {"EVALS_MODEL": "m", key_env: "secret"}, clear=True):
                model = cls()
            self.assertEqual((model.name, model.version), (provider, "m"))
            self.assertEqual(model.base_url, PROVIDERS[provider]["base_url"].rstrip("/"))
            self.assertEqual(model.api_key, "secret")
            self.assertTrue(model.base_url.startswith(("https://", "http://localhost")))

    def test_preset_without_key_explains_which_variable(self):
        with mock.patch.dict(os.environ, {"EVALS_MODEL": "m"}, clear=True):
            attempt = produce(DeepSeekModel(), CASES["RC-001"])
        self.assertIn("DEEPSEEK_API_KEY", attempt["error"])

    def test_local_ollama_needs_no_key(self):
        with mock.patch.dict(os.environ, {"EVALS_MODEL": "m", "EVALS_BASE_URL": self._serve()}, clear=True):
            result = graded(OllamaModel(), "RC-001")
        self.assertNotIn("Authorization", _Handler.seen[-1][1])
        self.assertTrue(result["passed"], result["failed_checks"])

    def test_missing_model_name_is_explained(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "k"}, clear=True):
            attempt = produce(OpenAIModel(), CASES["RC-001"])
        self.assertIn("Set EVALS_MODEL", attempt["error"])

    def test_reasoning_text_and_fences_are_ignored(self):
        raw = "<think>Maybe {not this}.</think>\n```json\n" + json.dumps(GOOD) + "\n```"
        self.assertEqual(parse_model_json(raw)["order_id"], "EO-10417")


class _FakeAnthropic:
    def __init__(self, stop_reason="end_turn", served_by="claude-opus-5-5"):
        self.calls = []
        text = SimpleNamespace(type="text", text=json.dumps(GOOD))
        thinking = SimpleNamespace(type="thinking", thinking="")
        self.response = SimpleNamespace(content=[thinking, text], stop_reason=stop_reason, model=served_by,
                                        stop_details=SimpleNamespace(category="cyber"))
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class TestClaudeModel(unittest.TestCase):
    def _model(self, fake):
        model = ClaudeModel()
        model.make_client = lambda: fake
        return model

    def test_request_shape_and_text_extraction(self):
        fake = _FakeAnthropic()
        with mock.patch.dict(os.environ, {}, clear=True):
            result = graded(self._model(fake), "RC-001")
        call = fake.calls[0]
        self.assertEqual(call["model"], "claude-opus-5-5")
        self.assertEqual((call["fallbacks"], call["betas"]), ("default", ["server-side-fallback-2026-07-01"]))
        self.assertNotIn("temperature", call)
        self.assertTrue(result["passed"], result["failed_checks"])

    def test_refusal_becomes_a_recorded_error(self):
        attempt = produce(self._model(_FakeAnthropic(stop_reason="refusal")), CASES["RC-001"])
        self.assertIn("declined", attempt["error"])

    def test_fallback_model_is_noted(self):
        attempt = produce(self._model(_FakeAnthropic(served_by="claude-opus-4-8")), CASES["RC-001"])
        self.assertIn("served by claude-opus-4-8", attempt["draft"]["note_for_agent"])


if __name__ == "__main__":
    unittest.main()
