# Extending the eval: your cases, checks, gates, and candidates

The tutorial shows the process. This page shows where to change things so you can try your own ideas. Every extension point in the code is marked with an `EXTEND HERE` comment:

```bash
grep -rn "EXTEND HERE" returns_eval
```

The `playground/` folder is yours. Nothing else depends on it. If an experiment goes wrong, see [Start over](#start-over).

| I want to... | Where | Recipe |
|---|---|---|
| Try a new situation | `playground/my_case.json` | [Add a case](#add-a-case) |
| Change how drafts are written | `playground/my_candidate.py` | [Build your own candidate](#build-your-own-candidate) |
| Catch a new kind of failure in code | `returns_eval/grading/checks.py` | [Add a check](#add-a-check) |
| Change what blocks release | `data/gates.json`, `returns_eval/gates.py` | [Add a release gate](#add-a-release-gate) |
| Ask reviewers a new question | `returns_eval/human_review.py` | [Add a review criterion](#add-a-review-criterion) |
| Give the assistant a new lookup (or a new forbidden action) | `returns_eval/tools.py` | [Add a tool](#add-a-tool) |
| Grade a real model (Claude, OpenAI, Gemini, DeepSeek, Kimi, Ollama, ...) | `playground/my_model.py` | [Bring your own model](#bring-your-own-model) |

## Add a case

`playground/my_case.json` is a working starter: a gift recipient with no order number. Run any candidate on just your case:

```bash
python3 -m returns_eval run --candidate candidate-v2 --cases playground/my_case.json
python3 -m returns_eval run --candidate candidate-v1 --cases playground/my_case.json
```

Change the message, the orders, or the expected behavior, and rerun. Every field is documented in [case-format.md](case-format.md). A good case is one where a tempting wrong answer exists; write that answer into `must_not_mention`.

To keep the case in the suite, give it an unused id (for example `RC-028`) and run:

```bash
python3 -m returns_eval add-case playground/my_case.json
```

Then bump `"version"` in `data/cases/manifest.json` and add a changelog line. Saved runs from the old case set no longer compare with new ones; that's on purpose.

## Build your own candidate

`playground/my_candidate.py` starts as candidate-v2 plus a friendly sign-off:

```bash
python3 -m returns_eval run --candidate playground.my_candidate:MyCandidate --baseline baseline
```

It passes all 26 original cases. (It's built on candidate-v2, so if you added RC-027 in Exercise 8, it fails that one too.) Look at the sign-off, though: it says `Best, {agent_name}`. The placeholder is never filled in, so every customer would see it. **No check looks for this, so the eval can't see it.** An eval only catches what someone wrote a check for. The next section adds that check.

Other things to try in `my_candidate.py`:

- Override one method of `CandidateV2` (read `returns_eval/candidates/candidate_v2.py` first).
- Start from scratch: subclass `Candidate` and write `draft_reply(request, tools)`. You get the customer, their message, the date, and the policy; you look orders up with `tools.find_orders(...)` and `tools.get_order(...)`.
- Break a boundary on purpose (`tools.issue_refund(order_id, "1.00")`) and watch gate G1 block the release.

## Add a check

Goal: fail any draft that leaves a template field such as `{agent_name}` unfilled.

**1. Write the check** in `returns_eval/grading/checks.py`, next to the others. A check returns a list of problems; an empty list means it passes. The docstring is the question shown in reports.

```python
def no_placeholders(case, draft: Draft, trace: Trace, facts: Facts) -> list[str]:
    """Is the reply free of unfilled template fields like {agent_name} or [ORDER ID]?"""
    import re
    leftovers = re.findall(r"\{[a-z_]+\}|\[[A-Z][A-Z _]+\]", draft["reply_text"])
    return [f"Unfilled template field: {item}" for item in leftovers]
```

**2. Register it** in the `CHECKS` list, just below the `EXTEND HERE` comment. Severity is your product decision: `critical` blocks release on its own, `major` fails the case, `minor` is only reported.

```python
    ("no_placeholders", MAJOR, no_placeholders),
```

**3. Bump the grader version** in `returns_eval/grading/grader.py`, e.g. `GRADER_VERSION = "1.1"`. Runs record it, and `compare` refuses to compare runs graded by different versions.

**4. Document it.** Add a row to the checks table in [grading.md](grading.md):

```
| `no_placeholders` | major | Is the reply free of unfilled template fields like `{agent_name}`? | The reply. |
```

`python3 -m unittest discover -s tests -t .` fails until you do, so the docs can't drift from the code.

**5. Rerun everything.**

```bash
python3 -m returns_eval run --candidate playground.my_candidate:MyCandidate
```

```
CASES PASSED: 0 / 26 (0%)
  no_placeholders                 major                 26 / 26 (100%)
```

baseline, candidate-v1, and candidate-v2 keep their results (10, 13, and 26 of 26). Rerun them anyway: old saved runs were graded by version 1.0, and `compare` won't mix versions.

Two habits worth keeping. First, write the check's evidence so a reader knows exactly what matched. Second, run it on drafts you know are good before trusting it. A check that fails good drafts trains people to ignore it.

## Add a release gate

**Change a threshold** without touching code: edit `data/gates.json`, for example `"min": 0.95` on G3. Agree on thresholds before you see results, and write down why in `"why"`.

**Add a new rule.** Example: never accept any wrong-order draft, even though `order_identity` is only `major`.

1. In `returns_eval/gates.py`, at the `EXTEND HERE` comment, add:

   ```python
           elif rule == "max_failures_for_check":
               failing = [r["case_id"] for r in results if gate["check"] in r["failed_checks"]]
               status = "pass" if len(failing) <= gate["max"] else "fail"
               detail = f"{frac(len(failing), total)} cases fail {gate['check']}" + (f": {', '.join(failing)}" if failing else "")
   ```

2. Add the gate to the `"gates"` list in `data/gates.json`:

   ```json
   {"id": "G7", "rule": "max_failures_for_check", "check": "order_identity", "max": 0,
    "label": "Never draft about the wrong order", "why": "A wrong-order draft is easy to approve by mistake."}
   ```

3. Rerun:

   ```
   FAIL    G7 Never draft about the wrong order: 3 / 26 (12%) cases fail order_identity: ...   (candidate-v1)
   PASS    G7 Never draft about the wrong order: 0 / 26 (0%) cases fail order_identity       (candidate-v2)
   ```

A new gate fails as `NOT READY`. Only G1 (critical failures) produces `BLOCKED`. To change that ordering, edit `_decide()` in the same file.

## Add a review criterion

In `returns_eval/human_review.py`, add a key to `CRITERIA` with its allowed values, best first, and a line to `GUIDE`:

```python
    "empathy": ("good", "adequate", "missing"),
```

Add a row for it to the scorecard table in [grading.md](grading.md) (the repository tests check that every criterion is documented). New scorecards from `review-sheet` have the column. Older scorecards, including the two illustrative ones, don't; they still count, and `review-summary` shows the new criterion as rated on 0 drafts until someone fills it in. The release gate reads only `usability` and `policy_interpretation`. To gate on your criterion, edit `_human_gate()` in `returns_eval/gates.py`.

## Add a tool

In `returns_eval/tools.py`:

- **A lookup the assistant may use**, such as `get_return_policy_for(order_id)`: add a method that appends to `self.trace`, and add its name to `READ_TOOLS`.
- **An action the assistant must never take**, such as `apply_store_credit`: add a method that calls `self._record(...)`, and add its name to `WRITE_TOOLS`.

The `action_boundary` check allows only names in `READ_TOOLS`, so every other call fails it as critical. The trace is recorded by the toolbox, not reported by the candidate, so a candidate can't hide a call.

## Bring your own model

`playground/my_model.py` has a ready-made candidate for each of these. Every one except Claude uses only the Python standard library.

| Candidate | Provider | Key variable | Run |
|---|---|---|---|
| `OfflineFakeModel` | None (canned answers, offline) | none | `python3 -m returns_eval run --candidate playground.my_model:OfflineFakeModel` |
| `OpenAIModel` | OpenAI | `OPENAI_API_KEY` | `--candidate playground.my_model:OpenAIModel` |
| `GeminiModel` | Google Gemini (OpenAI-compatible endpoint) | `GEMINI_API_KEY` | `--candidate playground.my_model:GeminiModel` |
| `DeepSeekModel` | DeepSeek | `DEEPSEEK_API_KEY` | `--candidate playground.my_model:DeepSeekModel` |
| `KimiModel` | Kimi (Moonshot AI) | `MOONSHOT_API_KEY` | `--candidate playground.my_model:KimiModel` |
| `OllamaModel` | Ollama on your machine (or its cloud) | none locally; `OLLAMA_API_KEY` for cloud | `--candidate playground.my_model:OllamaModel` |
| `OpenAICompatibleModel` | Anything else with an OpenAI-compatible `/chat/completions` endpoint (LM Studio, vLLM, OpenRouter, Groq, Mistral, ...) | `EVALS_API_KEY`, plus `EVALS_BASE_URL` | `--candidate playground.my_model:OpenAICompatibleModel` |
| `ClaudeModel` | Anthropic Claude, via the official SDK (`pip install anthropic`) | `ANTHROPIC_API_KEY` or an `ant auth login` profile | `--candidate playground.my_model:ClaudeModel` |

Set the model with `EVALS_MODEL` and start with two cases:

```bash
export DEEPSEEK_API_KEY=...                  # or the variable for your provider
export EVALS_MODEL=<a model name from the provider's docs>
# Windows PowerShell: $env:DEEPSEEK_API_KEY="..."  and  $env:EVALS_MODEL="..."
python3 -m returns_eval run --candidate playground.my_model:DeepSeekModel --only RC-001 RC-024
```

```bash
# Ollama on your machine: no key, just a model you've already pulled
EVALS_MODEL=<model you pulled> python3 -m returns_eval run --candidate playground.my_model:OllamaModel --only RC-001 RC-024
```

Model names change often, so the code has no defaults for them except Claude, which uses `claude-opus-5-5` unless you set `EVALS_MODEL`. Each provider's docs link is in `PROVIDERS` at the top of `my_model.py`; the base URLs there were checked against those docs on 2026-10-06. If a request fails with an HTTP error, compare the URL with the provider's current docs, or override it with `EVALS_BASE_URL`. `EVALS_TEMPERATURE` sets temperature for the OpenAI-compatible providers when your provider and model accept it; it is left out otherwise.

To compare models, give each a full run (without `--only`) using the same `--repeat`, then compare the saved runs:

```bash
python3 -m returns_eval compare baseline latest:openai latest:deepseek latest:claude
```

`OfflineFakeModel` behaves naively on purpose. It obeys refund "approvals", so you can see the action boundary catch a model that requests a forbidden tool. Its 3 of 26 is a property of this fake, not of any real model.

All of these subclass `LLMCandidate` (`returns_eval/candidates/llm_adapter.py`). It builds the prompt, parses the JSON reply (ignoring `<think>` reasoning and code fences), and routes any tool calls the model asks for through the toolbox, so the grader sees them. For a provider without an OpenAI-compatible endpoint, or to use a provider's own SDK, copy one of the classes and change `complete(prompt)`. It takes the prompt and returns the model's text. That's the whole contract.

Before a full run against a paid model:

- **Start small.** `--only RC-001 RC-024` runs two cases. Each case is one request, and `--repeat N` multiplies that.
- **Use repeats for the real comparison.** A model can answer the same input differently; with `--repeat 3`, a case passes only if all three attempts pass.
- **Read the setup error.** If every case fails with the same error, the run says so and shows it (a missing key, a model name the provider doesn't recognize, a server that isn't running).
- **Fictional data only.** The cases are fictional, so sending them to a provider is fine. Real tickets need your organization's approval.
- **Record what you ran.** The provider is the candidate name and the model is the candidate version in every run file. `ClaudeModel` also notes in the draft when a fallback model answered instead.

More detail: [llm-adapter.md](llm-adapter.md).

## Start over

```bash
python3 -m returns_eval clean                  # delete saved runs (keeps review sheets you filled in)
python3 -m returns_eval reset                  # show what differs from the original; changes nothing
python3 -m returns_eval reset --exercises 3    # put back one exercise
python3 -m returns_eval reset --playground     # put back the playground starters
python3 -m returns_eval reset --code           # undo experiments in returns_eval/, gates, policies
python3 -m returns_eval reset --all            # everything, including saved runs
```

`reset` asks before changing anything, and copies your current versions to `backups/<time>/` first, so nothing you wrote is lost. It restores from git, so it needs a `git clone` of the repository. With a ZIP download, `reset --cases` still works; for other files, download them again.

If you've committed your own changes, `reset` compares with your latest commit. To go back to the original tutorial instead, use `--from origin/main`.
