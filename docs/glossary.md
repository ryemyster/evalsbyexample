# Glossary

Plain-language meanings for the terms used in this course. If a word isn't here, ask your coding agent: "What does ___ mean?"

## Eval terms

| Term | Meaning |
|---|---|
| **Eval** | Short for evaluation. A repeatable test of how an AI feature behaves on a fixed set of situations, used to decide whether it's ready. |
| **Case** (test case) | One situation to test: who wrote in, what they said, what the records show, and what a good reply must and must not do. This course has 26. |
| **Case set** | All the cases together. It has a version number, so results from different sets aren't mixed up. |
| **Candidate** | A version of the assistant being tested. Here: `candidate-v1` (flawed on purpose), `candidate-v2` (improved), or your own. |
| **Baseline** | How the job gets done today, the thing a candidate has to beat. Here: saved reply templates. |
| **Draft** | The reply a candidate writes. A human agent approves or edits it before anything is sent. |
| **Resolution** (next step) | What the draft proposes to do: answer a question (`inform`), say yes to the return (`accept_return`), say no (`decline_return`), ask the customer something (`ask_customer`), or hand it to a specialist (`escalate`). |
| **Escalate** | Pass a request to a specialist because it's too risky or unusual for a normal reply. |
| **Check** | One yes/no test that code runs on every draft, such as "did it reveal another customer's data?" |
| **Severity** (how serious) | How bad a failed check is. **Critical:** one is enough to stop a launch. **Major:** the case fails. **Minor:** noted, but the case can still pass. |
| **Must-pass case** | A test case so important that if it fails, the release is blocked, whatever the overall score. |
| **Run** | One pass of a candidate over every case, saved in `runs/` so you can look at it again. |
| **Trace** | The record of every lookup or action a candidate tried. It shows things the reply text doesn't, like an attempted refund. |
| **Human review / scorecard** | A spreadsheet where people who do the job rate drafts on things code can't judge, like "could an agent send this as is?" |
| **Release gate** | A rule agreed before testing that decides whether a candidate can move forward, such as "zero critical failures". |
| **Supervised pilot** | A small, careful trial with real customers, where support agents use the drafts and a person checks every reply before it's sent. It measures things tests can't, like time saved. |
| **Decision brief** | A one-page summary for a team: what you recommend, the evidence, and who is responsible for what. |
| **Rollback** | Switching a feature off and going back to the old way, for example after a serious mistake. |
| **Offline eval** | Testing on saved cases, before real customers are involved. It shows whether drafts are correct, not whether the job got easier. |
| **Regression case** | A case added after a real failure, so the same failure can't come back unnoticed. |
| **Illustrative** | Made up for teaching. The pilot data and reviewer ratings here are illustrative, not real results. |
| **Median** | The middle value: half the results are below it and half above. Used for time per ticket, because one very slow ticket would distort an average. |
| **Deterministic / probabilistic** | A deterministic candidate gives the same answer to the same input every time (the course's scripts). A probabilistic one, like a language model, can answer differently each time, so you test it several times. |
| **Simulated model / judge** | A script with built-in randomness or known flaws that behaves like a model, so you can practise for free. Not a language model; its numbers are teaching output. |
| **Seed** | The number that decides a simulated model's dice rolls. Same seed, same results. |
| **95% range (confidence interval)** | The range the real value probably lies in, given how few cases or runs you have. If the range for a difference includes 0, you can't tell the versions apart. |
| **pass@k / pass^k** | pass@k: right at least once in k tries. pass^k: right every time in k tries. A support assistant needs the second. |
| **Structured output** | A reply in an agreed format (here, JSON with named fields) so code can read it. |
| **Rubric** | The written criteria raters use. A good one says what a rater would see in the reply, what each value means, and who grades it. |
| **Binary / ordinal / continuous** | Two values (ok/problem); ordered levels (correct/debatable/incorrect); a measured number (minutes). |
| **Reference-based / reference-free** | Graded against something (the expected behavior, the record) or on the reply alone (tone). |
| **Kappa (Cohen's kappa)** | Agreement between two raters beyond what chance would give. 1 = always agree, 0 = no better than chance. |
| **Annotation / adjudication** | Labeling drafts; and settling disagreements between labelers by discussion, with a written reason. |
| **Judge (LLM-as-judge)** | A model that grades drafts against a written criterion. A grader, so it must be checked against people. |
| **Pointwise / pairwise** | Grading one reply at a time, or picking the better of two. |
| **Calibration (of a judge)** | Measuring a judge against people's labels to learn what it catches and misses. |
| **Train / calibration / holdout split** | Labeled drafts kept apart: examples you may show the judge; drafts to tune on; drafts used once at the end for a fair estimate. |
| **Contamination / leakage** | When test material leaks into what's being tuned or trained, so scores look better than they are. |
| **Precision / recall** | Of the drafts a judge flagged, how many were real problems; of the real problems, how many it flagged. |
| **False acceptance / false rejection** | A missed problem (passed though bad); a false alarm (flagged though fine). |
| **Position / verbosity / self-preference bias** | A judge favoring the reply shown first; the longer reply; or text from its own model family. |
| **Prompt injection** | Text inside content (a customer message, a reply) that tries to give a model instructions. |
| **Trace / trajectory** | The record of every step a request went through; the path as a whole. |
| **Failure attribution** | Working out which layer caused a failure: model, orchestration, policy, data, evaluator, or human review. |
| **Shadow / canary** | Running a new version on real requests without showing its output to anyone; or showing it on a small share of real requests. |
| **Distribution shift** | Real traffic that differs from what you tested on, like much longer messages. |
| **Drift** | Results changing over time without anyone changing the code, for example after a provider updates a model. |
| **n / N, e.g. 13 / 26 (50%)** | How many out of how many. The course always shows both numbers, because "50%" means something different with 2 cases than with 2,000. |

## Store and job terms

| Term | Meaning |
|---|---|
| **Product manager (PM)** | The person at a company who decides what a product should do and whether a feature is ready. This course puts you in that role. |
| **Launch / release** | Switching a feature on for real users. |
| **Customer support agent** | A person whose job is answering customers' questions and problems. |
| **Ticket** | One customer request that the support team has to handle. |
| **Return** | Sending something you bought back to the store. A **return label** is the prepaid shipping label for it. |
| **Refund** | Money the store gives back. Here, it's sent after the returned item is checked (inspected). |
| **Policy** | The store's written rules, such as "returns are accepted within 30 days". |
| **Final sale** | An item that can't be returned. |
| **Chargeback** | When a customer asks their bank to take a payment back from the store. Stores treat it as serious. |

## Computer terms

| Term | Meaning |
|---|---|
| **Terminal** | A window where you type commands instead of clicking. Your coding agent can run commands for you. |
| **Command** | One line of text that tells the computer to do something, such as `python3 -m returns_eval cases`. |
| **Python** | The programming language this course is written in. You need it installed (version 3.9 or newer; most Macs already have it), but you don't need to write it. |
| **Coding agent** | An AI assistant that can read files in a folder and run commands, with your permission. |
| **Repository (repo)** | The folder of files that makes up this course. |
| **git** | A tool that tracks changes to files. It lets you undo changes; you don't need to learn it. |
| **JSON / JSONL** | Plain-text formats for structured data. Each test case is stored as JSON. JSONL means one JSON item per line. |
| **API key** | A password-like code that lets a program use an online AI service. Only needed if you choose to test your own model. |
| **Environment variable** | A setting you give a program before it runs, such as an API key. Mac/Linux: `export NAME=value`. Windows PowerShell: `$env:NAME="value"`. |
