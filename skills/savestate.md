---
name: savestate
description: End-of-session savestate for TheIgors project. Updates all persistent records — design docs, memory files, GitHub discussion — so the next session starts with full context. Use when the user says /savestate, "save state", "end of session", or "wrap up".
---

# Savestate — TheIgors End-of-Session Ritual

If context is critically low (< 5% remaining): do Steps 0–0.5–2 only. Igor's memory + decisions_log survive.

---

## ⛔ Step 0 — State the current hypothesis FIRST

**Do this before anything else. Do not skip.**

One sentence: **what were we about to try and why?** NONE if nothing in-flight.

Say it out loud in the response before running any commands. Example:
> "In-flight: about to add burn trajectory to HeartbeatSource — haven't touched push_sources.py yet."
> "In-flight: NONE — last ticket closed cleanly."

This prevents next-session blindness. Write it into the Step 3 finalize call as the in_flight field.

---

## Step 0.5 — Flush session summary to Igor (FAST — do this first)

Flush the session summary to Igor's memory. Survives auto-compact.

```bash
python3 ~/TheIgors/claudecode/cc_queue.py flush_session 2026-03-15e "theme: ...; next: ..."
```

Non-fatal if Igor is down — logs locally and continues.
Note: individual decisions are flushed by Step 2 (decision_manager.py add handles this).

**This is the invariant:** a decision isn't made until it's in Igor's memory. The DSB is the durable backup.

---

## Step 2 — Record each new decision (CRITICAL)

For each new decision made this session, run:

```bash
IGOR_HOME_DB_URL=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001 \
  python3 ~/TheIgors/claudecode/decision_manager.py add Dxxx "short-name" "status" "one-line description"
```

This atomically: updates decisions_log.dsb header + appends line, upserts to docs_entries, flushes to Igor memory.
Do this before anything else file-related — decisions_log is the most irreplaceable artifact.

---

## Step 3 — Finalize session record (Designer + Akien — synthesis required)

This is the only step that needs judgment. The session record already has decisions + key changes
from /decided calls. Add the two synthesis fields:

```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/claudecode/session_manager.py finalize "YYYY-MM-DDx" \
  "Next session: top 2-3 priorities" \
  "In-flight hypothesis or NONE"
```

If context-load was run (normal case), the session record exists and this just adds the tail.
If /decided was called throughout, decisions + key_changes are already populated in DB.
If the session crashes before this: only next + in_flight are lost — everything else survived.

Then run `/day-close` to handle steps 4–9 (gap_analysis, subsystem DSBs, MEMORY.md, GitHub discussion, commit).

---

## ⛔ Step 4 — Output compact string

**Always do this last. Do not skip.**

Output the following for Akien to copy into the `/compact` command:

```
preserve: session=YYYY-MM-DDx finalized. Done this session: <2-3 line summary of key changes>.
Next: <top priority>. In-flight: <hypothesis or NONE>.
```

Example:
> `preserve: session=2026-03-22a finalized. Done: D211 local-first routing, boot_check import fix, ollama daemon thread fix, T-resource-history burn tracking. Next: seed location habits for machine_in_use. In-flight: NONE.`

This is the input string for `/compact`. Copy it exactly.

---

## What NOT to do

- Do not rewrite DSB files from scratch — update in place
- Do not re-read files already read this session
- Do not add speculative plans to gap_analysis — only things that happened or were decided
- Do not commit source code as part of savestate — that should already be committed
