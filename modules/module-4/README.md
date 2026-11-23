# Module 4 · Break It: Can't Tell If It's Working

> **It ran is not the same as it was right.**

Every run exits with code 0. Nobody knows how many were right. Today you run
one ticket ten times and get three different answers, score the agent against
twenty hand-labelled tickets, and watch a one-line prompt change drop accuracy
by twenty points without a single alarm.

**Runtime** ~45 min · **Folder** `modules/module-4/scripts`

## What's new in this folder

The agent itself hasn't changed since Module 1. Three things for measuring it:

| File | What it is |
|------|------------|
| `run_many.py` | One ticket, many runs, a tally of decisions and exit codes. |
| `score.py` | Accuracy against the answer key. `--prompt v1` or `--prompt v2`. |
| `eval/labels.json` | 20 tickets, each with the queue a human chose (`expected`). |
| `samples/ambiguous.json` | "I was charged twice and now I can't log in." Genuinely unclear. |
| `prompts.py` | `v1` = the original prompt. `v2` = v1 + *"If a help article matches the question, reply with it."* |

## Build it

**1. Get the latest code**

```bash
cd first-production-agent && git pull
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**2. Step into Module 4**

```bash
cd modules/module-4/scripts && ls
```

**3. Run the ambiguous ticket once**

```bash
python3 run_agent.py --input samples/ambiguous.json --sim --seed 7
echo $?                              # Windows: $LASTEXITCODE
```
`DECISION: billing · steps: 3 · stop_reason: end_turn`, then `0`. Looks fine.
If this were the demo, you'd call it working. `--seed 7` fixes the simulator's
dice so your result matches the slides.

**4. Run it ten times and count**

```bash
python3 run_many.py --input samples/ambiguous.json --runs 10 --sim --seed 7
```
```
billing 6 · account 3 · technical 1
exit code 0 on 10 of 10 runs
```
Four of them are wrong, and nothing says so.

**5. Open the answer key**

```bash
head -n 12 eval/labels.json          # Windows: Get-Content eval/labels.json -TotalCount 12
```
Each ticket has an `id`, a `message` and the `expected` queue. Twenty is a toy;
real answer keys have hundreds and keep growing.

**6. Score the original prompt**

```bash
python3 score.py --prompt v1 --sim
```
`v1: accuracy 18/20 (90%)`, two misses, both genuinely hard tickets.
This is the first time the agent has had an accuracy number at all.

**7. Score the one-line change**

```bash
python3 score.py --prompt v2 --sim
echo $?
```
`v2: accuracy 14/20 (70%), with 4 new misses compared with v1`, and `echo $?`
still prints `0`. Twenty points gone. No error, no failed run, no alert.

**8. Write down three numbers**

| | |
|---|---|
| **3 answers** | in 10 runs of one ticket, all exit 0 |
| **90% → 70%** | accuracy, v1 to v2, one sentence apart |
| **0 alerts** | nothing noticed but the score |

*Right?* is still a **no** on your Module 1 scorecard, but now the no has evidence.

## Name it

* **Same input, different output:** a model gives a spread of answers, not one answer.
* **Exit code 0 is not success:** your system checks that the agent finished, not that it was correct.
* **The silent regression:** a helpful-sounding prompt change costs 20 points. Customers notice first.

**Treated in:** *Observability for Non-Deterministic Systems*.

## Exercises (before Module 5)

1. **Change the seed:** `--seed 1` to `--seed 5`. Does the spread ever disappear?
2. **Run it 50 times:** `--runs 50`. How close does billing get to 60%?
3. **Label five tickets** yourself, and with a colleague. Argue about the one you disagree on.
4. **Read the misses** for v2. For each of the four that flipped, one sentence on why.
5. **Write your own v3** in `prompts.py`. Predict the score, then run `score.py`.
6. **Test a normal ticket** with `run_many.py`. Is a clear ticket stable?
7. **Find the checks:** list every signal `run_agent.py` gives about a run. Which say anything about correctness?
8. **Ten runs of yours:** run one input of your own agent ten times. Count the answers.

**Next:** [Module 5 · No Guardrails, Leaks Data](../module-5)
