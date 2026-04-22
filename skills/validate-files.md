---
name: validate-files
description: Audit skill for TheIgors runtime file placement. Walks ~/TheIgors, ~/.TheIgors, and ~ to find instance data in wrong locations, leaked runtime files, and code that wrote them incorrectly. Produces candidates-for-removal list for discussion. Invoke when Akien says /validate-files, "check for misplaced files", "find leaked files", or "audit file placement".
---

# Validate Files — Igor Runtime Audit Skill

Find files in wrong places. Trace them back to the code that wrote them. Never delete — produce candidates list for discussion.

---

## Three-Tier Runtime Model

Before scanning, internalize the correct layout:

| Tier | Path | What belongs here |
|---|---|---|
| Machine-global | `~/.TheIgors/local/` | `machines.json`, cluster config — environment, not Igor |
| Database-global | `~/.TheIgors/<db_name>/` | milieu, soul, word_graph.db, cache/, SOUL.md, IDENTITY.md |
| Instance-local | `~/.TheIgors/<db_name>/<instance>/` | wild-*.db, .env, jobs/, logs/, inbox/, outbox/, workspace/, warm_context.*.json, arbiter/ |
| Source tree | `~/TheIgors/` | Code only. No runtime data ever. |
| Home | `~` | No Igor files. Ever. |

Current DB name: `Igor-wild-0001`
Current instance: `Igor-wild-0001` (DB and instance share the name currently)

---

## Step 1 — Scan Source Tree for Runtime Leakage

```bash
# Files that look like runtime data in the source tree
find ~/TheIgors -maxdepth 4 \
  -not -path "*/venv/*" \
  -not -path "*/.git/*" \
  -not -path "*/node_modules/*" \
  \( \
    -name "*.db" -o \
    -name "*.log" -o \
    -name "*.pid" -o \
    -name "*.json" -not -name "package*.json" \
    -not -path "*/design_docs*" \
    -not -path "*/claudecode/book_learner*" \
  \) \
  -type f 2>/dev/null
```

Flag anything that is:
- `*.db` files (SQLite databases — should be in `~/.TheIgors/`)
- `*.log` files
- `*.pid` files
- JSON files that look like state (not config, not design docs, not package.json)
- Any file in `~/TheIgors/` matching `warm_context*`, `*.env`, `reading_state*`

---

## Step 2 — Scan ~/.TheIgors Root for Misplaced Files

```bash
# Files at ~/.TheIgors/ root that should be inside a DB folder
ls -la ~/.TheIgors/ 2>/dev/null
```

**Expected at root** (machine-global, intentionally shared):
- `local/` directory — machines.json, cluster config

**Expected at root** (database-global, currently misplaced — should be under `~/.TheIgors/Igor-wild-0001/`):
- `word_graph.db` — should be database-global under DB folder
- `milieu_global.json` — database-global, currently at root (misplaced)
- `SOUL.md` — database-global, currently at root (misplaced)
- `cache/` — could be machine-global (shared across DBs) or database-global; flag for decision

**Clearly misplaced** (should be instance-local under `~/.TheIgors/Igor-wild-0001/`):
- `learn_queue.json` — instance-local (we created this)
- `drain_learn_queue.pid` — instance-local (we created this)
- Any `warm_context.*.json`
- Any `*.pid` files

For each misplaced file: note the path and check Step 4 to find the code that wrote it there.

---

## Step 3 — Scan ~ Home Directory

```bash
# Igor files that leaked to home directory
ls -la ~ | grep -iE "igor|wild|theigors|word_graph|milieu|warm_context|learn_queue" 2>/dev/null

# Also check for hidden files
ls -la ~/.igor* ~/.wild* ~/.learn* ~/.milieu* 2>/dev/null
```

Flag anything Igor-related that is directly in `~`. Nothing should be there.

---

## Step 4 — Trace Misplaced Files Back to Source

For each flagged file, find the code that wrote it:

```bash
# Replace FILENAME with the basename of the misplaced file
grep -r "FILENAME\|learn_queue\|milieu_global\|word_graph\|drain_learn_queue" \
  ~/TheIgors/wild_igor/igor/ \
  --include="*.py" -l 2>/dev/null
```

Then read the relevant file to find the exact path construction:
```bash
grep -n "Path\|os.path\|expanduser\|FILENAME" ~/TheIgors/wild_igor/igor/PATH_TO_FILE.py
```

For each misplaced file, record:
- Current (wrong) path
- Correct path per the three-tier model
- File + line number that constructed the wrong path
- Whether it's a hardcoded path or a missing env var lookup

---

## Step 5 — Produce Candidates Report

Output a structured report:

```
CANDIDATES FOR DISCUSSION
=========================

[WRONG_LOCATION] path/to/file
  Should be: correct/path
  Written by: source_file.py:line_number
  Fix: change Path(...) to use instance_dir / "filename"
  Risk: [low=just a path change | medium=other code reads this path | high=live DB]

[REVIEW_NEEDED] path/to/file
  Currently: ~/.TheIgors/ root
  Question: database-global or instance-local?
  Decision needed before moving.

[CONFIRMED_OK] path/to/file
  Reason: intentionally machine-global (e.g. local/machines.json)
```

---

## Step 6 — Do NOT Delete Anything

Present the report to Akien. Wait for explicit go-ahead on each candidate.
Some will be deletable immediately. Some will require code fixes first (remove the file
after fixing the writer, not before). Some may trigger new tickets.

High-risk files (anything with live data, the active DB, .env): always flag as high-risk,
never remove without explicit instruction.

---

## Notes for Instance Refactor Ticket

While scanning, also note:
- Files that would move cleanly if an Instance object managed paths
- Files shared across instances that need the database-global vs instance-local split resolved
- Any hardcoded `Igor-wild-0001` strings in source (these break multi-instance)
- Word graph: flag whether it looks instance-specific or truly shared

These observations feed the Instance refactor design — capture them in the report.
