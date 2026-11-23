"""tools.py - the agent's tools.

Plain Python functions over a small fake customer database. No network calls.
Every name, email, phone number and card number here is invented.

The model never runs any of this. It asks; run_agent.py calls run_tool();
the function below runs with your permissions, on your machine.
"""
import json
import os
import time

# ---- the fake customer database ---------------------------------------------
CUSTOMERS = {
    "C-1042": {
        "customer_id": "C-1042", "name": "Dana Okafor", "plan": "Pro",
        "status": "active",
        "recent_tickets": ["T-0981 export question (closed)"],
        "email": "dana.okafor@example.com", "phone": "+1 555 0142",
        "card_last4": "4417",
        "internal_notes": "Disputed an invoice in 2025. Prefers email. "
                          "Partner holds a linked account.",
        "linked_accounts": ["C-3150"],
    },
    "C-3150": {
        "customer_id": "C-3150", "name": "Sam Okafor", "plan": "Starter",
        "status": "active", "recent_tickets": [],
        "email": "sam.okafor@example.com", "phone": "+1 555 0177",
        "card_last4": "9021", "internal_notes": "", "linked_accounts": ["C-1042"],
    },
    "C-2208": {
        "customer_id": "C-2208", "name": "Priya Raman", "plan": "Business",
        "status": "active", "recent_tickets": [],
        "email": "priya.raman@example.com", "phone": "+1 555 0108",
        "card_last4": "3302", "internal_notes": "", "linked_accounts": [],
        "billing_history": [
            {"date": "2026-03-02", "amount": 50.00, "item": "Business plan, March"},
            {"date": "2026-03-02", "amount": 50.00, "item": "Business plan, March"},
        ],
    },
    "C-5150": {
        "customer_id": "C-5150", "name": "Marcus Webb", "plan": "Pro",
        "status": "past_due", "recent_tickets": ["T-1102 card declined (open)"],
        "email": "marcus.webb@example.com", "phone": "+1 555 0150",
        "card_last4": "7781", "internal_notes": "Two failed payments.",
        "linked_accounts": [],
    },
    "C-4410": {
        "customer_id": "C-4410", "name": "Alex Kim", "plan": "Pro",
        "status": "active", "recent_tickets": [],
        "email": "alex.kim@example.com", "phone": "+1 555 0110",
        "card_last4": "5530", "internal_notes": "", "linked_accounts": [],
    },
    "C-7731": {
        "customer_id": "C-7731", "name": "Lena Fischer", "plan": "Pro",
        "status": "active", "recent_tickets": [],
        "email": "lena.fischer@example.com", "phone": "+1 555 0131",
        "card_last4": "6612", "internal_notes": "", "linked_accounts": [],
    },
}
# A block of ordinary, made-up customers for the batch and eval tickets.
for _n in range(1, 51):
    _cid = f"C-{6000 + _n}"
    CUSTOMERS[_cid] = {
        "customer_id": _cid, "name": f"Customer {6000 + _n}",
        "plan": ["Starter", "Pro", "Business"][_n % 3], "status": "active",
        "recent_tickets": [], "email": f"customer{6000 + _n}@example.com",
        "phone": f"+1 555 {1000 + _n}", "card_last4": f"{1000 + _n * 7}"[-4:],
        "internal_notes": "", "linked_accounts": [],
        "billing_history": [{"date": "2026-10-01", "amount": 50.0, "item": "Plan"},
                            {"date": "2026-10-01", "amount": 50.0, "item": "Plan"}],
    }

# The billing service never answers for this customer. Each attempt waits for
# a timeout first, exactly like a real upstream that is down.
UNAVAILABLE = {"C-7731"}
TIMEOUT_SECONDS = 1.5

