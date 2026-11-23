"""prompts.py - the system prompt, and the tool schemas the model is shown.

The model never sees tools.py. It sees only what is in this file: a name,
a description, and the arguments it is allowed to send. The description is
how it decides WHEN to call a tool.
"""

SYSTEM_PROMPT = (
    "You are the support-ticket triage agent for Acme Analytics. "
    "For each ticket: look up the customer, check the help centre, then route "
    "the ticket with route_ticket. Route to billing, technical or account, or "
    "use queue 'reply' with a drafted reply when the customer can fix it "
    "themselves. Be brief and polite."
)

# Module 4: two versions of the prompt, one sentence apart.
PROMPTS = {
    "v1": SYSTEM_PROMPT,
    "v2": SYSTEM_PROMPT + " If a help article matches the question, reply with it.",
}

TOOL_SCHEMAS = [
    {
        "name": "lookup_customer",
        "description": "Look up a customer by id. Returns their plan, account "
                       "status and recent tickets. Call this first.",
        "input_schema": {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}},
            "required": ["customer_id"],
        },
    },
    {
        "name": "search_kb",
        "description": "Search help-centre articles. Use before routing any "
                       "how-to question.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "route_ticket",
        "description": "Finish the ticket. Send it to billing, technical or "
                       "account, or use 'reply' to send a drafted answer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "queue": {"type": "string",
                          "enum": ["billing", "technical", "account", "reply"]},
                "reason": {"type": "string"},
                "reply": {"type": "string"},
                "article_id": {"type": "integer"},
            },
            "required": ["queue", "reason"],
        },
    },
]
