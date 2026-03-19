# ClaudeAndAkien

A general-purpose agentic framework for building AI-assisted applications with Claude Code.

Built by Akien Maciain and Claude, extracted from the TheIgors project.

---

## What This Is

A framework for building applications where Claude Code sessions are first-class workers —
not just a coding assistant, but a coordinated fleet of specialized agents sharing state,
communicating through a common channel, and handing work between each other via a ticket system.

The patterns here are domain-agnostic. The Igor-specific parts (habit system, word graph,
emotional milieu) live in TheIgors. This repo contains the frame.

---

## The Layers

### Storage
- **Postgres** as the primary state store — all persistent data, all participants share it
- **db_proxy** — unified database access with SQLite→Postgres translation shim; timing, reconnect, slow query logging
- **Blob/trail pattern** — append-only logs with newest-first prepend; read tops until context sufficient, stop
- **Config split** — `.env` for secrets only; `switches.ini` for instance flags with safe defaults

### Communication
- **Standalone channel** (`channel/`) — append-only JSONL at `~/.channel/messages.jsonl`; post/read/listen/sessions
- **Web server** (`web/`) — Starlette/uvicorn; WebSocket for real-time; mirrors to channel JSONL
- No participant depends on another being up — channel persists across restarts

### Coordination
- **Slate** — shared source of truth for what's active (`~/.channel/slate.md`)
- **Tickets** — unit of work; size S/M/L; priority; status; result written back on completion
- **Queue** — JSONL ticket queue; any session reads next pending; result IS the savestate

### Execution
- **Spawned minions** — Claude Code sessions as focused workers; smallest possible context per session
- **Leave-running pattern** — minion's loaded context persists; give it the next related ticket via SendMessage
- **Plan approval gate** — L-size tickets post plan to channel before any code; human approves

### Context
- `/context-load` skill — read slate → fetch blob tops → read channel → assemble briefing; ~60 lines total
- **DB document tree** — project docs as traversable graph in Postgres; root node describes structure; traverse only what you need
- No reading 8 files at session start — slate + blob tops replace it

### Skills
- `/sprint` — claim ticket → work it → post result → surface next
- `/commit` — full cycle: tests → audit → stage specific files → commit → pull → push
- `/decided` — close-out ritual: record decision → update ticket → verify tests → next
- `/context-load` — trail-based startup briefing
- Domain skills extend these — bind the infrastructure to the problem domain

### Workflow
- Every workflow segment ends with **interact with the human**
- Human touchpoints: plan approval, progress check-in, completion review
- Minions work between touchpoints; Designer session holds the arc

### Ops
- **Boot diagnostics** — check dependencies at startup (DB reachable, schema version, required services)
- **Health endpoint** — `/api/health` always returns 200 if server is up
- **Multi-instance routing** — machines table in DB, not config files; routing decisions from live data
- **Forensic logging** — timestamped, state changes, tool outputs, errors; prepend-newest-first

---

## What's In This Repo

```
channel/        Shared JSONL channel — post/read/listen, no server required
db/             db_proxy — unified DB access, SQLite/Postgres shim, timing
web/            Standalone web server — channel WebSocket, health, file endpoints
skills/         Claude Code slash skills — sprint, commit, decided, context-load
claudecode/     Claude Code integration helpers
docs/           Framework documentation (English, maintained periodically)
```

---

## Key Principles

1. **State in the database** — not in files, not in session memory, not in config
2. **Channel as shared truth** — all participants see the same conversation
3. **Minions have minimal context** — a ticket is a complete brief; no sprawling onboarding
4. **Blob tops are enough** — newest-first + read until sufficient = fast, focused context
5. **Trails, not snapshots** — temporal sequences of activity are the indexing mechanism
6. **Human at every checkpoint** — automation works between touchpoints, never past them

---

## Origin

Extracted from [TheIgors](https://github.com/akienm/TheIgors) — an AI agent with persistent
memory, habit-based cognition, and a word graph inference engine. The framework pieces here
are the scaffolding that makes Igor work; they're useful without Igor.

---

*Built with Claude Sonnet 4.6*