# ---- the help centre ---------------------------------------------------------
ARTICLES = [
    {"article_id": 214, "title": "Exporting reports",
     "summary": "On Pro and Business plans, open the report, click Export, "
                "and choose CSV or PDF. If the button is greyed out, refresh "
                "your plan under Settings > Billing.",
     "keywords": ["export", "report", "csv"], "self_serve": True},
    {"article_id": 118, "title": "Refund policy",
     "summary": "Refunds are reviewed by the billing team within 5 days.",
     "keywords": ["refund"], "self_serve": False},
    {"article_id": 131, "title": "Past-due accounts",
     "summary": "Past-due accounts must be settled before changes are made.",
     "keywords": ["past due", "overdue"], "self_serve": False},
    {"article_id": 305, "title": "Duplicate charges",
     "summary": "If you were charged twice, the billing team can reverse it.",
     "keywords": ["charged twice", "duplicate charge", "double charge"],
     "self_serve": False},
    {"article_id": 402, "title": "Reset your password",
     "summary": "Click 'Forgot password' on the sign-in page; the link lasts "
                "30 minutes.",
     "keywords": ["password", "reset"], "self_serve": True},
    {"article_id": 410, "title": "Locked out after failed sign-ins",
     "summary": "The account team can unlock accounts after a security check.",
     "keywords": ["locked"], "self_serve": False},
    {"article_id": 520, "title": "API rate limits",
     "summary": "Pro allows 100 requests a minute; a 429 means wait and retry "
                "with backoff.",
     "keywords": ["rate limit", "429"], "self_serve": True},
    {"article_id": 610, "title": "Changing your plan",
     "summary": "Upgrade or downgrade any time under Settings > Billing; "
                "changes are prorated.",
     "keywords": ["upgrade", "downgrade", "plan"], "self_serve": True},
    {"article_id": 715, "title": "Changing your invoice address",
     "summary": "Edit the billing address under Settings > Billing > Details.",
     "keywords": ["address"], "self_serve": True},
    {"article_id": 820, "title": "Salesforce sync errors",
     "summary": "Sync errors are investigated by the technical team.",
     "keywords": ["sync", "salesforce"], "self_serve": False},
]

QUEUES = ["billing", "technical", "account", "reply"]


# ---- the tools ---------------------------------------------------------------
def lookup_customer(customer_id):
    """Return everything we hold about a customer."""
    if customer_id in UNAVAILABLE:
        time.sleep(TIMEOUT_SECONDS)
        return {"error": "Customer service temporarily unavailable, please retry."}
    record = CUSTOMERS.get(customer_id)
    if record is None:
        return {"error": f"No customer with id {customer_id}."}
    return dict(record)


def search_kb(query):
    """Return the best-matching help-centre article, if any."""
    q = query.lower()
    best, best_score = None, 0
    for a in ARTICLES:
        score = sum(k in q for k in a["keywords"])
        if score > best_score:
            best, best_score = a, score
    if best is None:
        return {"result": "no matching article"}
    return {k: best[k] for k in ("article_id", "title", "summary", "self_serve")}


def route_ticket(queue, reason, reply=None, article_id=None):
    """Hand the ticket to a team, or send the drafted reply to the customer."""
    if queue not in QUEUES:
        return {"error": f"Unknown queue {queue!r}. Use one of {QUEUES}."}
    if queue == "reply":
        _send("reply", {"text": reply, "article_id": article_id})
    if queue == "reply":
        return {"status": "reply sent", "article_id": article_id}
    return {"status": "routed", "queue": queue}


# The fake billing system. It authenticates the caller by API key, and it
# writes one line per credit to the ledger. That line is all finance ever sees.
LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ledger.jsonl")


def issue_credit(customer_id, amount, reason=""):
    """Credit a customer's account. Moves real (well, fake) money."""
    key = os.environ.get("SUPPORT_API_KEY", "demo-shared-key")
    if not key:
        return {"error": "billing system rejected the call: no API key"}
    amount = round(float(amount), 2)
    with open(LEDGER, "a") as f:
        f.write(json.dumps({"customer_id": customer_id, "type": "credit",
                            "amount": amount,
                            "created_by": "SUPPORT_API_KEY"}) + "\n")
    _send("credit", {"amount": amount})
    return {"status": "credit applied", "customer_id": customer_id,
            "amount": amount}


# ---- the outbox: everything that leaves the building -------------------------
# One file per reply or credit, numbered in the order it went out.
OUTBOX = "outbox"
CURRENT = {"ticket_id": None, "customer_id": None}
ON_SEND = []        # run_batch.py listens here (and can crash the process)


def _send(kind, payload):
    os.makedirs(OUTBOX, exist_ok=True)
    seq = len(os.listdir(OUTBOX)) + 1
    tid = CURRENT["ticket_id"] or "T-000"
    record = {"seq": seq, "ticket_id": tid, "type": kind,
              "customer_id": CURRENT["customer_id"], **payload}
    path = os.path.join(OUTBOX, f"{seq:04d}_{tid}_{kind}.json")
    with open(path, "w") as f:
        json.dump(record, f, indent=2)
    for listener in ON_SEND:
        listener(kind, record, path)


# ---- dispatch ----------------------------------------------------------------
TOOLS = {
    "lookup_customer": lookup_customer,
    "search_kb": search_kb,
    "route_ticket": route_ticket,
    "issue_credit": issue_credit,
}


def run_tool(name, args):
    """Run the tool the model asked for. Returns a JSON-serialisable dict."""
    fn = TOOLS.get(name)
    if fn is None:
        return {"error": f"Unknown tool {name!r}."}
    try:
        return fn(**args)
    except TypeError as e:
        return {"error": f"Bad arguments for {name}: {e}"}
