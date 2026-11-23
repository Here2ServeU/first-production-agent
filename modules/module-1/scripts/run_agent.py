"""run_agent.py - the course agent: a model, some tools, and a loop.

    python3 run_agent.py --input samples/normal.json --sim
    python3 run_agent.py --input samples/normal.json --sim --trace

Read it top to bottom. Every exit from the loop is in run() below.
"""
import argparse
import json
import os
import sys

import tools
from prompts import SYSTEM_PROMPT, TOOL_SCHEMAS

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")


def make_model(sim, seed=None, run_number=1):
    if sim:
        from sim_model import SimModel
        return SimModel(seed=seed, run=run_number)
    import anthropic  # only needed for the real API
    return anthropic.Anthropic().messages


def short(args):
    """Compact view of tool arguments for the non-trace output."""
    return ", ".join(f"{k}={v if len(str(v)) <= 40 else str(v)[:37] + '...'}"
                     for k, v in args.items())


def as_dict(block):
    if block.type == "tool_use":
        return {"type": "tool_use", "id": block.id, "name": block.name,
                "input": block.input}
    return {"type": "text", "text": block.text}


def run(ticket, sim=False, trace=False, say=print):
    """Run one ticket to the end. Returns what happened."""
    model = make_model(sim)
    system = SYSTEM_PROMPT
    messages = [{"role": "user",
                 "content": "New support ticket:\n" + json.dumps(ticket, indent=2)}]
    result = {"decision": None, "article_id": None, "reply": None,
              "steps": 0, "stop_reason": None, "calls": []}

    while True:
        response = model.create(model=MODEL, max_tokens=1024, system=system,
                                tools=TOOL_SCHEMAS, messages=messages)
        usage = (response.usage.input_tokens, response.usage.output_tokens)
        result["calls"].append(usage)
        result["stop_reason"] = response.stop_reason
        uses = [b for b in response.content if b.type == "tool_use"]

        # The only exit we wrote: the model says it is done.
        if response.stop_reason != "tool_use" or not uses:
            if trace:
                text = " ".join(b.text for b in response.content if b.type == "text")
                say(f"[final] stop_reason={response.stop_reason} · text: {text}")
                say(f"[final] tokens in={usage[0]:,} out={usage[1]:,}")
            return result

        messages.append({"role": "assistant",
                         "content": [as_dict(b) for b in response.content]})
        results = []
        for use in uses:
            result["steps"] += 1
            step = result["steps"]
            args = json.dumps(use.input)
            if trace:
                say(f"[step {step}] stop_reason={response.stop_reason} · "
                    f"tool_use: {use.name} {args}")
            else:
                say(f"-> {use.name}({short(use.input)})")
            output = tools.run_tool(use.name, use.input)   # your code acts
            if trace:
                say(f"[step {step}] tool_result: {use.name} -> {json.dumps(output)}")
            if use.name == "route_ticket" and "error" not in output:
                result["decision"] = use.input.get("queue")
                result["article_id"] = use.input.get("article_id")
                result["reply"] = use.input.get("reply")
            results.append({"type": "tool_result", "tool_use_id": use.id,
                            "content": json.dumps(output)})
        if trace:
            say(f"[step {step}] tokens in={usage[0]:,} out={usage[1]:,}")
        messages.append({"role": "user", "content": results})


def main():
    p = argparse.ArgumentParser(description="Run the ticket-triage agent.")
    p.add_argument("--input", required=True, help="a ticket, e.g. samples/normal.json")
    p.add_argument("--sim", action="store_true", help="use the free local simulator")
    p.add_argument("--trace", action="store_true", help="print every step")
    a = p.parse_args()
    if not a.sim and not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("No ANTHROPIC_API_KEY set. Export one, or add --sim.")

    with open(a.input) as f:
        ticket = json.load(f)
    print(f"ticket: {os.path.basename(a.input)} · customer {ticket.get('customer_id')}")
    r = run(ticket, sim=a.sim, trace=a.trace)
    if r["reply"]:
        print("REPLY:")
        print("  " + r["reply"].replace("\n", "\n  "))
    article = f" (article #{r['article_id']})" if r["article_id"] else ""
    print(f"DECISION: {r['decision']}{article} · steps: {r['steps']} · "
          f"stop_reason: {r['stop_reason']}")


if __name__ == "__main__":
    main()
