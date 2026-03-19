# Getting Started

This framework turns Claude Code sessions into coordinated workers on a shared codebase.
Instead of one big session that does everything, you get focused sessions that share state,
hand work to each other, and survive crashes without losing what was built.

---

## Prerequisites

- Claude Code installed
- Postgres running (local is fine — `docker run -p 5432:5432 postgres` works)
- `psycopg2` Python package (`pip install psycopg2-binary`)
- `gh` CLI for GitHub sync (optional)

---

## Step 1 — Set environment variables

Add to your shell profile or `.env`:

```bash
export CC_DB_URL="postgresql://user:password@localhost/your_db"
export CC_GH_REPO="your-org/your-repo"          # optional, for github_sync
export CC_RUNTIME_DIR="$HOME/.channel"           # where channel + state files live
```

---

## Step 2 — Create the database tables

```bash
python3 claudecode/session_manager.py seed       # creates sessions table
python3 claudecode/slate_manager.py seed         # creates slates table (edit seed data first)
python3 claudecode/decision_manager.py add D001 "first-decision" "defined" "describe it"
```

The tables auto-create on first use. You can also run `CREATE TABLE` statements manually
from the docstrings in each file.

---

## Step 3 — Install the skills

Copy the `skills/` directory to your Claude Code skills location:

```bash
# Find your skills directory
ls ~/.claude/skills/

# Copy skills
for skill in context-load decided sprint commit workstep day-close; do
  mkdir -p ~/.claude/skills/$skill
  cp skills/$skill.md ~/.claude/skills/$skill/SKILL.md
done
```

---

## Step 4 — Start a session

```bash
# Load context (reads slate + channel + starts session record)
/context-load

# Pick up a ticket and work it
/sprint T-001

# When done
/decided

# End of day
/day-close
```

---

## Step 5 — Adapt for your project

The tools use environment variables throughout — no hardcoded paths.
Things to customize:

- `slate_manager.py cmd_seed()` — seed your initial slates
- Skill files — update repo names, project-specific conventions
- Channel path — defaults to `~/.channel/`, configurable via `CC_RUNTIME_DIR`

---

## The minimum viable setup

If you just want crash-safe session tracking without everything else:

```bash
# At session start:
CC_DB_URL=... python3 claudecode/session_manager.py start "2024-01-15a" "What you're working on"

# After each unit of work:
CC_DB_URL=... python3 claudecode/session_manager.py append-change "What you just did"

# At session end (optional — crash-safe without it):
CC_DB_URL=... python3 claudecode/session_manager.py finalize "2024-01-15a" "What's next" "In-flight hypothesis"
```

That's it. On crash, `session_manager.py show 1` reconstructs what was done.
