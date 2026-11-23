"""score.py - accuracy against the answer key.

Runs the agent once on each hand-labelled ticket in eval/labels.json and
compares its decision with the queue a human chose.

    python3 score.py --prompt v1 --sim
    python3 score.py --prompt v2 --sim
"""
import argparse
import json
import os

import run_agent

HERE = os.path.dirname(os.path.abspath(__file__))


def score(labels, prompt, sim):
    decisions = {}
    for t in labels:
        ticket = {k: t[k] for k in ("id", "customer_id", "message")}
        r = run_agent.run(ticket, sim=sim, prompt=prompt, say=lambda *_: None)
        decisions[t["id"]] = r["decision"]
    return decisions


def main():
    p = argparse.ArgumentParser(description="Score the agent against labels.")
    p.add_argument("--prompt", default="v1", choices=sorted(run_agent.PROMPTS))
    p.add_argument("--sim", action="store_true")
    p.add_argument("--labels", default=os.path.join(HERE, "eval", "labels.json"))
    a = p.parse_args()

    with open(a.labels) as f:
        labels = json.load(f)
    got = score(labels, a.prompt, a.sim)
    right = [t for t in labels if got[t["id"]] == t["expected"]]
    misses = [t for t in labels if got[t["id"]] != t["expected"]]

    print(f"prompt {a.prompt}: {run_agent.PROMPTS[a.prompt][-60:]!r}")
    print("misses:")
    for t in misses:
        print(f"  {t['id']}  expected {t['expected']:<9} got {got[t['id']]:<9} "
              f"{t['message'][:50]}")

    line = (f"{a.prompt}: accuracy {len(right)}/{len(labels)} "
            f"({100 * len(right) // len(labels)}%)")
    if a.prompt != "v1":
        base = score(labels, "v1", a.sim)
        flipped = [t for t in misses if base[t["id"]] == t["expected"]]
        line += f", with {len(flipped)} new misses compared with v1"
    print(line)
    # Note what is NOT here: no threshold, no failure, no alert. Exit code 0.


if __name__ == "__main__":
    main()
