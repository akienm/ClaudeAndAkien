---
name: notethat
description: Bookmark the current conversation topic before it evaporates. Lighter than /decided — no decision required, no DB write required. Just captures "what we just talked about" into a durable note. Use when the user says /notethat, "note that", "capture this", "don't lose this", or "bookmark this".
---

# Notethat — Conversation Bookmark

Captures the current topic as a durable note before it's lost to context scroll or session end.
Lighter than /decided — no architecture decision required, no session record required.
Think of it as a sticky note on the conversation.

---

## Step 1 — Identify what to capture

From the last few exchanges, identify:
- The core fact, insight, list, or decision fragment being discussed
- Why it matters (one sentence)
- Any action implied (ticket needed? list to rebuild? fix to make?)

If ambiguous: ask "what specifically should I capture?" before proceeding.

---

## Step 2 — Write to a note file

Write to `~/.TheIgors/cc_channel/notes/YYYY-MM-DD_<slug>.md`:

```bash
mkdir -p ~/.TheIgors/cc_channel/notes
```

Format:
```markdown
# <topic in one line>
Date: YYYY-MM-DDThh:mm
Session: <current session ID if known>

## What
<2-5 sentences capturing the fact, list, or insight>

## Why it matters
<one sentence>

## Action implied
<ticket ID if one was created, or "none" or "TBD">
```

---

## Step 3 — Flush to Igor memory

```bash
python3 ~/TheIgors/claudecode/cc_queue.py flush_session <session-id> "<slug>: <one-line summary>"
```

Non-fatal if Igor is down.

---

## Step 4 — Confirm to user

Say: "Noted: <one-line summary of what was captured> → `~/.TheIgors/cc_channel/notes/<filename>`"

---

## What /notethat is NOT

- Not a design decision — use /decided for that
- Not a task — use cc_queue.py add for that
- Not a savestate — that's end of session
- Not a memory update — that's for durable cross-session facts

It's a bookmark. Fast, lightweight, losable if the notes dir is wiped — but survives session end and context compaction.
