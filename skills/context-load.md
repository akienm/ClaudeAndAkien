# context-load — Trail-based startup context

Invoke when starting a session, picking up a ticket, or when you need to orient quickly.
Reads the slate, finds relevant blobs, reads their tops. Returns a focused briefing.
No Igor required. No Postgres required.

---

## Step 1 — Read the slate

```bash
cat ~/.channel/slate.md
```

The slate tells you:
- What's actively being worked (tickets)
- Which blobs are relevant and where they live
- One-paragraph current context

---

## Step 2 — Read blob tops

For each blob listed in the slate, read the top 40 lines only:

```bash
head -40 <blob-path>
```

Blobs are newest-first (prepend convention). The top is the hottest context.
Stop reading when you have enough. You rarely need the bottom.

Standard blobs (always read if no slate):
- `~/.claude/projects/-home-akien-TheIgors/memory/MEMORY.md` — project memory index
- `~/.channel/messages.jsonl` — recent channel activity (last 10 lines)
- `~/TheIgors/design_docs_for_igor/decisions_log.dsb` — top 30 lines = recent decisions

---

## Step 3 — Read recent channel

```bash
python3 $PROJECT_ROOT/claudecode/channel.py read 10
```

See what other sessions have posted recently. Who is working on what.

---

## Step 4 — Assemble briefing

Synthesize into 5-10 lines:
- Current active tickets
- Key design context (1-2 sentences per active area)
- What other sessions are doing (if any)
- What you should NOT touch (in-progress by another session)

Output format:
```
CONTEXT LOAD — <timestamp>
Active: <ticket IDs>
Design thread: <one line>
Channel: <recent activity or "quiet">
Do not touch: <files/areas in use>
Ready.
```

---

## Step 5 — Start session record in DB

Check if a session is already in progress (e.g. prior tab or crash recovery):
```bash
DB=$CC_DB_URL
python3 $PROJECT_ROOT/claudecode/session_manager.py current
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py show 1
```
If a prior unfinalized session exists, surface it in the briefing: "previous session Xxx has partial record — last change: Y"

Determine the session ID: today's date + next letter (check `show 3` to see what's used).
Start the session (writes ID to state file — /decided reads it automatically from here on):
```bash
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py start "YYYY-MM-DDx" "Theme: one line"
```
This creates a partial record AND writes `~/.channel/current_session.txt`. Crash loses nothing — key changes accumulate via /decided without any ID argument.

---

## Hard rules

- Never read more than 40 lines of any blob — if you need more, something is wrong with the blob
- Never load CLAUDE.md as your primary context — slate + blob tops replace it
- If slate is missing: fall back to MEMORY.md + decisions top + channel read
