# Start here (no coding needed)

This is a hands-on course on **evals**: how a product team tests an AI feature before deciding to launch it. You'll work through one example, an AI assistant that drafts replies to customers who want to return something, and make the product calls yourself.

You don't need to know how to code. A **coding agent** does the typing and runs the commands. You make the decisions: what counts as a failure, what a good reply looks like, and whether the feature is ready.

## What you need

- **A computer** (Mac, Windows, or Linux).
- **A coding agent**: an AI assistant that can open a folder on your computer, read the files, and run commands in it. Claude Code, Cursor, GitHub Copilot, and Codex are examples. If you already use one at work, use that one. Check your organization's rules first.
- **This repository**, downloaded to your computer (step 1).

You don't need an API key or any paid service beyond your coding agent. Everything in the course runs on your computer, and every customer, order, and result in it is made up.

## Step 1: Download the repository

**Easiest:** on the repository's GitHub page, click the green **Code** button, then **Download ZIP**. Unzip it somewhere you'll find it again, such as your Documents folder.

**Or, if you use git:** `git clone https://github.com/YOUR-USERNAME/evalsbyexample.git`

## Step 2: Open the folder in your coding agent

Open your coding agent and point it at the folder you just unzipped (usually called `evalsbyexample` or `evalsbyexample-main`). In most tools that means **File → Open Folder**, or starting the agent from inside that folder.

## Step 3: Say hi

In your coding agent's chat, type **hi** and press Enter.

Your agent should reply with something like "Hi! Let's learn evals together." and lead you from there. The folder contains instructions most coding agents read automatically (`AGENTS.md`, plus `CLAUDE.md` for Claude Code), so there's nothing to set up. If the agent asks whether you trust this folder, say yes. In Claude Code, that dialog also lists the course commands it will run without asking each time; they only work inside this folder.

**Using Claude Code in a terminal?** Start it from inside the folder with `claude "hi"` and it greets you right away.

**If your agent doesn't start the course** (some don't read those files automatically), paste this prompt instead:

```text
I'm a product manager learning how to evaluate AI features. I don't know how to code.
This folder is a hands-on course called "Evals by example".

Please be my tutor:
1. Read TUTOR.md in this folder and follow it. It explains how to guide me.
2. Check that my computer is ready, and help me fix anything that's missing.
3. Then walk me through the course one step at a time, in plain language.

I want to make the product decisions myself. You do the typing and run the commands.
Explain what happened, then wait for me before moving on.
```

**Coming back later?** Open the folder again and say hi. The agent checks your notes and offers to pick up where you left off.

## What to expect

- **You may be asked to approve commands or file edits.** That's normal. The course commands start with `python3 -m returns_eval` or `python3 -m exercises` (on Windows, `py` instead of `python3`), and they only read and write files inside this folder. Claude Code runs them without asking once you trust the folder; other agents may ask each time, and most offer an "allow for this session" option. If you're unsure about something, ask the agent what it does before you approve it.
- **You don't need to set anything up.** The course needs Python 3.9 or newer, which most Macs already have. If your computer needs it (common on Windows), your agent asks first: it can install it for you, show you how to do it yourself, or skip ahead if you've got it handled. On a Mac, a window may ask to install "command line developer tools": click Install. Nothing else gets installed.
- **You'll be asked questions.** "Would you approve this draft?" "What should block a launch?" There's often no single right answer. The point is to practice the judgment.
- **It's split into lessons.** You can do a quick tour in one sitting, or the full course over a few sessions.
- **You can't break anything permanently.** The agent can put any file back the way it started, and it saves a copy of your version first.

## If you'd rather do it yourself

The [README](README.md) has every command and the full walkthrough. [docs/glossary.md](docs/glossary.md) explains the terms in plain language.

## Need help, or want to learn more?

Want help applying this to an AI feature at your company, or have questions about the course? Contact [Ascendvent](https://ascendvent.life).
