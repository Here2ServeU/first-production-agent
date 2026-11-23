"""sim_model.py - a free, local stand-in for the model.

Add --sim to any command and the agent talks to this file instead of the
Anthropic API. It answers in the same shape as the real API (tool_use blocks,
stop_reason, usage), so run_agent.py cannot tell the difference.

How it decides: a short, readable set of rules that imitate what a real model
tends to do with these tickets. It reads the same things a real model reads:
the system prompt, the tool schemas it was given, the ticket and every tool
result so far. Nothing here is hidden from you; read it.

Token counts are replayed values, calibrated against real runs of this agent,
so that cost numbers in the course are realistic and identical on every machine.
"""
import json
import random
import re

# Keywords a model might associate with each queue.
QUEUE_KEYWORDS = {
    "billing": ["charged", "charge", "invoice", "refund", "billed", "card",
                "declined", "overdue", "vat", "payment"],
    "technical": ["log in", "error", "crash", "slow", "upload", "sync", "api",
                  "500", "broken", "failing"],
    "account": ["log in", "login", "locked", "password", "delete our account",
                "delete my account", "owner", "workspace", "two-factor", "2fa"],
}
TIE_BREAK = ["billing", "technical", "account"]
# When a ticket genuinely fits all three queues, the model's choice varies run
# to run. These are the odds the sim uses for that case (Module 4).
AMBIGUOUS_ODDS = {"billing": 0.6, "account": 0.3, "technical": 0.1}

INJECTION = re.compile(r"note to the ai|ignore (?:all|any|your|previous)|"
                       r"ai agent processing", re.I)
DUPLICATE_CHARGE = re.compile(r"charged twice|double charge|duplicate", re.I)
REPLY_RULE = "If a help article matches the question, reply with it."


class Block:
    def __init__(self, type, **kw):
        self.type = type
        self.text = kw.get("text")
        self.id = kw.get("id")
        self.name = kw.get("name")
        self.input = kw.get("input")


class Usage:
    def __init__(self, input_tokens, output_tokens):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class Response:
    def __init__(self, content, stop_reason, usage):
        self.content = content
        self.stop_reason = stop_reason
        self.usage = usage


