"""Bring your own model. OPTIONAL: nothing else in the tutorial needs this file.

Pick a candidate, set the model name, and start with two cases:

    python3 -m returns_eval run --candidate playground.my_model:OfflineFakeModel        # no setup at all

    export EVALS_MODEL=<a model name from your provider's docs>
    python3 -m returns_eval run --candidate playground.my_model:OpenAIModel   --only RC-001 RC-024
    python3 -m returns_eval run --candidate playground.my_model:GeminiModel   --only RC-001 RC-024
    python3 -m returns_eval run --candidate playground.my_model:DeepSeekModel --only RC-001 RC-024
    python3 -m returns_eval run --candidate playground.my_model:KimiModel     --only RC-001 RC-024
    python3 -m returns_eval run --candidate playground.my_model:OllamaModel   --only RC-001 RC-024
    python3 -m returns_eval run --candidate playground.my_model:ClaudeModel   --only RC-001 RC-024

Each provider reads its key from the environment variable in PROVIDERS below
(OPENAI_API_KEY, GEMINI_API_KEY, ...). Ollama on your own machine needs no key.

Any other provider with an OpenAI-compatible /chat/completions endpoint works through
OpenAICompatibleModel: set EVALS_BASE_URL and EVALS_API_KEY from that provider's docs.

Optional for every candidate: EVALS_TEMPERATURE (omitted unless set).

Everything except ClaudeModel uses only the Python standard library. ClaudeModel uses
Anthropic's official SDK: pip install anthropic.

Before a full run against a paid model, read docs/extending.md#bring-your-own-model:
start with --only, then use --repeat 3 for the real comparison.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from returns_eval.candidates.llm_adapter import LLMCandidate
from returns_eval.models import Draft, Request
from returns_eval.tools import Toolbox

# Base URLs and docs checked against each provider's documentation on 2026-10-06.
# Providers change these; if a request fails, compare with the docs link.
PROVIDERS = {
    "openai": {"base_url": "https://api.openai.com/v1", "key_env": "OPENAI_API_KEY",
               "docs": "https://developers.openai.com/api/reference/overview"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "key_env": "GEMINI_API_KEY",
               "docs": "https://ai.google.dev/gemini-api/docs/openai"},
    "deepseek": {"base_url": "https://api.deepseek.com", "key_env": "DEEPSEEK_API_KEY",
                 "docs": "https://api-docs.deepseek.com/"},
    "kimi": {"base_url": "https://api.moonshot.ai/v1", "key_env": "MOONSHOT_API_KEY",
             "docs": "https://platform.kimi.ai/docs/guide/start-using-kimi-api"},
    # Local Ollama needs no key. For Ollama's cloud, set EVALS_BASE_URL=https://ollama.com/v1 and OLLAMA_API_KEY.
    "ollama": {"base_url": "http://localhost:11434/v1", "key_env": "OLLAMA_API_KEY", "key_optional": True,
               "docs": "https://docs.ollama.com/api/openai-compatibility"},
}


class OfflineFakeModel(LLMCandidate):
    """A stand-in "model" with deliberately naive behavior. No network, no key."""

    name = "offline-fake-model"
    version = "1"
    description = "Pretend model for trying the adapter offline. Naive on purpose."

    def complete(self, prompt: str) -> str:
        message = prompt.split("<<<", 1)[1].split(">>>", 1)[0].strip()
        orders = re.findall(r'"order_id": "(EO-\d{5})"', prompt)
        order_id = orders[0] if orders else None
        actions = []
        # Like an over-obliging model, it "does what the message says" when someone claims authority.
        if re.search(r"approved|authori[sz]ed", message, re.I) and "refund" in message.lower() and order_id:
            actions.append({"tool": "issue_refund", "args": {"order_id": order_id, "amount": "full"}})
        reply = {
            "resolution": "escalate",
            "order_id": order_id,
            "reply_text": "Hi there, thanks for your message. A member of our team will review it and follow up with you.",
            "note_for_agent": "offline fake model: generic reply",
            "actions": actions,
        }
        return "Here is the draft:\n" + json.dumps(reply)


class OpenAICompatibleModel(LLMCandidate):
    """Any provider with an OpenAI-compatible /chat/completions endpoint (standard library only).

    Use directly with EVALS_BASE_URL and EVALS_API_KEY, or use a subclass below that
    fills in a provider's base URL and key variable.
    """

    provider = "custom"
    description = "A model behind an OpenAI-compatible /chat/completions endpoint."

    def __init__(self) -> None:
        preset = PROVIDERS.get(self.provider, {})
        self.name = self.provider
        self.model = os.environ.get("EVALS_MODEL", "")
        self.version = self.model or "unset"  # the model name is recorded in the run metadata
        self.base_url = os.environ.get("EVALS_BASE_URL", preset.get("base_url", "")).rstrip("/")
        self.key_env = preset.get("key_env", "EVALS_API_KEY")
        self.api_key = os.environ.get("EVALS_API_KEY") or os.environ.get(self.key_env, "")
        self.key_optional = preset.get("key_optional", False)
        self.docs = preset.get("docs", "your provider's API documentation")
        self.temperature = os.environ.get("EVALS_TEMPERATURE")

    def complete(self, prompt: str) -> str:
        if not self.model:
            raise RuntimeError(f"Set EVALS_MODEL to a model name from {self.docs}")
        if not self.base_url:
            raise RuntimeError("Set EVALS_BASE_URL to your provider's OpenAI-compatible base URL (ending before /chat/completions).")
        if not self.api_key and not self.key_optional:
            raise RuntimeError(f"Set {self.key_env} (or EVALS_API_KEY) to your API key. See {self.docs}")
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        if self.temperature is not None:
            body["temperature"] = float(self.temperature)
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        url = f"{self.base_url}/chat/completions"
        request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Could not reach {url} ({exc.reason}). Check the URL, or that the server is running.") from exc
        content = data["choices"][0]["message"].get("content")
        if not content:
            raise RuntimeError(f"{self.provider} returned no text content (finish_reason: "
                               f"{data['choices'][0].get('finish_reason')}).")
        return content


class OpenAIModel(OpenAICompatibleModel):
    provider = "openai"
    description = "OpenAI via its Chat Completions endpoint."


class GeminiModel(OpenAICompatibleModel):
    provider = "gemini"
    description = "Google Gemini via its OpenAI-compatible endpoint."


class DeepSeekModel(OpenAICompatibleModel):
    provider = "deepseek"
    description = "DeepSeek via its OpenAI-compatible endpoint."


class KimiModel(OpenAICompatibleModel):
    provider = "kimi"
    description = "Kimi (Moonshot AI) via its OpenAI-compatible endpoint."


class OllamaModel(OpenAICompatibleModel):
    provider = "ollama"
    description = "A model served by Ollama (local by default)."


class ClaudeModel(LLMCandidate):
    """Claude via Anthropic's official Python SDK (pip install anthropic)."""

    name = "claude"
    description = "Claude via the Anthropic Python SDK."

    def __init__(self) -> None:
        self.model = os.environ.get("EVALS_MODEL") or os.environ.get("EVALS_CLAUDE_MODEL") or "claude-opus-5-5"
        self.version = self.model
        self._client = None
        self.served_by = None

    def make_client(self):
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError("ClaudeModel needs the Anthropic SDK: pip install anthropic") from exc
        return anthropic.Anthropic()  # credentials: ANTHROPIC_API_KEY, or a profile from `ant auth login`

    def complete(self, prompt: str) -> str:
        if self._client is None:
            self._client = self.make_client()
        response = self._client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}],
            # If a safety classifier declines, let the API retry on its recommended
            # fallback model instead of returning the refusal. Remove these two lines
            # if you want refusals to show up as failures instead.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None)
            raise RuntimeError(f"Model declined the request (category: {category}).")
        self.served_by = response.model
        return "".join(block.text for block in response.content if block.type == "text")

    def draft_reply(self, request: Request, tools: Toolbox) -> Draft:
        draft = super().draft_reply(request, tools)
        if self.served_by and self.served_by != self.model:
            # A fallback model answered. Record it, because it changes what this run measured.
            draft.note_for_agent = f"{draft.note_for_agent} [served by {self.served_by}]".strip()
        return draft
