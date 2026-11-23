"""dupes.py - count what went out more than once.

Reads outbox/ (one file per reply or credit sent), groups by ticket, and
counts repeats: duplicate replies, duplicate credits and their dollar total,
and the model cost paid a second time for tickets that ran twice.

    python3 dupes.py
"""
import collections
import glob
import json
import os

OUTBOX = "outbox"


def main():
    files = sorted(glob.glob(os.path.join(OUTBOX, "*.json")))
    if not files:
        print("outbox/ is empty. Run run_batch.py first.")
        return
    by_ticket = collections.defaultdict(lambda: {"reply": [], "credit": []})
    for path in files:
        with open(path) as f:
            rec = json.load(f)
        by_ticket[rec["ticket_id"]][rec["type"]].append(rec)

    dup_replies = dup_credits = 0
    dup_dollars = repaid = 0.0
    half_done = []
    for tid, sent in sorted(by_ticket.items()):
        replies, credits = sent["reply"], sent["credit"]
        if len(replies) > 1:
            dup_replies += len(replies) - 1
            repaid += sum(r.get("model_cost", 0) for r in replies[1:])
        if len(credits) > 1:
            dup_credits += len(credits) - 1
            dup_dollars += sum(c["amount"] for c in credits[1:])
        if credits and len(credits) > len(replies):
            half_done.append(tid)

    print(f"outbox/: {len(files)} files for {len(by_ticket)} tickets")
    print(f"duplicate replies: {dup_replies} · duplicate credits: {dup_credits} "
          f"(${dup_dollars:.2f}) · re-paid model cost: ${repaid:.2f}")
    if half_done:
        print("credited more times than told: " + ", ".join(half_done))


if __name__ == "__main__":
    main()
