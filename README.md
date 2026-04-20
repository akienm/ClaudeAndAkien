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
- **Slate** — daily dated file (`~/.channel/YYYYMMDD.slate.txt`); fresh each day; context-load creates if missing; shows only active tickets, today's decisions, and `/notethat` bookmarks
- **Closed tickets blob** — `~/.channel/closed_tickets.txt`; newest at top; `YYYY-MM-DD | T-id | description`; closed tickets prepend here, not accumulate in the slate
- **Tickets** — unit of work; size S/M/L; priority; status; `github_issue` number for cloud backup; `required_files` pre-declares context; `related_to` links related tickets
- **Queue** — JSONL ticket queue; any session reads next pending; result IS the savestate
- **GitHub Issues** — cloud backup for every ticket; local queue is source of truth for work state; `/day-close` creates issues for tickets missing `github_issue`; each day gets its own GitHub Discussion (not comments on the master thread)

### Execution
- **Spawned minions** — Claude Code sessions as focused workers; smallest possible context per session
- **Leave-running pattern** — minion's loaded context persists; give it the next related ticket via SendMessage
- **Plan approval gate** — L-size tickets auto-run `/filter` before posting plan to channel; blocking filter failures stop execution before any code is written; human approves after filter passes

### Context
- `/context-load` skill — read slate → fetch blob tops → read channel → assemble briefing; **2000-token budget** (~8000 chars; ~4 chars per token); token count reported in briefing output
- **DB document tree** — project docs as traversable graph in Postgres; root node describes structure; traverse only what you need
- No reading 8 files at session start — slate + blob tops replace it

### Skills
- `/context-load` — trail-based startup briefing; starts session record in DB
- `/design` — (optional) mark the start of a design block so /decided knows scope
- `/decided` — close a design block: summarize, draft tickets, run /review per draft, file batch with two-way decision↔ticket links, write to queue + slate + session + palace
- `/review` — filing-time checks (duplicate, already-done-in-code, blocked-by-pending, size sanity, scope-creep, test-plan emit, HIGH-inertia inline approval). Also invokable standalone on a plan/diff/PR
- `/sprint` — single-ticket: claim → work → test → cleanup → doc-refresh → commit+push → close → savestateauto
- `/sprint-batch` — multi-ticket: selector (today-slate, slate:planned, decision:D-..., tag:..., explicit ids); shared setup, topo-sorted dep order, one commit per ticket
- `/fixit` — fast reactive shortcut = /decided + /sprint-batch on just-filed tickets (rewritten 2026-04-20; previously /ticket + /sprint single-ticket)
- `/export-chat` — dump current CC session transcript to claude_chat_logs/YYYY-MM-DD.md for recovery. Flags: --all, --session <id>, --dry-run
- `/commit` — standalone full cycle: tests → stage specific files → commit → pull → push
- `/day-close` — end-of-day: sync docs DB, render views, update GitHub discussion, commit docs
- `/day-close-audit` — automated debris + health check run during /day-close (renamed 2026-04-20 from `/audit` — `/review` handles plan/code review; `/day-close-audit` handles debris)
- `/savestate` — end-of-session ritual: flush summary, record decisions, finalize session record
- `/savestateauto` — lightweight state flush invoked between work steps (no compact)
- `/slate` — start-of-slate planning: orient, review tickets, agree on scope
- `/slateclose` — close a slate: summarize, post to GitHub, archive
- `/probe` — behavioral verification: inject stimulus, observe response, report pass/fail
- `/test-fix` — bounded test-run-and-fix loop (3 passes, then escalate)
- `/validate-files` — audit runtime file placement; candidates-for-removal report
- `/notethat` — lightweight conversation bookmark before it evaporates
- `/note` — insight/decision to notes.log (non-ticket items)
- Domain skills extend these — bind the infrastructure to the problem domain

**Deprecated (for case-study context):**
- `/filter` — merged into `/review` in 2026-04-20; same checks now live in `/review`'s filing-time mode
- `/audit` — renamed to `/day-close-audit` in 2026-04-20 (same behavior, clearer role split from `/review`)

### Batched sprint, in-process pickup
- `/sprint-batch` handles the multi-ticket case (shared setup, topo-sorted dep order, one commit per ticket)
- Ticket pickup on idle migrated to biomimetic engram chain `ENGRAM_TICKET_PICKUP_SCAN → ENGRAM_TICKET_PICKUP_ADOPT → ENGRAM_CODE_INIT` — Igor picks up his own work in-process, no konsole-spawned separate session
- Shared channel (messages.jsonl) remains the coordination substrate across CC + Igor + across-machine
- Multiple CC instances can still pull from the same queue against the same Postgres DB — the worker *daemon* is gone, not the multi-instance capability

**Retired (for case-study context):**
- `worker_daemon.sh` — polled queue and spawned `claude /sprint <id>` per ticket. Replaced by `/sprint-batch` + biomimetic engram pickup. Retired T-retire-worker-foreman (Phase A + B complete 2026-04-19; Phase C destructive cleanup still pending)

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
  session_manager.py   Crash-safe session accumulation in Postgres; append-tool-output records per-call tool summaries for crash reconstruction
  decision_manager.py  Atomic decision recording — DB + log in one call
  slate_manager.py     Daily dated slate files — create, close-ticket, render YYYYMMDD.slate.txt
  github_sync.py       Push tickets to GitHub Issues; create issues for tickets missing github_issue
  cc_queue.py          Ticket queue — list, start, done, add
docs/           Human-readable documentation
  getting_started.md   Prerequisites, setup, minimum viable config
  crash_safe_sessions.md  Before/after crash recovery pattern
  slate_workflow.md    Daily dated slate files, closed-tickets blob, GitHub sync, daily flow
  skills_guide.md      All 6 skills explained + daily sequence
  working_together.md  Field notes: how to work with Claude effectively
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
