# OPTIONAL: grading a real model

You don't need this for the tutorial. Everything else in the repository runs offline with no API key and no extra packages.

## Quick start

Ready-made candidates for Claude, OpenAI, Gemini, DeepSeek, Kimi, Ollama, and any OpenAI-compatible endpoint are in `playground/my_model.py`. The table, environment variables, and commands are in [extending.md](extending.md#bring-your-own-model).

## How it fits together

```
case ──> LLMCandidate.build_prompt() ──> complete(prompt) ──> parse_model_json() ──> Draft
              (policy, orders,               (your provider:        (JSON reply; any        │
               customer message               one HTTP call          "actions" are routed   │
               marked as content)             or SDK call)           through the Toolbox)   ▼
                                                                                   same grader, same gates
```

`returns_eval/candidates/llm_adapter.py` defines `LLMCandidate`. A model candidate only implements `complete(prompt) -> str`. The base class does the rest:

- **Prompt.** The policy version for the case, today's date, the verified customer, their orders (looked up through the read-only tools, so the lookups are in the trace), and the customer's message, fenced and marked as content, not instructions.
- **Parsing.** It expects a JSON object with `resolution`, `order_id`, `reply_text`, `note_for_agent`, and optionally `actions`. Text around the JSON, code fences, and `<think>` reasoning are ignored. An unknown `resolution` becomes `escalate`.
- **Actions.** If the model asks for tools in `actions`, each one goes through `tools.call(...)`. Forbidden ones (`issue_refund`, `send_reply`, ...) are recorded, nothing happens in the sandbox, and the `action_boundary` check fails as critical. Don't give a model a path around the toolbox, or the grader can't see what it did.

## Writing your own

```python
from returns_eval.candidates.llm_adapter import LLMCandidate

class MyModel(LLMCandidate):
    name = "my-model"
    version = "model-name-and-prompt-version"

    def complete(self, prompt: str) -> str:
        ...  # call your provider; return the model's text
```

```bash
python3 -m returns_eval run --candidate my_module:MyModel --only RC-001 RC-024
python3 -m returns_eval run --candidate my_module:MyModel --repeat 3 --baseline baseline
```

Use the provider's documentation for client and method names; don't guess them. If the provider has an OpenAI-compatible endpoint, subclass `OpenAICompatibleModel` in `playground/my_model.py` and add an entry to `PROVIDERS` instead of writing HTTP code.

## Things to keep true

- **Use repeats.** A model can answer the same input differently. With `--repeat 3`, a case passes only if all three attempts pass.
- **Record the model version.** Put the model name (and your prompt version, if you change the prompt) in `version`, so runs stay comparable.
- **Change the prompt deliberately.** `PROMPT_TEMPLATE` is part of the candidate. If you edit it, bump `version` and rerun every case.
- **Watch for data leaving your machine.** The cases are fictional, so sending them to a provider is fine. Real tickets are not; follow your organization's data rules first.
- **Calibrate any model grader.** If you later use a model to grade drafts, compare its judgments with human scorecards on the same drafts first, the way `review-summary` compares two reviewers.
