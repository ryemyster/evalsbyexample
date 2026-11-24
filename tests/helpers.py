from returns_eval.cases import CASES_DIR, load_case_set

CORE = load_case_set([CASES_DIR / "core.jsonl"])
CASES = {c["id"]: c for c in CORE.cases}


def draft(text, resolution="inform", order_id=None):
    return {"reply_text": text, "resolution": resolution, "order_id": order_id, "note_for_agent": "", "fingerprint": "x"}


def attempt(text, resolution="inform", order_id=None, trace=None):
    return {"draft": draft(text, resolution, order_id), "trace": trace or [], "error": None}


# Settings the model and judge adapters read. Tests remove these, but keep the rest of the
# environment: on Windows, wiping everything (including SYSTEMROOT) can break networking.
MODEL_VARS = ("EVALS_MODEL", "EVALS_BASE_URL", "EVALS_API_KEY", "EVALS_TEMPERATURE", "EVALS_CLAUDE_MODEL",
              "EVALS_JUDGE_MODEL", "EVALS_JUDGE_TEMPERATURE", "EVALS_SEED", "EVALS_PRICES", "OPENAI_API_KEY",
              "GEMINI_API_KEY", "DEEPSEEK_API_KEY", "MOONSHOT_API_KEY", "OLLAMA_API_KEY", "ANTHROPIC_API_KEY")


def model_env(values=None):
    """Patch os.environ so only `values` are set among the model settings."""
    import os
    from unittest import mock

    env = {k: v for k, v in os.environ.items() if k not in MODEL_VARS}
    env.update(values or {})
    return mock.patch.dict(os.environ, env, clear=True)
