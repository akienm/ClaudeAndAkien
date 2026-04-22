# The Slate Workflow

A slate is today's work plan — a live, dated file that travels through the day with you.

The name comes from film production: "what's on the slate today?"
It adapts to the day. It's not a sprint backlog or an epic — it's what's actually happening right now.

---

## The Slate File

Each day gets its own dated file: `~/.channel/YYYYMMDD.slate.txt`.

Context-load creates it if it doesn't exist. Each day starts fresh — closed tickets from
prior days don't carry forward. The file is the entry point for any new session.

```
# Slate 2024-01-15

## Active
- T-auth-middleware: Rewrite auth middleware  [in_progress]
- T-auth-tests: Integration test suite  [pending]

## Done today
- ~~T-token-leak~~ ✓  Token leak in /refresh

## Notes
- 09:42 — deadline-context: compliance deadline end of month — drove scope decision on auth

## Tools
...
```

---

## Closed Tickets

Closed tickets don't accumulate in the daily slate — they go to a separate blob:

```
~/.channel/closed_tickets.txt
```

Format: newest at top — `YYYY-MM-DD | T-id | description`

Tail from the top until satisfied. The daily slate stays clean.

---

## What a Ticket Contains

```python
{
  "id": "T-auth-middleware",
  "title": "Rewrite auth middleware",
  "description": "...",
  "size": "M",
  "priority": 1,
  "status": "in_progress",
  "github_issue": 47,           # GitHub issue number, linked at creation
  "required_files": [...],      # pre-declared for sprint context loading
  "related_to": [...]           # links tickets sharing context
}
```

**`github_issue`**: every ticket links to a GitHub issue. The local queue is the work-state
source of truth; GitHub is the cloud backup. If the local drive dies, GitHub is what survives.

---

## Daily Flow

```
Start of day:
  /context-load       → creates today's dated slate if missing; reads it; starts session record

During work:
  /sprint T-auth-middleware    → claims ticket, works it
  /decided                     → records decision; today's D-numbers appear in the slate
  /notethat                    → bookmarks an idea; headline appended to today's slate
  cc_queue.py done T-id "..."  → closes ticket; prepends line to closed_tickets.txt

End of day:
  /day-close          → syncs docs DB, creates new GitHub Discussion for today's record,
                        creates GitHub Issues for any tickets missing github_issue number,
                        commits docs
```

---

## Notes Mid-Slate

Use `/notethat` to capture ideas, insights, or conversation fragments that shouldn't be lost:

```
/notethat
```

Full note lands in `~/.channel/notes/YYYY-MM-DD_<slug>.md`.
One-liner headline appended to today's slate so context-load picks it up next session.

For structured design decisions, use `/decided` instead — that's for architectural choices with D-numbers.

---

## GitHub: Push, Not Pull

Local cc_queue is canonical for work state. GitHub Issues are the durable backup:

- Every ticket carries a `github_issue` field (GitHub issue number)
- GitHub issue titles include the cc_queue slug: `T-auth-middleware: Rewrite auth middleware`
- `/day-close` creates GitHub Issues for any ticket missing `github_issue`
- Each day gets its own GitHub Discussion (not a comment on the master plan thread)

The master plan thread is for roadmap and architecture. Daily Discussions are the daily record.

---

## Multiple Sessions, One Slate

When running multiple Claude Code tabs simultaneously:
- All tabs read the same dated slate file
- When a ticket is claimed, mark it in_progress via `cc_queue.py claim`
- Other tabs see it as in_progress and don't touch it
- Channel posts show who is working on what

The slate + channel together replace the need for explicit session coordination.