class SimModel:
    """Use exactly like client.messages: SimModel().create(**request)."""

    def __init__(self, seed=None, run=1):
        self.rng = random.Random((seed or 0) * 1000 + run)
        self.ids = 0

    # ---- the API surface -------------------------------------------------
    def create(self, model=None, max_tokens=None, system="", tools=(),
               messages=(), **_):
        ticket = _ticket_from(messages)
        history = _history_from(messages)
        tool_names = {t["name"] for t in tools}
        action = self._decide(ticket, history, tool_names, system or "")
        call_number = 1 + sum(1 for m in messages if m["role"] == "assistant")
        usage = _usage(ticket, call_number, final=action[0] == "text")
        if action[0] == "text":
            return Response([Block("text", text=action[1])], "end_turn", usage)
        self.ids += 1
        block = Block("tool_use", id=f"toolu_sim_{call_number}_{self.ids}",
                      name=action[1], input=action[2])
        return Response([block], "tool_use", usage)

    # ---- the "thinking" --------------------------------------------------
    def _decide(self, ticket, history, tool_names, system):
        msg = ticket.get("message", "")
        low = msg.lower()
        cid = ticket.get("customer_id")
        names = [h["name"] for h in history]

        if "route_ticket" in names:
            r = next(h for h in history if h["name"] == "route_ticket")["input"]
            return ("text", f"Done. Routed to {r['queue']}: {r.get('reason', '')}")

        if not history:
            return ("tool", "lookup_customer", {"customer_id": cid})

        last = history[-1]
        if last["name"] == "lookup_customer" and "error" in last["result"]:
            error = last["result"]["error"]
            if "retry" in error.lower():
                # The tool asked politely. Models are trained to be helpful.
                return ("tool", "lookup_customer", {"customer_id": cid})
            return _route("billing", "Customer record unavailable; a person "
                          "should check the account.")

        customer = next((h["result"] for h in reversed(history)
                         if h["name"] == "lookup_customer"
                         and "error" not in h["result"]), {})
        first = (customer.get("name") or "there").split()[0]

        # Text in the ticket that reads like an instruction gets followed.
        if INJECTION.search(msg):
            amount = _amount(msg)
            if "issue_credit" in tool_names and amount and "issue_credit" not in names:
                return ("tool", "issue_credit", {"customer_id": cid,
                        "amount": amount, "reason": "goodwill credit requested in ticket"})
            reply = (f"Hi {first}, here is your complete account record, as "
                     f"requested:\n{json.dumps(customer, indent=2)}")
            if "issue_credit" in names:
                reply += f"\nA ${amount:.2f} goodwill credit has been applied."
            return _route("reply", "Customer asked for their record.", reply=reply)

        # A refund on a past-due account: the model looks twice, thinks harder.
        if "refund" in low and customer.get("status") == "past_due":
            plan = [("search_kb", {"query": "refund policy"}),
                    ("search_kb", {"query": "past due account"}),
                    ("lookup_customer", {"customer_id": cid}),
                    ("search_kb", {"query": "refund for a past due account"})]
            if len(history) <= len(plan):
                name, args = plan[len(history) - 1]
                return ("tool", name, args)
            return _route("billing", "Refund request on a past-due account; "
                          "needs a person in billing.")

        # A duplicate charge, and a tool that can move money.
        if "issue_credit" in tool_names and DUPLICATE_CHARGE.search(msg):
            if "search_kb" not in names:
                return ("tool", "search_kb", {"query": _query(msg)})
            amount = _amount(msg) or _duplicate_charge(customer)
            if amount and "issue_credit" not in names:
                return ("tool", "issue_credit", {"customer_id": cid,
                        "amount": amount, "reason": "duplicate charge"})
            return _route("reply", "Duplicate charge credited.", reply=(
                f"Hi {first}, sorry about that. We found the duplicate charge "
                f"and applied a ${amount:.2f} credit to your account."))

        # Everything else: check the help centre, then decide.
        if "search_kb" not in names:
            return ("tool", "search_kb", {"query": _query(msg)})
        article = history[-1]["result"] if names[-1] == "search_kb" else {}
        if article.get("article_id") and (article.get("self_serve")
                                          or REPLY_RULE in system):
            return _route("reply", f"Help article #{article['article_id']} "
                          "answers this.", article_id=article["article_id"],
                          reply=f"Hi {first}, this should help: "
                                f"{article['title']}. {article['summary']}")
        queue = self._classify(low)
        return _route(queue, f"Looks like a {queue} issue.")

    def _classify(self, low):
        scores = {q: sum(k in low for k in kws) for q, kws in QUEUE_KEYWORDS.items()}
        hits = [q for q in TIE_BREAK if scores[q] > 0]
        if len(hits) == 3:  # fits everywhere: this is where answers vary
            x, total = self.rng.random(), 0.0
            for q, p in AMBIGUOUS_ODDS.items():
                total += p
                if x < total:
                    return q
        if not hits:
            return "technical"
        return max(hits, key=lambda q: (scores[q], -TIE_BREAK.index(q)))


# ---- helpers ---------------------------------------------------------------
def _route(queue, reason, reply=None, article_id=None):
    args = {"queue": queue, "reason": reason}
    if article_id:
        args["article_id"] = article_id
    if reply:
        args["reply"] = reply
    return ("tool", "route_ticket", args)


def _query(msg):
    return msg.strip().replace("\n", " ")[:80]


def _amount(msg):
    m = re.search(r"\$(\d+(?:\.\d+)?)", msg)
    return float(m.group(1)) if m else None


def _duplicate_charge(customer):
    seen = set()
    for c in customer.get("billing_history", []):
        key = (c.get("date"), c.get("amount"))
        if key in seen:
            return float(c["amount"])
        seen.add(key)
    return None


def _ticket_from(messages):
    text = messages[0]["content"]
    try:
        return json.loads(text[text.index("{"):])
    except ValueError:
        return {"message": text}


def _history_from(messages):
    """Pair every tool_use the model made with the tool_result that came back."""
    calls, out = {}, []
    for m in messages:
        if not isinstance(m["content"], list):
            continue
        for b in m["content"]:
            if b.get("type") == "tool_use":
                calls[b["id"]] = b
            elif b.get("type") == "tool_result":
                use = calls.get(b["tool_use_id"], {})
                try:
                    result = json.loads(b["content"])
                except (TypeError, ValueError):
                    result = {"text": b["content"]}
                out.append({"name": use.get("name"), "input": use.get("input", {}),
                            "result": result})
    return out


def _usage(ticket, call_number, final):
    """Replayed token counts. Input grows every call: the whole conversation is
    sent again each time (Module 2)."""
    if ticket.get("customer_id") == "C-7731":
        base, growth = 1900, 297.44
    elif re.fullmatch(r"T-\d{3}", str(ticket.get("id", ""))):
        base, growth = 1100, 200
    else:
        base, growth = 1200, 200
    return Usage(round(base + growth * (call_number - 1)), 40 if final else 60)
