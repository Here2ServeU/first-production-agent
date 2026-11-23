# Your First Production Agent

**Course 2 · Build it. Break it. Name it.**

Companion code for *Your First Production Agent* by Emmanuel Naweji.

We build one small, honest support-ticket agent, then break it on purpose five
different ways, on your own machine, with real numbers. Nothing is fixed in this
course; that is deliberate. You leave able to **name** each failure, **measure**
it, and **point at** where it gets treated.

> Working is not the same as ready for production.

---

## The five questions

A happy-path demo can never answer these. Each module takes one and makes it hurt.

| # | Question | What breaks | Module | Your number |
|---|----------|-------------|--------|-------------|
| 1 | **Cost?** What did it cost, and what stops it? | A runaway loop | [Module 2](modules/module-2) | 40 steps in 60 s · ≈ $547 a night |
| 2 | **Who?** Who ran it, and can you prove it? | No audit trail, no identity | [Module 3](modules/module-3) | 0 / 6 audit questions answered |
| 3 | **Right?** Was the answer correct? | Can't tell if it's working | [Module 4](modules/module-4) | 3 answers in 10 runs · 90% → 70% |
| 4 | **Safe?** What if the input is hostile? | No guardrails, leaks data | [Module 5](modules/module-5) | 5 private fields + $200 credit |
| 5 | **Recoverable?** What if it dies halfway? | No checkpoint | [Module 6](modules/module-6) | 36 duplicate replies · $180 re-credited |

## Modules

| Module | Title | Folder |
|--------|-------|--------|
| 01 | Build an Agent That Works | [`modules/module-1`](modules/module-1) |
| 02 | Break It: The Runaway Loop | [`modules/module-2`](modules/module-2) |
| 03 | No Audit Trail, No Identity | [`modules/module-3`](modules/module-3) |
| 04 | Break It: Can't Tell If It's Working | [`modules/module-4`](modules/module-4) |
| 05 | No Guardrails, Leaks Data | [`modules/module-5`](modules/module-5) |
| 06 | Fails Mid-Run, No Checkpoint | [`modules/module-6`](modules/module-6) |
| 07 | **Capstone:** The Diagnosis | [`modules/capstone`](modules/capstone) |

Every module has its own complete copy of the agent under `modules/module-N/scripts/`,
so you can always come back to a clean version of any module.

---

## Before you start

### Prerequisite: install your tools first

**[▶ Watch the setup playlist](https://youtube.com/playlist?list=PLJsx6ZsqoAKI&si=BvAxh4bO_ZlAWL0L)** before Module 1. It walks you through
installing everything this course needs: Python 3, Git, VS Code, and the
course's Python package, step by step on macOS and Windows.

You need **Python 3**, **Git** and a terminal (the one inside VS Code is fine).

**macOS**

```bash
# install Homebrew first: https://brew.sh
brew install python git
brew install --cask visual-studio-code
python3 --version && git --version
```

**Windows (PowerShell)**

```powershell
winget install Python.Python.3.12
winget install Git.Git
winget install Microsoft.VisualStudioCode
py --version; git --version
```

Setup videos: [macOS](https://www.youtube.com/watch?v=8ZIiXg4XOY0&t=6s) ·
[Windows](https://www.youtube.com/watch?v=f091sbQSv7I)

## Get it running

```bash
git clone https://github.com/Here2ServeU/first-production-agent
cd first-production-agent

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt    # one dependency: the Anthropic SDK

cd modules/module-1/scripts
python3 run_agent.py --input samples/normal.json --sim
```

You should see three tool calls, then:

```
DECISION: reply (article #214) · steps: 3 · stop_reason: end_turn
```

### Real model or simulator

* **No API key? Add `--sim` to every command.** `sim_model.py` replays realistic
  model responses locally. Same agent, same loop, same tools. Free, and the
  numbers match the slides exactly.
* **Have a key?** Set it as an environment variable, never in a file in the repo,
  and drop `--sim`:

  ```bash
  export ANTHROPIC_API_KEY=your-key-here     # Windows: $env:ANTHROPIC_API_KEY="your-key-here"
  ```

  Optional: `ANTHROPIC_MODEL` picks the model (default `claude-sonnet-5-5`).

---

## How the agent works

```
ticket.json ──▶  run_agent.py (the loop)  ──▶  DECISION
                   MODEL  ⇄  TOOLS               billing / technical / account / reply
                          lookup_customer · search_kb · route_ticket
```

| File | What it is |
|------|------------|
| `run_agent.py` | The loop. About 100 lines. Sends messages, runs tools, checks the stop reason. |
| `tools.py` | The tools: plain Python over a small fake customer database. No network calls. |
| `prompts.py` | The system prompt and the JSON tool schemas the model is shown. |
| `sim_model.py` | The free local stand-in for the model (`--sim`). |
| `samples/` | The tickets. Later modules add the inputs that break it. |

The model never runs anything. It **asks** (`tool_use`); your code **acts**
(`tool_result`). Everything risky happens in your code.

## Where each failure is treated

| Symptom people report | Cause | Treated in |
|-----------------------|-------|-----------|
| The bill keeps climbing | no step cap, no budget | *The Agent Cost Problem* |
| Nobody can say who did it | no identity, no record | *Running AI Agents in Production* |
| Green lights, wrong answers | no labels, no score, no alert | *Observability for Non-Deterministic Systems* |
| The ticket gave the orders | input trusted, tools too wide | *Securing AI Agents* |
| A crash means doing it twice | no checkpoint, repeats actions | *Running AI Agents in Production* |

---

## Ground rules

* **All data is fake.** Every customer, email, phone and card number is invented.
  Keep it that way; never test these demos with real customer records.
* **Keep `--max-seconds` on** whenever you run the stuck ticket in Module 2.
* **Use `--sim`** for Modules 2 to 6 unless you deliberately want to spend money.
* Commands are shown for macOS/Linux (`python3`, `$`). On Windows use `py`, and
  each module README gives the PowerShell version.

## Repository layout

```
first-production-agent/
├── requirements.txt
├── modules/
│   ├── module-1/  README.md  scripts/   build: the working agent
│   ├── module-2/  README.md  scripts/   + meter.py, never_finishes.json
│   ├── module-3/  README.md  scripts/   + issue_credit, investigate.py
│   ├── module-4/  README.md  scripts/   + run_many.py, score.py, eval/labels.json
│   ├── module-5/  README.md  scripts/   + leak_check.py, injected.json
│   ├── module-6/  README.md  scripts/   + run_batch.py, dupes.py, batch_50.json
│   └── capstone/  README.md  diagnose.py   → writes report.md
```

---

© Emmanuel Naweji · [github.com/Here2ServeU](https://github.com/Here2ServeU)
