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
