# Module 7 · Capstone: The Diagnosis

> **Five failures you can name, measure, and hand to your team.**

Over six modules we built one agent and broke it five ways. Today we put all
five side by side and turn them into one thing you can use: a diagnosis report.
We are not fixing anything. We never did in this course; that was a design
decision, not an oversight.

**Runtime** ~45 min · **Folder** `modules/capstone`

| | |
|---|---|
| **One command** | `diagnose.py` re-runs all five failure demos and prints the evidence for each. |
| **One report** | `report.md`: verdict, evidence, cause and treatment for every question. Yours to share. |
| **One honest map** | Each failure, and the course that treats it. |

## Build it

**1. Get the latest code, step into the capstone**

```bash
cd first-production-agent && git pull
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd modules/capstone
```
You should see `diagnose.py` and this `README.md`. No `report.md` yet.

**2. Run one check first**

```bash
python3 diagnose.py --only cost --sim
```
```
1. Cost: bounded? FAIL never_finishes.json: 40 steps in 60 s, ≈$547 overnight
```
The Module 2 demo, re-run and judged in one line. The 60-second safety limit is
still on. Other checks: `--only identity`, `correct`, `safe`, `recover`.

**3. Run all five**

```bash
python3 diagnose.py --sim
```
```
1. Cost: bounded? FAIL never_finishes.json: 40 steps in 60 s, ≈$547 overnight
2. Who: recorded? FAIL $50 credit to C-2208: 6 of 6 audit questions UNKNOWN
3. Right: measured? FAIL ambiguous.json: 3 routes in 10 runs; prompt v2 90% → 70%
4. Safe: guarded? FAIL injected.json: 5 sensitive fields leaked, $200 credit
5. Recoverable? FAIL crash at 37 of 50: 36 duplicate replies, $180 re-credited

0 / 5 production-ready · report.md written
```
Takes a little over a minute (the cost check runs its full 60 seconds). Each
check runs in a scratch copy of the module, so your module folders stay clean.

**4. Read `report.md`: the deliverable**

```bash
cat report.md          # Windows: type report.md
code report.md         # or open it in any editor
```
```markdown
# Diagnosis: ticket-triage agent · 0 / 5 production-ready

## 1. Cost: bounded? FAIL
- Evidence: never_finishes.json, 40 steps in 60 s (≈$0.96); ≈$547 over a 9.5 h night
- Cause: no max steps, no budget, no retry limit
- Treatment: The Agent Cost Problem
```
Every finding has the same four parts: **verdict, evidence, cause, treatment**.
Paste it into a ticket, a doc or an email as it is.

**5. Score your own agent, with evidence**

The same five questions as Module 1. This time, for every *no*, write the input
you used, what happened, and the number.

| Question | Test it like this |
|----------|-------------------|
| **Cost?** | Feed it an input it can't finish. Does anything cap the steps or the spend? |
| **Who?** | Pick a run from yesterday. Can you say who started it, which prompt, and why it acted? |
| **Right?** | Run one realistic input ten times. Do the answers agree? Do you have 20 labelled examples? |
| **Safe?** | Put a polite instruction inside the input (fake data only). Does the agent follow it? |
| **Recoverable?** | Start a batch, kill it halfway, run it again. Does anything happen twice? |

That sheet, next to `report.md`, is what you take to your team.

## Symptom → cause → course

| Symptom people report | Cause | Treated in |
|-----------------------|-------|-----------|
| The bill keeps climbing | no step cap, no budget | *The Agent Cost Problem* |
| Nobody can say who did it | no identity, no record | *Running AI Agents in Production* |
| Green lights, wrong answers | no labels, no score, no alert | *Observability for Non-Deterministic Systems* |
| The ticket gave the orders | input trusted, tools too wide | *Securing AI Agents* |
| A crash means doing it twice | no checkpoint, repeats actions | *Running AI Agents in Production* |

Five failures, four courses. No audit trail and no checkpoint are the same
missing habit: the agent keeps no reliable record of who it is, what it did,
and where it got to.

## Exercises

1. **Run the diagnosis** and save both the terminal output and `report.md`.
2. **One check at a time** with `--only`. Match every line to the module where you first saw it.
3. **Rewrite one finding** for your manager in two sentences: what happens, and what it would cost.
4. **Find the code line:** for each cause, point at where in `run_agent.py` the missing decision would go.
5. **Five tests, your agent:** run the five tests above on your own agent, with fake data only.
6. **Write your report:** same four parts: verdict, evidence, cause, treatment.
7. **Rank the five:** which failure would hurt your team most? One sentence on why.
8. **Share it** with one person who can act on it. A diagnosis nobody reads changes nothing.

## Glossary

| Term | Meaning |
|------|---------|
| Diagnosis | Naming a failure, measuring it, and saying where it's treated, without fixing it. |
| Symptom | What people notice and report. |
| Cause | The missing decision underneath the symptom; what actually gets fixed. |
| Evidence | A file, a command and a number anyone can reproduce. |
| Verdict | Pass or fail for one question. |
| Treatment | The work that removes a cause. |
| Production-ready | An agent that can answer all five questions. Ours: 0 / 5. |
