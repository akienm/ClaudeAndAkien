# sprint — Pick up a ticket, work it, report back

Invoke at the start of a focused work session. Loads context, claims a ticket,
works it, posts result to channel and queue. One ticket per sprint.

Arguments (optional):
  /sprint <ticket-id>    — work a specific ticket
  /sprint                — pick the next pending ticket by priority

---

## Step 0 — Pre-load deferred tools

The `Skill` tool is deferred at session start — call ToolSearch first to load its schema,
otherwise the first `/context-load` invocation fails with "Invalid tool parameters":

```
ToolSearch: select:Skill,Bash,Read,Edit,Grep,Glob
```

Do this before anything else. It is instant and silent.

---

## Step 1 — Load context

Always run `/context-load` first. Get the briefing. Confirm the session record is started in DB.

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

Always follow workstep discipline (see /workstep). Key gates:
- S/M size: implement directly after reading the relevant files.
- L size: always post the plan to channel first, then wait for Akien approval before coding.
- Always read every file before editing it.
- Always add forensic logging on non-trivial changes.

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

- Always sprint one ticket at a time — no scope creep.
- Always get plan approval before coding an L-size ticket.
- Always check the in_progress flag before claiming — another session may already hold it.
- Always post to channel at start, on progress, and on completion.
- Always run /decided after each ticket — decisions land in DB before session ends.
