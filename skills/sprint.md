# sprint — Pick up a ticket, work it, report back

Invoke at the start of a focused work session. Loads context, claims a ticket,
works it, posts result to channel and queue. One ticket per sprint.

Arguments (optional):
  /sprint <ticket-id>    — work a specific ticket
  /sprint                — pick the next pending ticket by priority

---

## Step 1 — Load context

Run `/context-load` first. Get the briefing. Confirm session record is started in DB.

---

## Step 2 — Claim ticket

If ticket ID given: read it from queue.
If no ID: find next pending by priority:
```bash
python3 $PROJECT_ROOT/claudecode/cc_queue.py list
```

Mark ticket as in_progress:
```bash
python3 $PROJECT_ROOT/claudecode/cc_queue.py start <ticket-id>
```

Post to channel:
```bash
python3 $PROJECT_ROOT/claudecode/channel.py post "claimed <ticket-id>: <title>" --as <tab>
```

Record in session:
```bash
DB=$CC_DB_URL
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py append-change "sprint: started <ticket-id>"
```

---

## Step 3 — Work the ticket

Follow workstep discipline (see /workstep). Key gates:
- S/M size: implement directly after reading relevant files
- L size: post plan to channel first, wait for Akien approval before coding
- Read every file before editing
- Forensic logging for non-trivial changes

Post progress updates to channel:
```bash
python3 $PROJECT_ROOT/claudecode/channel.py post "progress: <what just happened>" --as <tab>
```

---

## Step 4 — Complete

Mark done and write result:
```bash
python3 $PROJECT_ROOT/claudecode/cc_queue.py done <ticket-id> "<one paragraph summary>"
```

Record in session:
```bash
DB=$CC_DB_URL
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py append-change "sprint: closed <ticket-id> — <one line>"
```

Post completion to channel:
```bash
python3 $PROJECT_ROOT/claudecode/channel.py post "done: <ticket-id> — <one line summary>" --as <tab>
```

Update slate if this ticket was listed there:
```bash
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/slate_manager.py close-ticket <ticket-id>
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/slate_manager.py render
```

Run /decided to record any decisions made.

---

## Step 5 — Surface next

```bash
python3 $PROJECT_ROOT/claudecode/cc_queue.py list
```

Post next ticket to channel so Akien or another session can pick it up. Then either:
- Start another sprint (if context is fresh and next ticket is related)
- End session (post "session ending" to channel)

---

## Hard rules

- One ticket per sprint — no scope creep
- L-size tickets: plan approval required before any code
- Never claim a ticket already marked in_progress by another session
- Always post to channel at start, on progress, and on completion
- Run /decided after each ticket — decisions must land in DB before session ends
