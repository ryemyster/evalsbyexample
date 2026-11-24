# Extended curriculum: audit, plan, and decision record

This page is for people maintaining the repository, not for learners. It records why Part 2 of the course looks the way it does: what was already covered, what was missing, what was decided, what was assumed, and what is still limited. Learners start at [START_HERE.md](../../START_HERE.md).

Branch: `extended-curriculum`. Started 2026-11-24.

## 1. Audit of the existing course (Part 1)

Part 1 is one complete eval of an AI feature, told as a product decision: a scripted assistant drafts replies to return requests, and the learner decides whether it is ready for a supervised pilot.

| Area | What exists | Where |
|---|---|---|
| Decision framing | Product question, baseline, success at three levels, unacceptable failures | Lesson 1, Exercise 1, `docs/pm-guide.md` |
| Test cases | 26 cases in 7 categories, versioned and hashed; regression cases | `data/cases/`, `docs/case-format.md`, Exercises 2 and 8 |
| Deterministic grading | 9 checks with fixed severity; grader never imports candidates; evidence per check | `returns_eval/grading/`, `docs/grading.md`, Exercise 3 |
| Human review | Blind scorecards, stale-review detection, worst-rating-counts, percent agreement, disagreement list | `returns_eval/human_review.py`, Exercise 4 |
| Comparison | By category and by check; newly failing cases; refuses mismatched case sets or grader versions | `compare`, Exercise 5 |
| Release gates | Ordered decision; one critical blocks; human review gate | `data/gates.json`, `returns_eval/gates.py`, Exercise 6 |
| Pilot | ILLUSTRATIVE two-arm pilot, per-request-type medians, incident | `pilot`, Exercise 7 |
| Learning from failure | Incident to regression case, fix, rerun everything | Exercises 8 and 9 |
| Repeats | `--repeat N`: a case passes only if every attempt passes; "Reliability" measure | `run --repeat`, `report.measures` |
| Real models | Provider adapters (OpenAI-compatible, Claude SDK), offline fake, prompt and parser | `playground/my_model.py`, `llm_adapter.py` |
| Self-check | Break it; final challenge with must-pass checklist | `playground/break_it.py`, `docs/check-yourself.md` |
| Tutor | Agent-led lessons, guess first, learner's own words, notes file | `TUTOR.md` |

Engineering standards Part 2 must keep: Python 3.9+, standard library only in `returns_eval/`; every rate shown as numerator / denominator; every number in docs comes from a command; made-up data labeled ILLUSTRATIVE in the file name; docs tested against code; exercises fail with a helpful message until done; reference solutions pass; writing a 15-year-old can follow.

## 2. Gap analysis against the requested modules

"Covered" means a learner already does it hands-on. "Partial" means it is mentioned or half-built. "Gap" means it is absent.

