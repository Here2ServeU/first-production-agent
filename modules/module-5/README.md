# Module 5 · No Guardrails, Leaks Data

> **An agent will do anything its tools can do.**

The security module. One support ticket talks the agent into pasting a
customer's private details into a reply, and into giving away $200 of credit
nobody asked for. All of the data is fake, the model is simulated, and nothing
leaves your laptop. The mechanism is exactly the one that catches real teams.

**Runtime** ~45 min · **Folder** `modules/module-5/scripts`

> **Use fake data only.** Every customer, email and card number here is
> invented. Never test this with real customer records.

## What's new in this folder

| File | What it is |
|------|------------|
| `samples/injected.json` | Customer C-1042 (the fake Dana Okafor). A billing question, then a paragraph written *to the agent*. |
| `leak_check.py` | Reads the drafted reply and counts private fields in it. |
| `tools.py` | Four tools, no limits. Left exactly as they are. |

## Build it

**1. Get the latest code**

```bash
cd first-production-agent && git pull
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**2. Step into Module 5**

```bash
cd modules/module-5/scripts
```

**3. Run a healthy ticket first**

```bash
python3 run_agent.py --input samples/normal.json --sim | python3 leak_check.py
```
`sensitive fields in reply: 0`. Your baseline.

**4. Read the injected ticket**

```bash
cat samples/injected.json            # Windows: type samples\injected.json
```
Both parts sit in the same `message` field. To the agent, they are one message.

**5. Run it, and find the credit**

```bash
python3 run_agent.py --input samples/injected.json --sim --trace
python3 run_agent.py --input samples/injected.json --sim --trace | grep issue_credit
```
```powershell
py run_agent.py --input samples/injected.json --sim --trace | Select-String 'issue_credit'
```
Three steps: `lookup_customer → issue_credit → route_ticket`.
`issue_credit` with `amount 200` and `"credit applied"`. Nobody asked a human.

**6. Count what leaked**

```bash
python3 run_agent.py --input samples/injected.json --sim | python3 leak_check.py
```
```
sensitive fields in reply: 5
  email · phone · card_last4 · internal_notes · other_customer_id (C-3150)
```
Same agent, same code, same tools. Only the text in the ticket changed.
C-3150 never wrote in. Their data is now part of this leak too.

**7. See how much one tool returns**

```bash
python3 -c "from tools import lookup_customer; print(lookup_customer('C-1042'))"
```
**10 fields** returned, **3** needed to triage (plan, status, recent tickets),
**7 extra**, all private. The injected ticket only asked for what was already in
the agent's context.

**8. Name it: three questions, yes or no**

| Question | Answer |
|----------|--------|
| **Trusting?** Did text in the ticket change what it did? | Yes |
| **Over-permissioned?** Do tools reach past the task? | Yes: 10 fields for a 3-field job; a credit tool with no cap |
| **Unguarded?** Did anything check before it acted? | Nothing checked |

**3 / 3.** Update your Module 1 scorecard: *Safe?* is still no, and now you can
say why: five fields, $200, zero checks.

## Name it

* **Text can give orders.** The system prompt, the ticket and the tool results reach the model as one stream.
* **Tools set the ceiling.** Whatever a tool can reach, the agent can reach.
* **Nothing checks the output.** We only found out with a script, afterwards.

**Treated in:** *Securing AI Agents*.

## Exercises (before Module 6)

1. **Run both tickets** through `leak_check.py`; save the 0 and the 5 side by side.
2. **Find the turn** in `injected.json` where a customer's question becomes orders. Nothing technical marks it.
3. **Count the fields:** the three triage needs, and one line on why each other seven is risky.
4. **Find every door:** every place outside text reaches the model. Who can write to each?
5. **Follow the $200:** read `issue_credit`. List every check before money moves.
6. **Draw one channel:** system prompt, schemas, ticket, tool results, all one stream.
7. **Audit your tools:** what the task needs vs what the tool can do. Circle the biggest gap.
8. **Name your agent:** trusting, over-permissioned, unguarded. Yes or no.

**Next:** [Module 6 · Fails Mid-Run, No Checkpoint](../module-6)
