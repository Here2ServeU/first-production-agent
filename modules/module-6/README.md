# Module 6 · Fails Mid-Run, No Checkpoint

> **Crashing is normal. Starting over is the failure.**

The last of the five breaks. In Module 1 we wrote down a question we couldn't
answer: *what if it dies at step four?* Today we give the agent a batch of fifty
tickets, crash it on ticket 37, run it again the obvious way, and count what
that costs.

**Runtime** ~45 min · **Folder** `modules/module-6/scripts`

## What's new in this folder

| File | What it is |
|------|------------|
| `run_batch.py` | Runs the agent once per ticket in a file, in order. `--fail-at N` crashes it on purpose. |
| `samples/batch_50.json` | Fifty tickets. Four of them will get a credit. |
| `dupes.py` | Reads `outbox/` and counts what went out more than once. |
| `outbox/` | Created on the first run: one file per reply or credit sent. |

Still no checkpoint, no log and no retry logic anywhere. That's the state we're testing.

## Build it

**1. Get the course repo**

```bash
cd first-production-agent && git pull
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
```

**2. Install, then step into Module 6**

```bash
pip install -r requirements.txt
cd modules/module-6/scripts
```

**3. Look before you break it**

```bash
ls
ls samples
```
Look for a checkpoint file, or anything that records progress. There is none.

**4. Run the batch, and crash it at 37**

```bash
python3 run_batch.py --input samples/batch_50.json --fail-at 37 --sim
```
```
[1/50] T-001 reply sent
...
[36/50] T-036 reply sent
[37/50] T-037 issue_credit $40
CRASH: simulated failure at ticket 37 of 50.
```
`--fail-at 37` stops the process right after the credit on ticket 37. In real
life: a deploy, a timeout, a lost machine.

**5. See what it left behind**

```bash
ls outbox | wc -l
ls outbox | tail -3
```
```powershell
(dir outbox).Count; dir outbox | Select-Object -Last 3
```
`40` files (36 replies and 4 credits). The last three:
`0038_T-035_reply.json`, `0039_T-036_reply.json`, `0040_T-037_credit.json`.
**Ticket 37 is half-done:** credited, never told. The only sign is a missing file.

**6. Run it again, the obvious way**

```bash
python3 run_batch.py --input samples/batch_50.json --sim
```
Its first line: `[1/50] T-001`. Nothing told it where it got to, so it started from the beginning.

**7. Count the damage**

```bash
python3 dupes.py
```
```
duplicate replies: 36 · duplicate credits: 4 ($180.00) · re-paid model cost: $0.74
credited more times than told: T-037
```

**8. Score it: the fifth question**

| | |
|---|---|
| **Fragile?** | Yes: one crash lost the place for all 50 |
| **Repeating?** | Yes: 36 replies and 4 credits sent twice |
| **Inconsistent?** | Yes: T-037 credited, never told |

**Recoverable? No**, and now with three numbers: 36 replies, $180, $0.74.

To start clean again: `rm -rf outbox` (Windows: `Remove-Item -Recurse outbox`).

## Name it

* **Long jobs die.** Deploys, timeouts, lost machines. That part is just life.
* **Restart means repeat.** No checkpoint, so it starts at ticket 1, pays again and acts again.
* **Half-done is worst.** Money sent, customer never told, nothing on record.

**Treated in:** *Running AI Agents in Production*.

## Exercises (before the capstone)

1. **Crash it elsewhere:** clear `outbox/`, run with `--fail-at 5`, then `--fail-at 49`. Compare `dupes.py`.
2. **Find the half-done:** after each crash, which ticket has a credit but no reply? Is there always one?
3. **Restart twice:** crash, re-run with a crash, re-run to the end. Which numbers grow?
4. **Sort the tools:** read-only or changes something? Safe to run twice?
5. **Read `run_batch.py`:** find the exact line where progress lives. What survives the process dying?
6. **Scale it up:** a 5,000-ticket night dies at ticket 3,700. Estimate the damage.
7. **Draw three states:** done, half-done, not started. Which needs a human?
8. **Ask your own agent:** if it died right now, what would a restart repeat?

**Next:** [Capstone · The Diagnosis](../capstone)