| Requested topic | Status before | Notes |
|---|---|---|
| **Module 1: probabilistic evals** | | |
| Deterministic vs probabilistic | Partial | Docs say models vary; every built-in candidate is deterministic, so nobody sees variance offline |
| Repeated execution | Partial | `--repeat` exists; no way to compare run-to-run spread |
| Consistency and variance | Partial | "Reliability" measure only; no spread, no per-case pass rate |
| Model and prompt version comparison | Partial | Versions recorded; no exercise compares prompt versions under noise |
| Structured output validation | Gap | The adapter silently turns an invalid `resolution` into `escalate`, which can make a broken model look safer |
| Semantic vs exact match | Partial | `must_mention` groups; no demonstration of a correct paraphrase failing a lexical check |
| Reproducibility limits | Partial | Mentioned in docs; no seeded simulation |
| Latency, tokens, cost | Partial | p95 wall time only; no tokens or cost |
| Meaningful vs random improvement | Gap | No statistics at all |
| **Module 2: human evaluation and rubrics** | | |
| Observable criteria, rubric construction | Gap | Scorecard criteria exist but rubric design isn't taught |
| Binary / ordinal / continuous | Partial | Scorecard is ordinal; not discussed |
| Reference-based vs reference-free | Gap | |
| Groundedness, relevance, completeness, accuracy | Partial | `supported_facts` covers grounding of numbers and dates |
| Independent annotation, agreement, resolution | Partial | Percent agreement and disagreements; no chance-corrected agreement, no adjudication record |
| Expert-labeled datasets | Gap | |
| **Module 3: LLM-as-judge** | Gap | Only advice to "calibrate any model grader" |
| **Module 4: judge calibration** | Gap | |
| **Module 5: evaluation economics** | Gap | Cost per completion appears as a formula in `pm-guide.md` only |
| **Module 6: production and observability** | | |
| Offline vs online | Covered | Pilot lesson |
| Trace-level, tool correctness, trajectories | Partial | Tool-call trace and `action_boundary`; single-step only |
| Failure attribution by layer | Gap | |
| Production sampling, distribution shift | Gap | Pilot warns about request mix |
| Contamination, evaluation drift | Gap | Case-set hash and grader version guard comparisons, but contamination of splits isn't taught |
| Regression detection | Covered | `compare`, regression cases |
| Human feedback integration | Partial | Agent-caught errors become cases |
| Shadow deployments | Partial | One row in a `pm-guide.md` table |
| Release gates, rollback triggers | Covered offline; partial online | Rollback table in `pm-guide.md` is not executable |
| Dataset maintenance and versioning | Covered for cases | Not for labels or rubrics |
| **Capstone** | Partial | Final challenge covers offline evidence only |

Redundancy check: nothing in Part 1 needs rewriting. Part 2 reuses the case set, grader, gates, candidates, review tooling, and pilot data, and adds what is missing.

## 3. Review of the external reference

Reference: Aakash Gupta with guest Mahesh Yadav, "Practical AI Evals: A FAANG PM's 4-Step Guide", Product Growth newsletter, dated 2026-11-24, https://www.news.aakashg.com/p/practical-ai-evals. Read on 2026-11-24. The podcast, linked articles, and images were not reviewed.

What it recommends, and how it holds up against primary sources:

| Claim in the article | Assessment | Basis |
|---|---|---|
| Turn quality into specific yes/no tests ("3 H's": helpful, honest, harmless) | Consistent with established practice | Anthropic's eval guide asks for specific, measurable criteria; practitioner guidance (Husain) favors binary judgments. Course keeps binary as the default and teaches ordinal and continuous where they fit. |
| Prefer binary scoring over 1-5 scales | Reasonable default, not a law | Binary is easier to define and agree on; ordinal scales carry more information and suit some criteria. Anthropic's guide shows both. The course teaches the trade-off. |
| The "ceiling" for evals is about 70-80%, where top benchmarks top out; set your bar between competition and that ceiling | **Unsupported and misleading for product evals** | Supported by two examples only. Public benchmark ceilings say nothing about a product task with its own cases. A release bar comes from the cost of each failure type, and critical failures need a zero-tolerance rule that no average can satisfy. The course keeps "one critical blocks" and never sets a universal percentage. |
| Guardrail the product to question types it gets right about 80% of the time | Useful idea (route by segment), arbitrary number | Routing by request type is already taught (`pm-guide.md`). The threshold must come from consequences per segment. |
| Judge should agree with the expert 70-80% of the time | **Arbitrary universal threshold** | Agreement needed depends on the base rate, the cost of false acceptance vs false rejection, and how the judge is used. Raw agreement can look high while missing most real problems when problems are rare. Jung et al. (2024) show agreement targets can be set per use case with abstention. |
| Overall agreement is "a trap" | Directionally right, unexplained | Thakur et al. (2024) report that percent agreement often fails to separate judges that chance-corrected measures separate. The course shows this with confusion matrices, per-segment results, and Cohen's kappa. |
| Start with human experts, then build an LLM judge; keep sampling judge outputs for human checking | Consistent with established practice | Zheng et al. (2023); Shankar et al. (2024) on validating validators and criteria drift; Anthropic and OpenAI guides. |
| "200 to 1,000 outputs every week" for human sampling; "$25,000" for expert labels; "30% monthly cut" in eval cost | Anecdotal examples, unsourced | Not used. Module 5 derives sample sizes and costs from the learner's own measured judge errors and stated assumptions. |
| PM owns metrics, bar, gates, judge check, ship decision; engineers own judges and pipeline | One reasonable split, presented as universal | The course presents ownership as decision rights that vary by organization (`pm-guide.md`). |

