# Glossary

Plain-language meanings for the terms used in this course.

## Eval terms

| Term | Meaning |
|---|---|
| **Eval** | A repeatable test of how a product behaves on a fixed set of situations, used to make a product decision. |
| **Case** (test case) | One situation to test: who wrote in, what they said, what the records show, and what a good reply must and must not do. This course has 26. |
| **Case set** | All the cases together. It has a version number, so results from different sets aren't mixed up. |
| **Candidate** | A version of the assistant being tested. Here: `candidate-v1` (flawed on purpose), `candidate-v2` (improved), or your own. |
| **Baseline** | How the job gets done today, the thing a candidate has to beat. Here: saved reply templates. |
| **Draft** | The reply a candidate writes. A human agent approves or edits it before anything is sent. |
| **Resolution** | What the draft proposes to do: answer a question, accept or decline a return, ask the customer something, or hand it to a specialist (escalate). |
| **Check** | One yes/no test that code runs on every draft, such as "did it reveal another customer's data?" |
| **Severity** | How bad a failed check is. **Critical:** blocks launch on its own. **Major:** the case fails. **Minor:** noted, but the case can still pass. |
| **Run** | One pass of a candidate over every case, saved in `runs/` so you can look at it again. |
| **Trace** | The record of every lookup or action a candidate tried. It shows things the reply text doesn't, like an attempted refund. |
| **Human review / scorecard** | A spreadsheet where support experts rate drafts on things code can't judge, like "could an agent send this as is?" |
| **Release gate** | A rule agreed before testing that decides whether a candidate can move forward, such as "zero critical failures". |
| **Supervised pilot** | A small, real trial where agents use the drafts and a human approves every reply. It measures outcomes such as time saved. |
| **Offline eval** | Testing on saved cases, before real customers are involved. It shows whether drafts are correct, not whether the job got easier. |
| **Regression case** | A case added after a real failure, so the same failure can't come back unnoticed. |
| **Illustrative** | Made up for teaching. The pilot data and reviewer ratings here are illustrative, not real results. |

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
