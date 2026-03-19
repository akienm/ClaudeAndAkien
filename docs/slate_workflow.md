# The Slate Workflow

A slate is a named, themed bundle of work — roughly a day's worth.

The name comes from film production: "what's on the slate today?"
It's more fluid than an epic or a sprint. It adapts to the day.

---

## The Horizon Cascade

Slates exist at multiple positions, getting vaguer the further out they are:

```
Slate 0 — TODAY        precise: tickets defined, acceptance criteria written
Slate 1 — NEXT         shaped: theme clear, tickets mostly defined
Slate 2 — AFTER NEXT   rough: theme known, tickets fuzzy
Slate 3+ — FUTURE      placeholder: name only, will sharpen as we approach
```

This matches how planning actually works. You don't need tomorrow's details today.
As you close slate 0 and advance, everything shifts down and sharpens.

---

## What a Slate Contains

```python
{
  "id": "slate-2024-01-15",
  "position": 0,
  "name": "Auth refactor",
  "done_when": "All auth middleware tests pass, deployed to staging",
  "tickets": [
    {"id": "T-auth-middleware", "title": "Rewrite auth middleware", "status": "in_progress"},
    {"id": "T-auth-tests",      "title": "Integration test suite",  "status": "pending"},
    {"id": "bug-token-leak",    "title": "Token leak in /refresh",  "type": "adopted_bug", "status": "done"}
  ],
  "notes": "Legal flagged session token storage; compliance deadline end of month"
}
```

**Adopted bugs** are fixes that surfaced during the slate's work — not planned, but absorbed.
They don't change the slate's scope; they're just acknowledged as part of the day's reality.

---

## The Slate File

The slate is rendered to `~/.channel/slate.md` by `slate_manager.py render`.
This file is the first thing `context-load` reads — it's the entry point for any new session.

Because it's rendered from Postgres, it's always current.
Multiple Claude Code tabs all see the same slate.

---

## Daily Flow

```
Morning:
  /context-load                    → reads slate, starts session record
  slate_manager.py show            → confirm what's on today

During work:
  /sprint T-auth-middleware        → claims ticket, works it
  /decided                         → records decision, appends to session
  slate_manager.py close-ticket T-auth-middleware
  slate_manager.py render          → updates slate.md

End of day:
  /day-close                       → syncs docs, posts GitHub update, commits
  slate_manager.py advance         → closes slate 0, shifts everything down
```

---

## Bugs Mid-Slate

When something unexpected surfaces during a slate:
```bash
CC_DB_URL=... python3 claudecode/slate_manager.py add-ticket 0 "bug-xyz" "describe the bug" --bug
```

The `--bug` flag marks it as `adopted_bug` type — visible in the slate but distinct from primary tickets.
This keeps the slate honest about what was planned vs. what reality injected.

---

## Why Not Just Use GitHub Issues?

GitHub issues are the upstream source — `github_sync.py` pulls them into Postgres on sync.
But GitHub doesn't know:
- Which issues are *today's* work vs. next week's
- Which bugs were absorbed mid-slate
- The *done_when* criterion for the current batch
- The horizon cascade (today → next → after)

The slate adds that organizational layer on top.
GitHub is the canonical issue tracker; the slate is the daily work plan.

---

## Multiple Sessions, One Slate

When running multiple Claude Code tabs simultaneously:
- All tabs read the same `slate.md` (rendered from Postgres)
- When a ticket is claimed, mark it in_progress via `cc_queue.py start`
- Other tabs see it as in_progress and don't touch it
- Channel posts show who is working on what

The slate + channel together replace the need for explicit session coordination.
