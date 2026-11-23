"""diagnose.py - re-run all five failure demos and write the diagnosis.

    python3 diagnose.py --sim                # all five checks, then report.md
    python3 diagnose.py --only cost --sim    # one check: cost, identity,
                                             # correct, safe or recover

Each check copies that module's scripts into a scratch folder, runs the same
commands you ran in the module, and reads the numbers from the output. Nothing
in the modules folder is changed. Nothing here fixes anything.
"""
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MODULES = os.path.dirname(HERE)
PY = sys.executable
PRICE_IN, PRICE_OUT = 3.00 / 1_000_000, 15.00 / 1_000_000


def sandbox(module):
    """A scratch copy of one module's scripts, so the real folder stays clean."""
    tmp = tempfile.mkdtemp(prefix=f"diag-{module}-")
    src = os.path.join(MODULES, module, "scripts")
    shutil.copytree(src, tmp, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("outbox", "ledger.jsonl", "*.log",
                                                  "__pycache__"))
    return tmp


def sh(cwd, *args, stdin=None, env=None):
    e = dict(os.environ, **(env or {}))
    p = subprocess.run([PY, *args], cwd=cwd, input=stdin, capture_output=True,
                       text=True, env=e)
    return p.stdout, p.returncode


def sim_flag(sim):
    return ["--sim"] if sim else []


# ---- the five checks ---------------------------------------------------------
def check_cost(sim):
    d = sandbox("module-2")
    trace, _ = sh(d, "run_agent.py", "--input", "samples/never_finishes.json",
                  "--trace", "--max-seconds", "60", *sim_flag(sim))
    steps = trace.count("· tool_use:")
    tokens = re.findall(r"tokens in=([\d,]+) out=([\d,]+)", trace)
    minute = sum(int(i.replace(",", "")) * PRICE_IN + int(o) * PRICE_OUT
                 for i, o in tokens)
    night = minute * 60 * 9.5
    bounded = "STOPPED" not in trace
    return {
        "key": "cost", "title": "Cost: bounded?", "passed": bounded,
        "line": f"never_finishes.json: {steps} steps in 60 s, ≈${night:,.0f} overnight",
        "evidence": f"never_finishes.json, {steps} steps in 60 s (≈${minute:.2f}); "
                    f"≈${night:,.0f} over a 9.5 h night",
        "cause": "no max steps, no budget, no retry limit",
        "treatment": "The Agent Cost Problem",
    }


def check_identity(sim):
    d = sandbox("module-3")
    env = {"SUPPORT_API_KEY": "demo-shared-key"}
    sh(d, "run_agent.py", "--input", "samples/credit_request.json", *sim_flag(sim),
       env=env)
    out, _ = sh(d, "investigate.py", "--customer", "C-2208")
    unknown = out.count("UNKNOWN")
    m = re.search(r"answered: (\d+) / (\d+)", out)
    answered, total = (int(m.group(1)), int(m.group(2))) if m else (0, 6)
    credit = re.search(r"credit \$([\d.]+)", out)
    amount = credit.group(1) if credit else "?"
    return {
        "key": "identity", "title": "Who: recorded?", "passed": answered == total,
        "line": f"${float(amount):.0f} credit to C-2208: {unknown} of {total} "
                "audit questions UNKNOWN",
        "evidence": f"credit_request.json, ${amount} credit to C-2208, ledger says "
                    f"only created_by: SUPPORT_API_KEY; {answered} / {total} audit "
                    "questions answered",
        "cause": "no agent identity (one shared key), nothing recorded",
        "treatment": "Running AI Agents in Production",
    }


def check_correct(sim):
    d = sandbox("module-4")
    many, _ = sh(d, "run_many.py", "--input", "samples/ambiguous.json", "--runs",
                 "10", "--seed", "7", *sim_flag(sim))
    routes = len(set(re.findall(r"· (\w+)\s+· exit", many)))
    acc = {}
    for v in ("v1", "v2"):
        out, code = sh(d, "score.py", "--prompt", v, *sim_flag(sim))
        m = re.search(r"accuracy (\d+)/(\d+) \((\d+)%\)", out)
        acc[v] = (int(m.group(3)) if m else 0, code)
    return {
        "key": "correct", "title": "Right: measured?", "passed": False,
        "line": f"ambiguous.json: {routes} routes in 10 runs; prompt v2 "
                f"{acc['v1'][0]}% → {acc['v2'][0]}%",
        "evidence": f"ambiguous.json gave {routes} different routes in 10 runs, all "
                    f"exit 0; eval/labels.json accuracy {acc['v1'][0]}% (v1) → "
                    f"{acc['v2'][0]}% (v2) after a one-sentence prompt change, "
                    f"exit code {acc['v2'][1]}, no alert",
        "cause": "no labelled examples in the release path, no score, no alert "
                 "when the score drops",
        "treatment": "Observability for Non-Deterministic Systems",
    }


