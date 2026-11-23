# Module 3 · No Audit Trail, No Identity

> **If you cannot say who did it, you cannot defend it.**

The agent gets a fourth tool, `issue_credit`, and can now move money. It works
perfectly. Three weeks later finance asks six questions about a $50 credit, and
nobody can answer one of them: the agent never wrote anything down, and it used
the same key as everyone else.

**Runtime** ~45 min · **Folder** `modules/module-3/scripts`

## What's new in this folder

| File | What it is |
|------|------------|
| `tools.py` | Now has `issue_credit`, which writes to a fake billing ledger (`ledger.jsonl`). |
| `samples/credit_request.json` | Customer C-2208 thinks they were charged twice in March. |
| `investigate.py` | Searches `logs/`, saved output and the ledger, then asks the six audit questions. |

## Build it

**1. Get the Module 3 changes**

```bash
cd first-production-agent && git pull
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**2. Step into Module 3**

```bash
cd modules/module-3/scripts
```

**3. Set the one key everything uses**

```bash
export SUPPORT_API_KEY=demo-shared-key     # fake; the README value
```
```powershell
$env:SUPPORT_API_KEY="demo-shared-key"
```
`tools.py` sends this key to the fake billing system with every credit. The
agent, the nightly script and both engineers in our story all use exactly this
value. **That is the problem we are measuring.**

**4. Run the credit ticket**

```bash
python3 run_agent.py --input samples/credit_request.json --sim --trace
```
You should see 4 tool calls:
`lookup_customer → search_kb → issue_credit(C-2208, 50.00) → route_ticket`, then
`DECISION: reply · steps: 4 · stop_reason: end_turn`.
Read the `issue_credit` step carefully. In a moment, that terminal output is all the evidence there is.

**5. Close the window, then look for the record**

Open a new terminal, activate `.venv`, go back to `modules/module-3/scripts`:

```bash
ls logs/            # Windows: dir logs
```
`ls: cannot access 'logs/': No such file or directory`. The run you watched left no trace on disk.

**6. Check who the caller was**

```bash
env | grep KEY      # Windows: gci env:*KEY*
```
`SUPPORT_API_KEY=demo-shared-key` (plus `ANTHROPIC_API_KEY` if you set one).
The key can't tell you: an agent name, a version, or "on behalf of" whom.

**7. Run the investigation**

```bash
python3 investigate.py --customer C-2208
```
```
found: credit $50.00 · C-2208 · created_by: SUPPORT_API_KEY

1 who triggered it?          UNKNOWN
2 which agent / version?     UNKNOWN
3 which prompt?              UNKNOWN
4 what did the model see?    UNKNOWN
5 why did it decide?         UNKNOWN
6 when, exactly?             UNKNOWN

answered: 0 / 6
```

**8. Score it: six questions, yes or no**

Who? Agent? Prompt? Inputs? Why? When? **= 0 / 6.** Then pick the last action
your own agent took (anything that changed something) and try to answer all six
from what it left behind. Logging what the code is doing isn't the same as
recording who asked for an action, and why.

## Three kinds of trace

| | What it is | What happens to it |
|---|---|---|
| **stdout** | What scrolled past your terminal | Gone when the window closes |
| **A log** | What the code was doing | Useful to engineers; rarely says who or why |
| **An audit trail** | Who acted, on whose behalf, with what inputs, why, and when | What finance, auditors and on-call actually need |

## Name it

* **Nobody in particular:** one shared key for the agent, the scripts and the engineers. Every caller looks the same.
* **Nothing on paper:** output scrolls past and vanishes. Six questions, zero answers.

**Treated in:** *Running AI Agents in Production* (identity, records, recovery).

## Exercises (before Module 4)

1. **Run it, then lose it:** close the terminal. What's left that proves the credit happened?
2. **Read the ledger line** in `ledger.jsonl`. Which of the six questions does each field answer?
3. **Count the key holders:** pick one credential on your team. List everything that uses it.
4. **Imagine revoking it:** what stops working? How long to recover?
5. **Write one record** on paper: who, what, when, why, inputs, version for the $50 credit.
6. **Draw the three traces:** stdout, a log, an audit trail.
7. **Read `investigate.py`:** where does it look? Is there anywhere else an answer could be?
8. **Score your own agent:** six questions about its last action. Keep the sheet.

**Next:** [Module 4 · Break It: Can't Tell If It's Working](../module-4)
