"""investigate.py - try to answer the six audit questions about a credit.

It looks in every place an answer could be:
  logs/                 anything the agent wrote down
  *.log in this folder  saved terminal output
  ledger.jsonl          the fake billing system's record of credits

    python3 investigate.py --customer C-2208
"""
import argparse
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# Each question, and the evidence that would answer it if anyone had recorded it.
QUESTIONS = [
    ("who triggered it?", ["triggered_by", "on_behalf_of", "user"]),
    ("which agent / version?", ["agent", "agent_version"]),
    ("which prompt?", ["prompt_version", "prompt_id"]),
    ("what did the model see?", ["tool_results", "model_input"]),
    ("why did it decide?", ["reason", "decision_reason"]),
    ("when, exactly?", ["timestamp", "run_id"]),
]


def load_records(customer):
    records, seen = [], []
    logs = os.path.join(HERE, "logs")
    if os.path.isdir(logs):
        files = glob.glob(os.path.join(logs, "*"))
        seen.append(f"logs/ ............... {len(files)} files")
        for path in files:
            records += _jsonl(path, customer)
    else:
        seen.append("logs/ ............... missing")
    saved = glob.glob(os.path.join(HERE, "*.log"))
    seen.append(f"saved output (*.log)  {len(saved) or 'none'}")
    for path in saved:
        records += _jsonl(path, customer)
    ledger = os.path.join(HERE, "ledger.jsonl")
    lines = _jsonl(ledger, customer) if os.path.exists(ledger) else []
    seen.append(f"ledger.jsonl ........ {len(lines)} line(s) for {customer}")
    return records + lines, lines, seen


def _jsonl(path, customer):
    out = []
    with open(path, errors="ignore") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict) and rec.get("customer_id") == customer:
                out.append(rec)
    return out


def main():
    p = argparse.ArgumentParser(description="Investigate a credit.")
    p.add_argument("--customer", required=True)
    a = p.parse_args()

    records, ledger, seen = load_records(a.customer)
    print("searched:")
    for s in seen:
        print("  " + s)
    credits = [r for r in ledger if r.get("type") == "credit"]
    if not credits:
        print(f"\nno credit found for {a.customer}. "
              "Run the credit ticket first (step 4 in the README).")
        return
    c = credits[-1]
    print(f"\nfound: credit ${c['amount']:.2f} · {a.customer} · "
          f"created_by: {c.get('created_by', 'UNKNOWN')}")
    if len(credits) > 1:
        print(f"       ({len(credits)} identical credit lines; nothing tells them apart)")
    print()
    answered = 0
    for n, (question, fields) in enumerate(QUESTIONS, 1):
        answer = next((str(r[f]) for r in records for f in fields if r.get(f)), None)
        answered += answer is not None
        print(f"{n} {question:<26} {answer or 'UNKNOWN'}")
    print(f"\nanswered: {answered} / {len(QUESTIONS)}")


if __name__ == "__main__":
    main()