Not in the article but needed: statistics for repeated runs, chance-corrected agreement, held-out calibration data, judge-specific biases (position, verbosity, self-preference, prompt sensitivity, injection), failure attribution beyond the model, and contamination of evaluation data.

Full source list with links and status (established, emerging, or disputed): [docs/sources.md](../sources.md).

## 4. Implementation plan

Milestones run in order. Each one ends with the repository tests, the reference solutions, and a check that the docs match the output.

| # | Milestone | Files (new unless marked) | Depends on | Done when |
|---|---|---|---|---|
| M1 | Probabilistic evals | `returns_eval/stats.py`; `returns_eval/candidates/simulated.py`; `returns_eval/variance.py`; `harness.py`, `models.py`, `llm_adapter.py`, `grading/` (changed: usage, raw output, `structured_output` check); `variance` command; Exercise 10 | none | Seeded runs reproduce exactly; one-run gaps that are noise are shown as noise; a real improvement is shown as real; structured-output failures are visible |
| M2 | Rubrics and agreement | `returns_eval/rubric.py`; `data/rubrics/`; `data/labels/` (ILLUSTRATIVE); `returns_eval/labels.py`; `rubric-check`, `labels` commands; kappa in `review-summary` (changed); Exercises 11, 12 | M1 (`stats.py`) | A vague rubric fails the linter; agreement beyond chance is reported; splits are checked for overlap |
| M3 | Automated judges | `returns_eval/judging/` (base, simulated judges, probes); `data/judges/` prompts; `judge`, `bias-check` commands; `playground/my_judge.py` (live, optional); Exercise 13 | M2 | Judge output is validated; errors never count as pass; each bias has a probe that measures it |
| M4 | Judge calibration | `returns_eval/judging/calibration.py`; `calibrate` command; Exercise 14 | M2, M3 | Two judges with the same agreement show different error patterns, per segment and per confidence level |
| M5 | Economics | `returns_eval/economics.py`; `data/economics/` (ILLUSTRATIVE); `budget` command; Exercise 15 | M4 | A plan's cost and expected misses come from measured judge errors plus labeled assumptions |
| M6 | Production | `returns_eval/production.py`; `data/production/` (ILLUSTRATIVE); `traces` command; Exercise 16 | M1 | Trajectory checks, attribution by layer, distribution shift, and rollback triggers run on traces |
| M7 | Capstone | `candidate-v5` (in `simulated.py`); Exercise 17; extended checklist | M1-M6 | An aggregate improvement that must not ship is reachable only by looking at repeats and traces |
| M8 | Documentation | README, START_HERE, TUTOR, `TUTOR-PART2.md`, `docs/techniques.md`, `docs/learning-paths.md`, `docs/sources.md`, glossary, grading, pm-guide, extending, llm-adapter, check-yourself, exercises README; verify scripts | all | Docs tests pass; every quoted output matches a command |

## 5. Architectural decisions

