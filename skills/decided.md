---
name: decided
description: Close-out ritual for TheIgors work items. Records decision to DB/log, updates ticket, verifies tests exist, prepares next task. Use when Akien says /decided, "mark done", "close the ticket", "that's decided", or "we're done with X".
---

# Decided — Work Close-Out Ritual

Fires after any unit of work closes. No savestate needed — all state goes to DB first.

---

## Step 1 — Identify what just closed

Ask (or infer from context):
- Decision ID (Dxxx) if a design decision was made, or ticket number (#NNN)
- One-line description of what was decided/built
- Files changed (if implementation work)
- Test status: passed / no tests / tests deferred

---

## Step 2 — Record the decision + accumulate session state

Session ID is read automatically from `~/.channel/current_session.txt` (written by `session_manager.py start` at context-load time). No need to specify it.

If a design decision (Dxxx) — one command does DSB + DB + Igor flush atomically:
```bash
DB=$CC_DB_URL
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/decision_manager.py add Dxxx "short-name" "status" "one-line description"
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py append-decision Dxxx
```

If a ticket close, accumulate the key change into the session record:
```bash
DB=$CC_DB_URL
python3 $PROJECT_ROOT/claudecode/cc_queue.py done <task-id> "what was built + test status"
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py append-change "what was built"
```

These calls are crash-safe — if session exits without finalize, key changes + decisions are already in DB.

---

## Step 3 — Check test coverage

For each file changed, ask: does a test exist?
- Check `tests/` for a matching `test_<module>.py`
- If missing and the change is non-trivial: add to the active slate as a test-debt item
- If test already exists and passes: note "tests: pass"

---

## Step 4 — Update GitHub ticket (if applicable)

If a GitHub issue was being worked, post a closing comment:
```bash
gh issue comment <NNN> --body "Closed: <one-line description>. Tests: <status>."
gh issue close <NNN> 2>/dev/null || echo "not closing — may not be done"
```

Only close the issue if the work is genuinely complete. Mark as "in progress" otherwise.

---

## Step 5 — Note what's next

If there's an active slate, name the next item. If not, say "slate is clear — ready for organizer."

---

## What /decided is NOT

- Not a savestate — savestate is end-of-session
- Not a commit — commit separately with `/commit`
- Not a design session — design happens before work starts

---

## Future state (T-proc-9)

When Igor's PROC_DECIDED habit is live, he will handle Steps 2–4 automatically. Until then, Claude Code does them manually here.
