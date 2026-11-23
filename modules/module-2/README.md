# Module 2 · Break It: The Runaway Loop

> **An agent with no limits has no maximum bill.**

One ordinary ticket, one helpful error message, and a loop with only one exit,
which never comes. We run it for 60 seconds with a safety switch on, measure
it, and do the arithmetic for a whole night. We don't fix it.

**Runtime** ~45 min · **Folder** `modules/module-2/scripts`

## What's new in this folder

| File | What it is |
|------|------------|
| `samples/never_finishes.json` | Customer C-7731 asks about a double charge. Nothing odd in it. |
| `meter.py` | Reads a `--trace` and prices every step: $3 per million tokens in, $15 per million out. |
| `--max-seconds` | The lab safety switch in `run_agent.py`. **Always on** for the stuck ticket. |

The trap isn't in the ticket. It's in what `lookup_customer` answers for this
customer, every single time: *"temporarily unavailable, please retry."*

## Build it: break it yourself

**1. Update the repo, step back into the box**

```bash
cd first-production-agent && git pull
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**2. Step into Module 2**

```bash
cd modules/module-2/scripts
```

**3. Meter a healthy ticket first**

```bash
python3 run_agent.py --input samples/normal.json --sim --trace | python3 meter.py
```
You should see: `TOTAL: 3 steps · $0.021 · stop_reason: end_turn`. That's your baseline.

**4. Read the ticket that never closes**

```bash
cat samples/never_finishes.json      # Windows: type samples\never_finishes.json
```

**5. Run it, with the safety switch on**

```bash
python3 run_agent.py --input samples/never_finishes.json --sim --trace --max-seconds 60
```
`lookup_customer` → "temporarily unavailable, please retry", over and over, until
`STOPPED: --max-seconds 60 reached`.

> **Never remove `--max-seconds`.** Without it nothing stops this run: not the
> agent, not the model, not the tool. The switch is a lab fuse, not a fix.

**6. Save the run, count the steps**

```bash
python3 run_agent.py --input samples/never_finishes.json --sim --trace --max-seconds 60 > runaway.log
grep -c 'tool_use' runaway.log
```
```powershell
(Select-String 'tool_use' runaway.log).Count
```
A quiet terminal for 60 seconds, then: `40`. The healthy ticket took 3.

**7. Put a price on it**

```bash
python3 meter.py < runaway.log       # Windows: Get-Content runaway.log | py meter.py
```
```
  step 1       1,900    60     $0.007    $0.007
  ...
 step 40      13,500    60     $0.041    $0.960
TOTAL: 40 steps · $0.96 · stopped by --max-seconds
```
The same request every step; seven times the tokens by the end.

**8. Extrapolate to one night (10:30 pm to 8 am)**

```bash
python3 meter.py --hours 9.5 --seconds 60 < runaway.log
```
`9.5 h at this rate ≈ $547, for one ticket.` And that's a **floor**: every later
minute sends more tokens than the one before.

## The numbers

| | Healthy ticket | Stuck ticket |
|---|---|---|
| Steps | 3 | 40 in the first minute |
| Cost | $0.021 | $0.96 a minute → ≈ $547 a night |

A quiet night of 500 healthy tickets costs about $10.50. One stuck ticket costs
about fifty times more than all of them together. An average hides it; only a
per-ticket number shows it.

Input per step grows in a straight line (~300 tokens a retry), so the total
grows **superlinearly**: the first 20 steps cost $0.30, the next 20 cost $0.66.

## Name it: a runaway loop

| Property | Meaning |
|----------|---------|
| **Unbounded** | Nothing caps it. No max steps, no budget, no retry limit. Only `end_turn`, which never came. |
| **Invisible** | Nobody sees it happen. No meter, no alert. The first signal is the invoice. |
| **Unattributed** | Nobody can pin it. One bill for the account; no run id, no per-ticket cost, no owner. |

**Treated in:** *The Agent Cost Problem*. Named here, measured here, fixed there.

## Exercises (before Module 3)

1. **Meter both tickets:** `normal.json` and `refund.json` through `meter.py`. Your healthy range.
2. **Find the retry:** in `tools.py`, find where C-7731 is handled. Read the exact words.
3. **Halve the window:** `--max-seconds 30`. Is the cost half? Explain why not in one sentence.
4. **Sketch the climb:** input tokens per step vs running total. Which is a line, which a curve?
5. **Change the words:** make the error say only "temporarily unavailable". Rerun with the switch on. Did the wording change what the model did?
6. **Price your night:** `meter.py --hours H --seconds 60` with your own H.
7. **Find the brakes:** list every line in `run_agent.py` that can stop the loop.
8. **Ask your own agent:** what stops it at 3 a.m.? Keep the answer for the capstone.

**Next:** [Module 3 · No Audit Trail, No Identity](../module-3)
