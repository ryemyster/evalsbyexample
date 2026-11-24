# Sources

Where Part 2's methods come from, and how settled each one is. Links were checked on 2026-11-24. Papers get revised and guides get rewritten, so read the current version before relying on a detail. Where only a summary was available when this page was written, the entry says so.

**Status** means:

- **Established:** peer-reviewed or long-standing practice, with results others have reproduced or widely adopted.
- **Emerging:** credible and increasingly used, but recent, mostly one group's results, or still changing.
- **Disputed:** commonly repeated, but the evidence is weak or experts disagree.

## Judges and their biases

| Source | What it supports here | Status |
|---|---|---|
| Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena", NeurIPS 2023 Datasets and Benchmarks. https://arxiv.org/abs/2306.05685 | Strong model judges can agree with human preferences about as often as people agree with each other, on their tasks. Names position, verbosity, and self-enhancement bias, and proposes swapping positions. Basis for Lessons 12-13 and pairwise "both orders" counting. | Established |
| Wang et al., "Large Language Models are not Fair Evaluators", ACL 2024. https://arxiv.org/abs/2305.17926 | Changing the order of two answers can change which one a judge prefers; proposes balancing across orders and sending hard items to people. Basis for the position probe and for escalating unsure verdicts. | Established |
| Panickssery, Bowman & Feng, "LLM Evaluators Recognize and Favor Their Own Generations", NeurIPS 2024. https://arxiv.org/abs/2404.13076 | Self-preference: judges rated their own summaries above others' that people rated equal, linked to recognizing their own text. Basis for the self-preference probe and "use a judge from another family". Measured on summarization; how far it generalizes is still being studied. | Emerging |
| Dubois et al., "Length-Controlled AlpacaEval: A Simple Way to Debias Automatic Evaluators", 2024. https://arxiv.org/abs/2404.04475 | Automatic evaluators can favor longer outputs; controlling for length made results more robust to padding. Basis for the length probe. | Established (as a documented bias); the specific correction is one method among several |
| Sclar et al., "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design", ICLR 2024. https://arxiv.org/abs/2310.11324 | Small formatting changes in prompts can move results a lot, and the effect differs between models. Basis for the wording probe and "version the prompt file". | Established |
| Shi et al., "Optimization-based Prompt Injection Attack to LLM-as-a-Judge" (JudgeDeceiver), 2024. https://arxiv.org/abs/2403.17710 | Text added to a candidate answer can steer a judge's choice; some tested defenses weren't enough. Why the course says fencing helps but isn't a guarantee. | Emerging |
| Thakur et al., "Judging the Judges: Evaluating Alignment and Vulnerabilities in LLMs-as-Judges", 2024. https://arxiv.org/abs/2406.12624 | Percent agreement often fails to tell judges apart where chance-corrected measures do; judges can be lenient and sensitive to prompt length. Later versions of the paper switch from Cohen's kappa to Scott's pi. | Emerging |
| Shankar et al., "Who Validates the Validators? Aligning LLM-Assisted Evaluation of LLM Outputs with Human Preferences", UIST 2024. https://arxiv.org/abs/2404.12272 | Criteria drift: people refine what they mean by "good" while grading, so criteria and judges have to be revisited. Basis for "fix the rubric before labeling" and regular recalibration. | Emerging |
| Jung, Brahman & Choi, "Trust or Escalate: LLM Judges with Provable Guarantees for Human Agreement", ICLR 2025. https://arxiv.org/abs/2407.18370 | A judge can abstain when unsure and hand off to a stronger judge or a person, with agreement targets set for the use case. Basis for "send unsure verdicts to people" and cascades. | Emerging |

## Statistics

| Source | What it supports here | Status |
|---|---|---|
| Miller, "Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations", 2024 (Anthropic). https://arxiv.org/abs/2411.00640 | Report uncertainty with every eval score; compare models with paired, question-level differences; plan how many questions you need. Basis for `variance`. | Emerging (preprint, widely cited) |
| Brown, Cai & DasGupta, "Interval Estimation for a Binomial Proportion", Statistical Science 16(2), 2001. https://doi.org/10.1214/ss/1009213286 | The textbook interval for a rate performs poorly on small samples; recommends Wilson's interval for small n. Basis for the 95% ranges in `calibrate`. | Established |
| Cohen, "A coefficient of agreement for nominal scales", Educational and Psychological Measurement 20(1), 1960. | Cohen's kappa. Basis for agreement beyond chance in `labels` and `review-summary`. | Established |
| Landis & Koch, "The measurement of observer agreement for categorical data", Biometrics 33, 1977. | The often-quoted kappa bands ("substantial" for 0.61-0.80, and so on). The authors offered them as guidelines, and others have criticized them as opinion rather than evidence. That's why the course never says what kappa is "good enough". | Disputed (as thresholds) |
| Angelopoulos et al., "Prediction-powered inference", Science 382, 2023. https://arxiv.org/abs/2301.09633 | Combining a small human-labeled sample with many model judgments can give valid, tighter estimates. Background for Module 5's mix of judge and people; the course doesn't implement it. | Established |
| Yao et al., "τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains", ICLR 2025. https://arxiv.org/abs/2406.12045 | pass^k: the chance that all k tries succeed; agents' consistency dropped sharply as k grew. Basis for "a case passes only if every attempt passes". | Established |
| Chen et al., "Evaluating Large Language Models Trained on Code", 2021. https://arxiv.org/abs/2107.03374 | pass@k: at least one of k tries succeeds. The contrast with pass^k. | Established |

