# context-load — Trail-based startup context

Invoke when starting a session, picking up a ticket, or when you need to orient quickly.
Reads the slate, finds relevant blobs, reads their tops. Returns a focused briefing.
No Igor required. No Postgres required.

---

## Step 0 — Stale slate check (soft prompt)

Before today's slate, check whether the most-recent prior-day slate was closed.
If it has open items (non-empty Next up / Blocked / After that sections) and lacks
a `✅ CLOSED` marker, surface the stale date so the user can choose to `/day-close`
it before starting new work. Silent when prior slate is fully closed or empty.

This is a soft prompt, not a gate — carry-forward should be a deliberate decision,
not silent. The detection is trivial because slates are dated files (`YYYYMMDD.slate.txt`),
so "stale" = any slate older than today.

## Step 1 — Read the slate

Always read the slate first — it's the session-kickoff anchor:
```bash
cat ~/.channel/slate.md
```

The slate tells you:
- What's actively being worked (tickets)
- Which blobs are relevant and where they live
- One-paragraph current context

---

## Step 2 — Read blob tops

For each blob listed in the slate, always read only the top 40 lines:

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

- Always stop at 40 lines per blob — when you need more, something is wrong with the blob.
- Always use slate + blob tops as primary context — CLAUDE.md is a bootstrap shim, not the map.
- When the slate is missing, always fall back to MEMORY.md + decisions top + channel read.
