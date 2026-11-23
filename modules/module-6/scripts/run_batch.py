"""run_batch.py - run the agent once per ticket in a file, in order.

    python3 run_batch.py --input samples/batch_50.json --sim
    python3 run_batch.py --input samples/batch_50.json --fail-at 37 --sim

--fail-at N kills the process on purpose during ticket N, right after its
first action that leaves the building (a credit, or a reply). In real life:
a deploy, a timeout, a lost machine.

Notice what this file does not have: a checkpoint. Progress lives in one
variable, in memory, and dies with the process.
"""
import argparse
import json
import sys

import run_agent
import tools

PRICE_IN = 3.00 / 1_000_000
PRICE_OUT = 15.00 / 1_000_000


def main():
    p = argparse.ArgumentParser(description="Run the agent over a batch of tickets.")
    p.add_argument("--input", required=True)
    p.add_argument("--sim", action="store_true")
    p.add_argument("--max-seconds", type=float, default=120)
    p.add_argument("--fail-at", type=int, help="crash on purpose during ticket N")
    a = p.parse_args()

    with open(a.input) as f:
        batch = json.load(f)
    total = len(batch)
    state = {"n": 0, "sent": [], "reply_path": None}

    def on_send(kind, record, path):
        if kind == "credit":
            state["sent"].append(f"issue_credit ${record['amount']:.0f}")
        else:
            state["sent"].append("reply sent")
            state["reply_path"] = path
        if a.fail_at == state["n"]:
            print(f"[{state['n']}/{total}] {record['ticket_id']} " + " · ".join(state["sent"]))
            print(f"CRASH: simulated failure at ticket {state['n']} of {total}.")
            sys.exit(1)

    tools.ON_SEND.append(on_send)

    for i, ticket in enumerate(batch, 1):          # <- progress lives here, in memory
        state.update(n=i, sent=[], reply_path=None)
        tools.CURRENT.update(ticket_id=ticket["id"], customer_id=ticket["customer_id"])
        r = run_agent.run(ticket, sim=a.sim, max_seconds=a.max_seconds,
                          say=lambda *_: None)
        cost = sum(i_ * PRICE_IN + o * PRICE_OUT for i_, o in r["calls"])
        if state["reply_path"]:                     # tag the reply with what it cost
            with open(state["reply_path"]) as f:
                rec = json.load(f)
            rec["model_cost"] = round(cost, 6)
            with open(state["reply_path"], "w") as f:
                json.dump(rec, f, indent=2)
        print(f"[{i}/{total}] {ticket['id']} " + (" · ".join(state["sent"]) or "routed"))
    print(f"done: {total} tickets")


if __name__ == "__main__":
    main()
