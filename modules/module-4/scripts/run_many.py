"""run_many.py - one ticket, many runs, a tally.

Runs run_agent.py as a separate process each time, exactly as you would,
and records the decision and the exit code of every run.

    python3 run_many.py --input samples/ambiguous.json --runs 10 --sim --seed 7
"""
import argparse
import collections
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    p = argparse.ArgumentParser(description="Run one ticket many times.")
    p.add_argument("--input", required=True)
    p.add_argument("--runs", type=int, default=10)
    p.add_argument("--sim", action="store_true")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--prompt", default="v1")
    a = p.parse_args()

    tally, exits = collections.Counter(), collections.Counter()
    for i in range(1, a.runs + 1):
        cmd = [sys.executable, os.path.join(HERE, "run_agent.py"), "--input", a.input,
               "--seed", str(a.seed), "--run", str(i), "--prompt", a.prompt]
        if a.sim:
            cmd.append("--sim")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        m = re.search(r"^DECISION: (\w+)", proc.stdout, re.M)
        decision = m.group(1) if m else "none"
        tally[decision] += 1
        exits[proc.returncode] += 1
        print(f"run {i:>2} · {decision:<9} · exit {proc.returncode}")

    print()
    print(" · ".join(f"{q} {n}" for q, n in tally.most_common()))
    print(f"exit code 0 on {exits[0]} of {a.runs} runs")


if __name__ == "__main__":
    main()
