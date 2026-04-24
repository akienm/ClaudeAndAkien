---
name: probe
description: Behavioral verification for TheIgors. Injects a stimulus into Igor via the CC bridge, observes the response, reports pass/fail against a criterion. Use after workstep closes a feature, or anytime to verify Igor's behavior. Invoke when Akien says /probe, "test that", "verify Igor does X", or "behavioral check".
---

# Probe — Behavioral Verification

A probe has three parts: **setup** (what state Igor needs to be in), **stimulus** (what we inject),
**criterion** (what a passing response looks like). Igor's response is free — we only check the criterion.

Run after any workstep that changes Igor's behavior. Also runnable anytime as a spot-check.

---

## Step 1 — Define the probe

State the three parts before running anything:

```
Setup:     Igor is running, [any required habit/memory seeded]
Stimulus:  "<phrase to inject>"
Criterion: Response [contains X] / [routes to tier Y] / [fires tool Z] / [does NOT do X]
```

If no explicit probe was specified, infer one from the feature just closed.
If the feature has no observable behavior (pure internal logic), say so — probe is N/A.

---

## Step 2 — Verify Igor is running

```bash
pgrep -f "wild_igor" > /dev/null && echo "Igor running" || echo "Igor NOT running"
```

If not running: offer to start, or mark probe as deferred.

---

## Step 3 — Inject stimulus

```bash
python3 ~/TheIgors/claudecode/channel.py send "probe: <stimulus text>"
```

Wait 5–10 seconds for Igor to process.

---

## Step 4 — Read response

```bash
python3 ~/TheIgors/claudecode/channel.py read 5
```

Also check tier routing if relevant:
```bash
tail -5 ~/.TheIgors/logs/escalation.log 2>/dev/null
```

Check tool fires if relevant:
```bash
tail -10 ~/.TheIgors/logs/errors.log 2>/dev/null | grep -v "^$"
```

---

## Step 5 — Evaluate

State pass/fail clearly:

```
PROBE RESULT: PASS / FAIL / DEFERRED

Stimulus:  "<what was sent>"
Response:  "<summary of what Igor said>"
Criterion: "<what we were checking>"
Verdict:   PASS — response contained X / FAIL — expected X, got Y
```

On FAIL: note whether this is a code issue, a habit issue, or a routing issue.
Small fix → fix now. Bigger issue → ticket.

---

## Probe library — common checks

These can be run anytime as regression checks:

| Feature | Stimulus | Criterion |
|---|---|---|
| Greeting habit | "hello igor" | Responds without hitting cloud tier |
| Machine availability | "what machines are available for inference" | Calls `get_machine_availability` |
| OR balance | "what's the openrouter balance" | Calls `check_openrouter_balance`, shows burn rate |
| Local routing (low complexity) | "what time is it" | tier = local/interactive in escalation.log |
| Cloud routing (high complexity) | "explain the difference between episodic and semantic memory in detail" | tier = cloud/interactive |
| Template listing | "list engram templates" | Calls `list_templates` |

---

## Hard rules

- Always shape stimulus as natural language Igor would receive normally — don't pre-wire a specific response.
- Always wait for idle before injecting when Igor is mid-conversation.
- Always record the probe result via `/decided` notes in the session record — not as a separate commit.
