# Skills Guide

Claude Code skills are Markdown files that expand into instructions when invoked with `/skill-name`.
This framework ships a set of pre-built skills that encode the workflow discipline.

---

## Installing Skills

```bash
# Copy skills to your Claude Code skills directory
for skill in context-load decided sprint commit workstep day-close; do
  mkdir -p ~/.claude/skills/$skill
  cp skills/$skill.md ~/.claude/skills/$skill/SKILL.md
done
```

After installation, `/context-load`, `/decided`, etc. are available in any Claude Code session.

---

## The Skills

### `/context-load`
**When**: start of every session.
**What it does**: reads the slate, fetches blob tops, reads channel, assembles a focused briefing,
creates a session record in DB, posts session ID to channel.
**Why it matters**: replaces reading 8 files at session start. Slate + blob tops = ~60 lines total.

### `/sprint <ticket-id>`
**When**: picking up a focused unit of work.
**What it does**: claims a ticket from the queue, works it following workstep discipline,
posts progress to channel, marks done, surfaces next.
**Why it matters**: one ticket per sprint — no scope creep. Result IS the state record.

### `/workstep`
**When**: beginning any implementation task.
**What it does**: enforces the full work loop — orient → plan → (compact for L-size) → implement → close.
Records phase transitions to session DB. Plan approval gate before any code.
**Why it matters**: prevents the "just start coding" trap. Every phase transition is recorded.

### `/decided`
**When**: after any unit of work closes — a ticket, a design decision, a debugging session.
**What it does**: records decision to DB + DSB, appends to session record (key changes + decisions),
updates ticket, checks test coverage, notes what's next.
**Why it matters**: this is the atomic save point. Run it frequently — a crash between /decided calls
loses at most one unit of work.

### `/commit`
**When**: at logical checkpoints during implementation.
**What it does**: runs tests → audits diff → stages specific files → commits → pulls → pushes.
Syncs docs DB if any `.dsb` files are staged.
**Why it matters**: full cycle every time. Never partial.

### `/day-close`
**When**: end of work day (or significant work block).
**What it does**: syncs docs DB, renders sessions.md, updates gap_analysis + subsystem docs,
posts GitHub discussion update, commits docs-only changes.
**Why it matters**: the documentation maintenance that used to happen in savestate. Once a day, not per session.

---

## Adapting Skills for Your Project

Each skill file is plain Markdown. Open it and change:
- `$PROJECT_ROOT` → your actual project path
- `$CC_DB_URL` → your DB connection string (or keep as env var reference)
- GitHub discussion ID → your project's discussion thread
- Subsystem names → your project's modules

The discipline (plan gate, forensic logging, atomic record-keeping) is the valuable part.
The specific paths are just wiring.

---

## The Skill Sequence in a Normal Day

```
Morning startup:
  /context-load          ← always first

During work (repeat):
  /workstep              ← start each ticket
  [implement]
  /decided               ← close each ticket/decision
  /commit                ← at logical checkpoints

End of day:
  /day-close             ← once, wraps up docs + GitHub
```

---

## Adding Your Own Skills

Create `~/.claude/skills/my-skill/SKILL.md` with frontmatter:
```markdown
---
name: my-skill
description: What this skill does and when Claude should invoke it.
---

# My Skill

Instructions here...
```

Claude Code will auto-discover it. Describe the trigger conditions clearly in the `description` —
that's what determines when Claude invokes it automatically vs. waiting to be asked.
