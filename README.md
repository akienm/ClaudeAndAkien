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
- `/context-load` — trail-based startup briefing; starts session record in DB
- `/sprint` — claim ticket → work it → post result → write done flag → exit
- `/decided` — close-out ritual: record decision → accumulate to session record → verify tests → next
- `/commit` — full cycle: tests → audit → stage specific files → commit → pull → push
- `/day-close` — end-of-day: sync docs DB, render views, update GitHub discussion, commit docs
- Domain skills extend these — bind the infrastructure to the problem domain

### Worker Daemon
- `worker_daemon.sh` — polls queue, spawns `claude /sprint <id>` per ticket, watches for done flag
- Resets timed-out tickets to pending so they retry automatically
- Exits cleanly when queue drains; relaunch via `cc_queue.py worker-launch`
- S/M tickets fully autonomous; L tickets post plan to channel before proceeding

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
skills/         Claude Code slash skills — context-load, sprint, decided, commit, day-close
claudecode/     Claude Code integration helpers
  session_manager.py   Crash-safe session accumulation in Postgres
  decision_manager.py  Atomic decision recording — DB + log in one call
  slate_manager.py     Slate CRUD + horizon cascade + render to ~/.channel/slate.md
  github_sync.py       Pull GitHub issues into Postgres for planning
  cc_queue.py          Ticket queue — list, start, done, add
docs/           Human-readable documentation
  getting_started.md   Prerequisites, setup, minimum viable config
  crash_safe_sessions.md  Before/after crash recovery pattern
  slate_workflow.md    Horizon cascade, daily flow, adopted bugs
  skills_guide.md      All 6 skills explained + daily sequence
```

---

## Crash-Safe Sessions

The traditional "savestate at end of session" pattern fails exactly when you need it most —
machine lockup, stuck modifier keys, Claude Code running out of context.

The new pattern accumulates state throughout the session:

```
/context-load     → session record created in DB immediately
  /decided        → each decision written to DB atomically
  /workstep gate  → loop state written at each phase transition
/day-close        → synthesizes next/in-flight; renders views; commits
```

A crash loses only two synthesis fields (`next_session` + `in_flight`) — the prediction
about the future that only a live Claude can provide. Everything else survives.

See `docs/crash_safe_sessions.md` for the full pattern.

---

## Key Principles

1. **State in the database** — not in files, not in session memory, not in config
2. **Channel as shared truth** — all participants see the same conversation
3. **Minions have minimal context** — a ticket is a complete brief; no sprawling onboarding
4. **Blob tops are enough** — newest-first + read until sufficient = fast, focused context
5. **Trails, not snapshots** — temporal sequences of activity are the indexing mechanism
6. **Human at every checkpoint** — automation works between touchpoints, never past them
7. **Crash-safe by default** — every unit of work writes to DB before it closes; session record accumulates throughout; finalize adds synthesis only

---

## Getting Started

See `docs/getting_started.md` for the full setup guide.

The minimum viable setup — crash-safe session tracking with nothing else:

```bash
# At session start:
CC_DB_URL=... python3 claudecode/session_manager.py start "2024-01-15a" "What you're working on"

# After each unit of work:
CC_DB_URL=... python3 claudecode/session_manager.py append-change "What you just did"

# At session end (optional — crash-safe without it):
CC_DB_URL=... python3 claudecode/session_manager.py finalize "2024-01-15a" "What's next" "In-flight hypothesis"
```

On crash: `session_manager.py show 1` reconstructs what was done.

---

## Origin

Extracted from [TheIgors](https://github.com/akienm/TheIgors) — an AI agent with persistent
memory, habit-based cognition, and a word graph inference engine. The framework pieces here
are the scaffolding that makes Igor work; they're useful without Igor.

---

*Built with Claude Sonnet 4.6*