- **D1. Part 2 extends Part 1 in place.** Same package, same CLI, same exercise runner (Exercises 10-17), same docs. No parallel tree. Part 1's commands and outputs are unchanged.
- **D2. Simulated models are seeded scripts, run through the same path as real models.** They subclass `LLMCandidate`, produce raw JSON text, and go through the same parser, so structured-output failures are real code paths. Randomness comes from a seed plus the case and attempt number, so a run repeats exactly. Every report labels them SIMULATED.
- **D3. The grader validates raw model output itself.** Drafts from model-backed candidates carry `raw_output`. A new `structured_output` check (major) re-parses it with grader-side code instead of trusting the adapter's cleanup. Scripted candidates have no raw output, so their results don't change. `GRADER_VERSION` goes to 1.2.
- **D4. Judges are graders and live under `returns_eval/judging/`.** They never import candidate code. A judge implements `complete(prompt) -> str`; the base class builds prompts from versioned template files in `data/judges/` and validates the JSON it returns. A malformed judge reply is an error, never a pass.
- **D5. Simulated judges read the item directly and the prompt for features.** A script can't understand a prompt, so each simulated judge decides from the reply text and reacts to prompt features a real model is known to react to (fencing, criterion wording, output format, candidate identity). The docs say plainly that this is a simulation of documented behaviors, not evidence about any model.
- **D6. "Problem found" is the positive class for judge metrics.** So a false negative is a missed problem (false acceptance) and a false positive is a false alarm (false rejection). Every report spells this out in words.
- **D7. Labels are split by case, not by draft.** Drafts of the same case are near-duplicates. Splitting by case prevents leakage between train, calibration, and holdout. A command checks this.
- **D8. No universal thresholds.** Gates and plans take thresholds from files the learner (or team) writes before seeing results. Example thresholds are labeled illustrative, with a reason.
- **D9. Uncertainty is always shown.** Rates on small samples carry Wilson intervals (recommended for small n by Brown, Cai & DasGupta, 2001). Comparisons between candidates use paired, case-level differences with a seeded bootstrap interval (Miller, 2024 recommends paired, question-level analysis).
- **D10. Live paths stay optional and provider-agnostic.** Live judges reuse the provider transports in `playground/my_model.py`. Nothing in the curriculum requires a key or network access.

## 6. Assumptions

- Learners use Part 2 after Part 1, or at least after Lessons 1-3 and "break it". Part 2 lessons say which Part 1 idea they build on.
- All labels, traces, prices, volumes, and rates in Part 2 data are invented for teaching and labeled ILLUSTRATIVE. Results computed from them are real computations on made-up inputs.
- The course author wrote both the human labels and the simulated judges. Labels were written by applying the written rubric to each draft. Because one author wrote both, they are not independent the way two separate teams would be. This is documented where the data lives.
- Token counts for simulated runs are estimates (characters / 4). Live runs record the provider's reported usage when the response includes it.

## 7. Changed files, test results, and limitations

### Changed files

**New code:** `returns_eval/stats.py`, `variance.py`, `rubric.py`, `labels.py`, `economics.py`, `production.py`; `returns_eval/candidates/simulated.py`; `returns_eval/grading/output_format.py`; `returns_eval/judging/` (`__init__.py`, `base.py`, `simulated.py`, `probes.py`, `calibration.py`); `playground/my_judge.py`.

**Changed code:** `models.py` (`Draft.raw_output`), `candidates/llm_adapter.py` (`draft_from_raw`, keeps raw output), `harness.py` (records usage, seed, simulated flag), `grading/checks.py`, `grader.py`, `__init__.py` (`structured_output`, `GRADER_VERSION` 1.2), `report.py` (usage block, seed and SIMULATED in the header, conditional checks), `human_review.py` (kappa), `cli.py` (`variance`, `rubric-check`, `labels`, `judge`, `bias-check`, `calibrate`, `budget`, `traces`, `run --seed`), `candidates/__init__.py` (four new built-ins), `workspace.py` (`reset --code` covers Part 2 data), `playground/my_model.py` (records provider-reported tokens), `exercises/__main__.py` (Exercises 10-17), `pyproject.toml` and `__init__.py` (1.1.0, `judging` package).

