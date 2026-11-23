"""meter.py - put a price on a run, step by step.

Reads a --trace from stdin and prices every model call:
$3 per million input tokens, $15 per million output tokens.

    python3 run_agent.py --input samples/normal.json --sim --trace | python3 meter.py
    python3 meter.py < runaway.log
    python3 meter.py --hours 9.5 --seconds 60 < runaway.log
"""
import argparse
import re
import sys

PRICE_IN = 3.00 / 1_000_000     # dollars per input token
PRICE_OUT = 15.00 / 1_000_000   # dollars per output token
TOKENS = re.compile(r"^\[(step \d+|final)\] tokens in=([\d,]+) out=([\d,]+)")


def main():
    p = argparse.ArgumentParser(description="Price a --trace, step by step.")
    p.add_argument("--hours", type=float, help="extrapolate this rate to H hours")
    p.add_argument("--seconds", type=float, help="how long the saved run lasted")
    a = p.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    lines = sys.stdin.read().splitlines()
    steps = sum(1 for line in lines if "· tool_use:" in line)
    stopped = any(line.startswith("STOPPED:") for line in lines)

    total = 0.0
    print(f"{'call':>8}  {'tokens in':>10}  {'out':>4}  {'this call':>9}  {'running':>8}")
    for line in lines:
        m = TOKENS.match(line)
        if not m:
            continue
        label = m.group(1)
        tin, tout = int(m.group(2).replace(",", "")), int(m.group(3).replace(",", ""))
        cost = tin * PRICE_IN + tout * PRICE_OUT
        total += cost
        print(f"{label:>8}  {tin:>10,}  {tout:>4}  {'$' + format(cost, '.3f'):>9}  "
              f"{'$' + format(total, '.3f'):>8}")

    if not steps and not total:
        sys.exit("No trace found. Pipe in the output of run_agent.py --trace.")
    end = "stopped by --max-seconds" if stopped else "stop_reason: end_turn"
    print(f"TOTAL: {steps} steps · ${total:.3f}" if total < 0.1
          else f"TOTAL: {steps} steps · ${total:.2f}", f"· {end}")

    if a.hours:
        if not a.seconds:
            sys.exit("Add --seconds: how long did the saved run last?")
        night = total / a.seconds * 3600 * a.hours
        print(f"{a.hours:g} h at this rate ≈ ${night:,.0f}, for one ticket. "
              "That is a floor: every later step sends more tokens than the last.")


if __name__ == "__main__":
    main()
