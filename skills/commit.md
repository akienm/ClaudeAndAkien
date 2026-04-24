---
name: commit
description: Full commit cycle for TheIgors project — run tests, audit, stage specific files, commit, pull, push. Use when Akien says /commit, "commit this", "commit and push", or "ship it".
---

# Commit — Full Cycle

One commit = run tests → audit → stage → commit → pull → push. Never partial.

---

## Step 0 — Sync docs DB if any .dsb files are staged

```bash
git diff --cached --name-only | grep -q '\.dsb$' && \
  CC_DB_URL=$CC_DB_URL \
  python3 $PROJECT_ROOT/claudecode/docs_sync.py sync || true
```

Non-fatal — docs DB sync failure never blocks a commit.

---

## Step 1 — Run tests

```bash
cd ~/TheIgors && source venv/bin/activate && python -m pytest tests/ -x -q 2>&1 | tail -20
```

If tests fail: **STOP**. Do not commit. Report failures. Offer to run `/test-fix` or investigate.

If no test file exists for changed code and it's non-trivial: flag it. Do not block on it — but note in commit message.

---

## Step 2 — Audit staged changes

Run `git diff --staged` (or `git diff HEAD` if nothing staged yet). Check:
- No secrets, keys, or .env content
- No `~/.TheIgors/` runtime paths committed
- No DB files committed
- Forensic logging present for non-trivial changes (warn if missing, don't block)
- No `--no-verify` or `--no-gpg-sign` flags in any command

If audit fails hard (secrets): **STOP**. Report. Do not proceed.

---

## Step 3 — Stage specific files

Use `git add <file1> <file2>` — **never** `git add -A` or `git add .`.

List every file being staged. If unsure which files to stage, run `git status` first and ask Akien.

---

## Step 4 — Commit

Use a meaningful message. Format:
```
feat/fix/docs/refactor: [one-line description] — closes #NNN if applicable

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

Use HEREDOC form to avoid shell quoting issues:
```bash
git commit -m "$(cat <<'EOF'
feat: description here

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

If pre-commit hook fails: fix the issue, re-stage, create a NEW commit (never --amend a published commit).

---

## Step 5 — Pull then push

```bash
git pull --rebase origin main && git push origin main
```

If pull has conflicts: resolve them, then push. If force-push would be needed: **STOP** and ask Akien.

---

## Hard rules

- Always let pre-commit hooks run — never use `--no-verify`.
- Always push non-force to main.
- Always stage files by name — runtime state (`.env`, `*.db`, paths under `~/.TheIgors/`) stays out automatically.
- Always commit source code as part of /sprint, not /savestate.
- Always read the diff before committing — no surprises