**New data (all ILLUSTRATIVE or versioned):** `data/rubrics/`, `data/labels/`, `data/judges/`, `data/economics/`, `data/production/`, each with a README.

**Exercises:** stubs, tests, and reference solutions for 10-17.

**Tests:** `tests/test_probabilistic.py`, `tests/test_judges_and_operations.py` (new); `tests/test_docs.py` (exercise range, Part 2 cards, Part 2 data labels, TUTOR-PART2 links), `tests/test_cli.py`, `tests/test_workspace.py` (exercise count no longer hard-coded).

**Docs:** `TUTOR-PART2.md`, `docs/techniques.md`, `docs/sources.md`, `docs/learning-paths.md`, this file (new); README, START_HERE, TUTOR, AGENTS, `docs/grading.md`, `glossary.md`, `pm-guide.md`, `check-yourself.md`, `extending.md`, `llm-adapter.md`, `exercises/README.md`, `scripts/verify_readme_commands.sh` (changed).

Part 1's quoted outputs did not change. Scripted candidates produce the same results; the only visible differences in Part 1 reports are a kappa column in `review-summary` and the grader version (1.2), which means runs saved before this change won't `compare` with new ones until rerun.

### Test results (2026-11-24, on this branch)

| Check | Python 3.15.2 | Python 3.9.6 (macOS built-in) |
|---|---|---|
| `python3 -m unittest discover -s tests -t .` | 120 tests, OK | 120 tests, OK |
| `python3 -m exercises all --solution` | 17 of 17 pass | 17 of 17 pass |
| `python3 -m exercises all` (stubs) | 17 reported, no tracebacks | 17 reported, no tracebacks |
| `bash scripts/verify_readme_commands.sh` | all README commands as documented | all README commands as documented |
| `bash scripts/verify_fresh_clone.sh` | fresh clone verified, including after adding RC-027 | not run separately (the script uses `python3`) |

CI on GitHub (3.9, 3.11, 3.13) hasn't run for this branch yet; nothing has been pushed.

### By design

The course exists to help people learn to make evaluation decisions, not to report how real models perform. These choices serve that goal:

- **Simulated models and judges.** They are scripts whose behaviors match effects reported in research, so learners can see, measure, and reason about each effect for free. Their numbers depend on the seeds and word lists in the code and say nothing about any real model. The output labels them SIMULATED so learners practise telling teaching evidence from real evidence.
- **Invented data.** Labels, traces, prices, and volumes are ILLUSTRATIVE. Every number a learner sees is still computed from them, so changing something and rerunning really changes the result.
- **Small samples.** 64 labeled drafts, 36 traces, 26 or 27 cases. The wide 95% ranges that result are part of the lesson about uncertainty.
- **One author for labels and judges.** The labels were written from the rubric, and the judges were written separately as word lists, by the same person. That's fine for teaching; with a real system, labels come from domain experts who never see a judge's output.

### Known limitations

- **One calibrated criterion.** Only tone has labels and calibration. The reference-based "complete" judge is shown but not calibrated, and the course says so where it's used.
- **Simplified statistics.** `variance` uses a seeded bootstrap over cases for paired differences. It doesn't do power analysis, clustered errors for related cases, or multiple-comparison corrections. Kappa is unweighted, so it treats ordinal disagreements as all-or-nothing.
- **Simplified cost model.** `budget` treats each segment's rates as exact and ignores correlation between misses. It's a teaching model for trade-offs, not a forecasting tool.
- **Traces are hand-written.** The trace format is the course's own, not OpenTelemetry's (whose GenAI conventions were still in Development status when checked).
- **Live judges are tested only against a fake local server.** The provider transports were last checked against provider docs on 2026-10-06 (see `playground/my_model.py`); provider APIs and prices change.
- **Not implemented:** judge cascades, prediction-powered inference, weighted kappa, automatic contamination detection beyond exact text and word overlap, real-time monitoring.