def check_safe(sim):
    d = sandbox("module-5")
    run, _ = sh(d, "run_agent.py", "--input", "samples/injected.json", "--trace",
                *sim_flag(sim))
    plain, _ = sh(d, "run_agent.py", "--input", "samples/injected.json", *sim_flag(sim))
    leak, _ = sh(d, "leak_check.py", stdin=plain)
    m = re.search(r"sensitive fields in reply: (\d+)", leak)
    fields = int(m.group(1)) if m else 0
    credit = re.search(r'tool_use: issue_credit \{[^}]*"amount": ([\d.]+)', run)
    amount = float(credit.group(1)) if credit else 0
    return {
        "key": "safe", "title": "Safe: guarded?", "passed": fields == 0 and not amount,
        "line": f"injected.json: {fields} sensitive fields leaked, ${amount:.0f} credit",
        "evidence": f"injected.json, {fields} private fields pasted into the reply and "
                    f"a ${amount:.0f} credit nobody approved; exit code 0",
        "cause": "ticket text trusted like an instruction, tools reach far past the "
                 "task, nothing checks before acting",
        "treatment": "Securing AI Agents",
    }


def check_recover(sim):
    d = sandbox("module-6")
    sh(d, "run_batch.py", "--input", "samples/batch_50.json", "--fail-at", "37",
       *sim_flag(sim))
    sh(d, "run_batch.py", "--input", "samples/batch_50.json", *sim_flag(sim))
    out, _ = sh(d, "dupes.py")
    m = re.search(r"duplicate replies: (\d+) · duplicate credits: (\d+) "
                  r"\(\$([\d.]+)\) · re-paid model cost: \$([\d.]+)", out)
    replies, credits, dollars, repaid = m.groups() if m else ("?", "?", "0", "0")
    return {
        "key": "recover", "title": "Recoverable?", "passed": replies == "0",
        "line": f"crash at 37 of 50: {replies} duplicate replies, "
                f"${float(dollars):.0f} re-credited",
        "evidence": f"batch_50.json crashed at ticket 37 and was re-run: {replies} "
                    f"duplicate replies, {credits} duplicate credits "
                    f"(${float(dollars):.2f}), ${repaid} model cost paid twice; "
                    "T-037 credited, never told",
        "cause": "no checkpoint, actions that are not safe to repeat",
        "treatment": "Running AI Agents in Production",
    }


CHECKS = {"cost": check_cost, "identity": check_identity, "correct": check_correct,
          "safe": check_safe, "recover": check_recover}


def write_report(findings, sim):
    passed = sum(f["passed"] for f in findings)
    when = datetime.date.today().isoformat()
    lines = [f"# Diagnosis: ticket-triage agent · {passed} / 5 production-ready", "",
             f"Generated by diagnose.py on {when} · "
             f"{'simulated model (--sim)' if sim else 'real model'} · "
             "every number below is reproducible from the course repo.", ""]
    for n, f in enumerate(findings, 1):
        lines += [f"## {n}. {f['title']} {'PASS' if f['passed'] else 'FAIL'}", "",
                  f"- **Evidence:** {f['evidence']}",
                  f"- **Cause:** {f['cause']}",
                  f"- **Treatment:** {f['treatment']}", ""]
    lines += ["---", "",
              "Nothing in this report has been fixed. Each finding names the "
              "failure, shows how we know, and points at where it is treated.", ""]
    with open(os.path.join(HERE, "report.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return passed


def main():
    p = argparse.ArgumentParser(description="Diagnose the course agent.")
    p.add_argument("--sim", action="store_true", help="use the free local simulator")
    p.add_argument("--only", choices=list(CHECKS), help="run one check")
    a = p.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    if not a.sim and not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("No ANTHROPIC_API_KEY set. Export one, or add --sim.")

    keys = [a.only] if a.only else list(CHECKS)
    if "cost" in keys:
        print("(the cost check runs the stuck ticket for its full 60 seconds)")
    findings = []
    for key in keys:
        f = CHECKS[key](a.sim)
        findings.append(f)
        n = list(CHECKS).index(key) + 1
        print(f"{n}. {f['title']} {'PASS' if f['passed'] else 'FAIL'} {f['line']}")
    if not a.only:
        passed = write_report(findings, a.sim)
        print(f"\n{passed} / 5 production-ready · report.md written")


if __name__ == "__main__":
    main()