## Reproducibility and contamination

| Source | What it supports here | Status |
|---|---|---|
| Atil et al., "Non-Determinism of 'Deterministic' LLM Settings", 2024. https://arxiv.org/abs/2408.04667 | Models set up to be deterministic (temperature 0, fixed seed) still varied across runs. Why the course says temperature 0 isn't a guarantee. | Emerging |
| Horace He and Thinking Machines Lab, "Defeating Nondeterminism in LLM Inference", blog post, September 2025. | Attributes much run-to-run variation at temperature 0 to inference kernels that aren't batch-invariant. Only secondary summaries were read for this page, and no link is given because the original URL wasn't confirmed. | Emerging |
| Sainz et al., "NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination for each Benchmark", Findings of EMNLP 2023. https://aclanthology.org/2023.findings-emnlp.722 | Test data that leaks into training inflates scores, and its extent is hard to measure. Basis for split checks and the holdout rule. | Established (as a problem); detection methods are emerging |

## Production, governance, and provider guidance

| Source | What it supports here | Status |
|---|---|---|
| Breck et al., "The ML Test Score: A Rubric for ML Production Readiness and Technical Debt Reduction", IEEE Big Data 2017. https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/ | Production ML needs tests of data, model, infrastructure, and monitoring, not just the model. Background for trace checks and layer-by-layer attribution. | Established |
| NIST, "Artificial Intelligence Risk Management Framework (AI RMF 1.0)", NIST AI 100-1, 2023. https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf | Roles, responsibilities, and human oversight should be defined and documented (GOVERN), and risks measured and tracked (MEASURE). Background for the decision-rights section of the PM guide. It doesn't prescribe one organizational model. | Established |
| OpenTelemetry, "Semantic conventions for generative AI systems". https://opentelemetry.io/docs/specs/semconv/gen-ai/ | A shared vocabulary for tracing model calls and agent steps. Status "Development" when checked, so names may change. Useful if you export traces like the course's. | Emerging |
| Anthropic, "Define success criteria and build evaluations". https://platform.claude.com/docs/en/test-and-evaluate/develop-tests | Specific, measurable criteria; evals that mirror the real task mix, including edge cases; code, model, and human grading. | Provider guidance |
| Anthropic, "Demystifying evals for AI agents", engineering blog, January 2026. https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents | Agent evals combine code-based, model-based, and human graders. Only part of the text was available when this page was written. | Provider guidance |
| OpenAI, "Evaluation best practices". https://developers.openai.com/api/docs/guides/evaluation-best-practices | Models can answer the same input differently, so traditional software tests aren't enough; model graders work best on comparisons, classification, or scoring against specific criteria. The page also noted that OpenAI's hosted Evals platform was being deprecated. | Provider guidance |
| Husain, "Using LLM-as-a-Judge For Evaluation: A Complete Guide". https://hamel.dev/blog/posts/llm-judge/ | Practitioner method: a domain expert gives pass/fail judgments with written critiques, which then guide a model judge. Only summaries were available when this page was written. | Practitioner guidance |

## Reviewed but not relied on

Aakash Gupta with Mahesh Yadav, "Practical AI Evals: A FAANG PM's 4-Step Guide", Product Growth, 2026-11-24. https://www.news.aakashg.com/p/practical-ai-evals. Its advice to turn quality into yes/no tests, start with human experts, build a judge, and keep sampling the judge's output matches the sources above. Its specific numbers (a 70-80% "ceiling" for evals, a 70-80% target for judge agreement, review volumes, labeling costs) are stated without evidence, and the course doesn't use them. A target for judge agreement depends on how often problems occur, what a missed problem and a false alarm cost, and how the judge is used. The full review is in [design/extended-curriculum.md](design/extended-curriculum.md#3-review-of-the-external-reference).

## Disputed or unsettled practices, as the course treats them

- **"Binary is always better than a scale."** Binary criteria are easier to define and agree on, and are the course's default. Ordinal scales carry more information when each level is defined; the course uses one for policy reading.
- **Universal thresholds** for agreement, kappa, recall, or pass rate. The course never sets one. Every threshold lives in a file someone agreed to before seeing results, with a reason.
- **A judge's self-reported confidence.** Useful only if you measure it. `calibrate` shows how often a judge was right at high and at low confidence; that's the evidence for escalating on it.
- **Replacing people with judges.** The sources above support judges as a way to scale checking that has been calibrated against people, with people kept in the loop where the judge is weak. None of them support dropping human review altogether.
