# Framework Overview

## The Core Insight

A Claude Code session is not just a coding assistant — it's a worker with a context window,
tools, and the ability to coordinate with other sessions. The framework treats CC sessions
as first-class agents that share state through a database and communicate through a channel.

## The Trail Pattern

All persistent data follows the same shape: a trail through time.

- **Activation trails** — which nodes fired, in what sequence, with what weights
- **Decision logs** — prepend-newest-first; read top until context sufficient
- **Channel messages** — append-only JSONL; any participant reads the tail
- **Logs** — newest at top; cold context at bottom; rarely need the bottom

Trails give you gradients for free: rising heat = active/important, fading heat = deprioritize.

## The Blob Reading Pattern

Any prepend-newest-first log is a "blob" in this framework's terminology.

Reading discipline:
1. Read the slate (what's active — 5-10 lines)
2. Slate points to relevant blobs
3. Read top 40 lines of each blob (newest = most relevant)
4. Stop when context is sufficient

This replaces reading 8 files at session start. Total context load: ~60-100 lines.

## The Minion Pattern

For code-writing, documentation, migrations, or any focused task:

1. Designer session identifies the work and writes a ticket
2. Ticket is the complete brief — everything the minion needs
3. Minion is spawned (new CC session or Agent tool call)
4. Minion announces on channel, works the ticket, posts result
5. If minion finishes and related work exists: SendMessage to continue (leave running)
6. Result written to queue IS the record — no scribe, no savestate ritual

## Human Checkpoints

Every workflow segment ends at a human touchpoint:
- Plan approval (before L-size implementation)
- Progress check-in (mid-sprint on long tickets)
- Completion review (result posted to channel, human sees it)

Automation works *between* checkpoints, never past them.

## Configuration Discipline

- `.env` — secrets and API keys ONLY
- `switches.ini` — instance flags with safe defaults (if absent, system works)
- DB machines table — routing decisions, performance data, instance capabilities
- Code — behavior; never config values embedded in code
