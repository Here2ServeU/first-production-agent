# Module 1 · Build an Agent That Works

> **Working is not the same as ready for production.**

A tutorial agent works on the happy path. Production is everything else.
Today you run a real agent, read every step it takes, and score it against
five questions it cannot answer yet. No changes to the agent today.

**Runtime** ~45 min · **Folder** `modules/module-1/scripts`

## What's in this folder

| File | What it is |
|------|------------|
| `run_agent.py` | The loop. Sends messages, runs tools, checks the stop reason. Read it top to bottom. |
| `tools.py` | Three tools: `lookup_customer`, `search_kb`, `route_ticket`. Fake data, no network. |
| `prompts.py` | The system prompt and the tool schemas: all the model ever sees of a tool. |
| `sim_model.py` | A free stand-in for the model. Add `--sim` and nothing costs money. |
| `samples/` | `normal.json` (a healthy ticket) and `refund.json` (a harder one). |

There is no cost tracking, no logging, no limits and no checks of any kind.
That's deliberate: it's exactly the state most first agents ship in.

## Prerequisite: set up your machine

New to Python, Git or VS Code? Watch the **[course setup playlist](https://youtube.com/playlist?list=PLJsx6ZsqoAKI&si=BvAxh4bO_ZlAWL0L)**
first. It installs everything you need for every module, on macOS and Windows.

## Build it: run your first agent

**1. Clone the course agent**

```bash
git clone https://github.com/Here2ServeU/first-production-agent && cd first-production-agent
```

**Set up a virtual environment** (a private box of packages for this project only)

```bash
python3 -m venv .venv
source .venv/bin/activate
```
```powershell
# Windows
py -m venv .venv
.venv\Scripts\Activate.ps1
```
Your prompt now starts with `(.venv)`.

**2. Install, then step into Module 1**

```bash
pip install -r requirements.txt
cd modules/module-1/scripts
```
You should see: `run_agent.py`, `tools.py`, `prompts.py`, `sim_model.py` and `samples/`.

**3. Set your API key, or use the simulator**

```bash
export ANTHROPIC_API_KEY=your-key-here   # Windows: $env:ANTHROPIC_API_KEY="your-key-here"
# no key? add --sim to every command and nothing costs money
```

**4. Run a healthy ticket**

```bash
python3 run_agent.py --input samples/normal.json --sim
```
A Pro customer can't export a report. You should see 3 tool calls,
`lookup_customer → search_kb → route_ticket`, then:
```
DECISION: reply (article #214) · steps: 3 · stop_reason: end_turn
```
Three tools, called in an order nobody wrote down. The model chose it.

**5. Read the trace**

```bash
python3 run_agent.py --input samples/normal.json --sim --trace
```
Every step: the `tool_use` (what the model asked for), the `tool_result` (what
your code sent back) and the `stop_reason` (`tool_use` = go again, `end_turn` = done).

**6. Count the steps**

```bash
python3 run_agent.py --input samples/normal.json --sim --trace | grep -c 'tool_use'
```
```powershell
(py run_agent.py --input samples/normal.json --sim --trace | Select-String 'tool_use').Count
```
Prints `3`. Write down: steps, tools used, decision.

**7. Run a harder ticket**

```bash
python3 run_agent.py --input samples/refund.json --sim --trace | grep -c 'tool_use'
```
Prints `6`: a refund on a past-due account. Same code, more steps.
The work decided the step count, not you.

**8. Score it: five questions, yes or no**

| Question | Today |
|----------|-------|
| Cost? Do you know what both runs cost? | No |
| Who? Could you prove who ran it? | No |
| Right? Was it correct, and did anything check? | No |
| Safe? What if the ticket is hostile? | No |
| Recoverable? What if it crashed at step 4? | No |

**0 / 5 is the right answer.** Keep this sheet; you fill it in again, with
evidence, in the capstone.

## Recap

* **An agent is a loop:** observe, think, act, repeat, until a stop condition you wrote. Or didn't.
* **The model asks; your code acts.** Every tool runs in your code, with your permissions.
* **The work decides the steps.** Same code, harder ticket, more steps.
* **Working is not production-ready.** Five questions, zero answers. That's the starting line.

## Exercises (before Module 2)

1. **Run both tickets** with `--trace` and save both outputs to files.
2. **Count the steps:** `tool_use` lines per run. Write down the difference and why.
3. **Read one `tool_result`:** find exactly what the model saw before it decided.
4. **Blur a description:** in `prompts.py`, make `search_kb`'s description just `"search"`. Rerun; count steps.
5. **Remove a tool:** delete `route_ticket` from the schemas. What does it do now?
6. **Draw the loop** from memory: observe, think, act, repeat, and every exit.
7. **Find the exits:** read `run_agent.py`. List every way it can stop. Is there a max?
8. **Score your own agent:** five questions, yes or no. Keep the sheet for the capstone.

## Glossary

| Term | Meaning |
|------|---------|
| Agent | A model in a loop with tools, deciding its own next step until it stops. |
| Step | One pass through the loop: usually one model call and the tool it asked for. |
| Tool schema | Name, description and arguments: all the model ever sees of a tool. |
| State | Every message so far. Sent again on every step, so it grows. |
| `tool_use` / `tool_result` | The model's request / what your code sends back. |
| Stop condition | An exit your code enforces: done, max steps, budget, error. |

**Next:** [Module 2 · Break It: The Runaway Loop](../module-2)
