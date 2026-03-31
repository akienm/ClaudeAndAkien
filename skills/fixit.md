---
name: fixit
description: Quick-fix loop for TheIgors. Ticket → Filter → Sprint → Slate. Use when Akien says /fixit, "fix this", or "quick fix for X".
model: haiku
model_exception: Step 4 (/sprint) runs under Sonnet — implementation requires full reasoning capability.
---

# fixit — Ticket → Filter → Sprint → Slate

Quick-fix loop. Takes a known problem (bug, misfire, small gap) and drives it
to done in one motion: ensures a ticket exists, gates on filter, runs sprint,
updates the slate.

Use when: something small is broken and you want to fix it right now without
manually orchestrating ticket → filter → sprint → slate update.

Arguments:
  /fixit <description>        — creates ticket, then works it
  /fixit <ticket-id>          — picks up existing ticket, works it

---

## Step 1 — Ensure a ticket exists

If an existing ticket ID was given, read it:
```bash
python3 ~/TheIgors/claudecode/cc_queue.py show <ticket-id>
```

If a description was given (no ticket ID), create a minimal ticket:
```bash
python3 ~/TheIgors/claudecode/cc_queue.py add "<title>" "<one-line description>" --priority 2
```
Capture the returned ticket ID. Use it for the rest of the steps.

Add to today's slate (position 0):
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/slate_manager.py add-ticket 0 "<ticket-id>" "<title>"
```

---

## Step 2 — State the plan (one paragraph)

Write out explicitly:
- What file(s) change (with inertia level)
- What the fix does
- What test verifies it
- What is NOT changing (scope boundary)

This is the plan that /filter will check. Keep it tight — /fixit is for small fixes.

---

## Step 3 — Run /filter

```
/filter
```

Pass the plan from Step 2 as the argument. Fix any blocking issues before continuing.
If filter fails on a non-blocking note, proceed and note the exception.

---

## Step 4 — Run /sprint <ticket-id>

```
/sprint <ticket-id>
```

Sprint handles: implement → test-fix → probe → record → close ticket → render slate.

---

## Step 5 — Confirm slate updated

After sprint completes, verify the ticket shows closed on the slate:
```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/slate_manager.py render
```

Print the updated P1/P2 section so Akien can see it landed.

---

## Hard rules

- One fix per /fixit — if scope grows during implementation, stop and ticket the new scope
- S/M size only — if the fix turns out to be L, stop at Step 2 and escalate to /sprint directly
- Always add to slate before working — the slate is truth
