---
name: day-close
description: End-of-day docs + commit ritual for TheIgors project. Syncs docs DB, renders sessions.md, updates gap_analysis + subsystem DSBs, posts GitHub discussion, commits docs-only changes. Replaces savestate Steps 4-9. Use when Akien says /day-close, "end of day", "wrap up docs", or "close out the day".
---

# Day-Close — End-of-Day Docs Ritual

Runs once at end of day (or end of a significant work block).
Session state is already in DB — this is just the rendered-view + docs sync step.
All steps are mechanical except Step 3 (gap analysis) which needs judgment.

---

## Step 1 — Read today's session record

```bash
DB=$CC_DB_URL
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py show 1
```

This tells you: decisions made, key changes, subsystems touched.
Skim it — you need to know which DSBs to update in Step 4.

---

## Step 2 — Sync docs DB + render sessions.md

```bash
DB=$CC_DB_URL

# Sync all DSB files to Postgres (fast — ~3s for all 18 files)
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/docs_sync.py sync

# Render sessions.md from DB (authoritative view)
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py render
```

---

## Step 3 — Update gap_analysis (judgment required)

Read the current gap_analysis files to understand open gaps:
```bash
head -60 ~/TheIgors/design_docs/gap_analysis.md
```

For each gap that was **closed** today:
- Add root cause + fix to `design_docs/gap_analysis.md`
- Mirror to `design_docs_for_igor/gap_analysis.dsb`: change status to `closed`

For each **new gap** surfaced today:
- Add to `design_docs/gap_analysis.md` as open item
- Add to `design_docs_for_igor/gap_analysis.dsb`: new `G-xxx|status|description` line

If no gaps opened or closed: skip this step.

---

## Step 4 — Update affected subsystem DSBs

For each subsystem touched today (infer from session key_changes):
- Update `updated=` date in the DSB header
- Update only the specific lines that changed — do not rewrite

Common subsystems and their DSBs:
- `subsystem_memory.dsb` — cortex, db_proxy, models changes
- `subsystem_cognition.dsb` — thalamus, BG, NE, milieu changes
- `subsystem_inference.dsb` — reasoners, tier routing changes
- `subsystem_tools.dsb` — tool additions or changes
- `subsystem_reading.dsb` — ebook_reader, watcher changes
- `subsystem_self_edit.dsb` — self_edit, hot_reload changes
- `subsystem_web_network.dsb` — server.py, cc_bridge, channel changes

For today's tooling-only sessions (claudecode/ changes only): skip subsystem DSBs.
Run docs_sync after any DSB edits:
```bash
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/docs_sync.py sync
```

---

## Step 5 — Update MEMORY.md if persistent facts changed

Read `~/.claude/projects/-home-akien-TheIgors/memory/MEMORY.md`.
Update only if something **non-obvious and durable** changed — architecture, known issues, priority shifts.
Do not add ephemeral notes. Do not duplicate what's already in sessions.md.

---

## Step 6 — Post GitHub discussion #62

Compose a brief session summary (3-5 bullets) and post:
```bash
gh api graphql -f query='mutation {
  addDiscussionComment(input: {
    discussionId: "D_kwDORR89g84AkjSM",
    body: "## Session YYYY-MM-DDx — <theme>\n\n**Decisions**: D130, D131\n**Done**: ...\n**Next**: ..."
  }) { comment { id } }
}'
```

Keep it short — it's a log entry, not an essay.

---

## Step 7 — Commit docs

Stage only docs/memory/design files — never source code:
```bash
git add design_docs/ design_docs_for_igor/ memory/ claudecode/
```

Check the diff — confirm no source code, no .env, no runtime data:
```bash
git diff --staged --stat
```

Commit:
```bash
git commit -m "$(cat <<'EOF'
docs: day-close session YYYY-MM-DDx — <one-line theme>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
git pull --rebase origin main && git push origin main
```

---

## What day-close is NOT

- Not a savestate — session state is already in DB before this runs
- Not a code commit — source code commits happen during workstep/sprint
- Not required for crash recovery — DB already has everything

## Hard rules

- Always commit docs only — source code commits belong in /sprint.
- Always update DSB files in place — never rewrite from scratch.
- Always add only gaps that actually happened — no speculative entries.
- Always skip steps with nothing to update — no noise.
