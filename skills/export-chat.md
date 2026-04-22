---
name: export-chat
description: Dump the current CC session transcript to /home/akien/TheIgors/claude_chat_logs/YYYY-MM-DD.md for recovery if chat scrolls off the top. Run on demand; also supports --all for bulk backfill and --session <id> for a specific one.
model: haiku
---

# /export-chat — Dump current chat to markdown

Recovery snapshot. If something scrolls off the top of the chat, `/export-chat` gives you a durable copy on disk.

## Steps

Run the helper script (default target is the most-recently-modified transcript — i.e. the current session):

```bash
python3 /home/akien/TheIgors/lab/claudecode/export_chat.py
```

Output: `YYYY-MM-DD.md` per calendar day. Each message is routed to the day-file matching its own timestamp, so long-lived sessions that span midnight contribute to multiple day-files. Each day-file is rebuilt as the union of every session's contribution for that date — re-running the export produces identical output (idempotent by construction).

## Flags

- `--session <session-id>` — scope the refresh to the day-files touched by a specific session (the UUID filename minus `.jsonl`). Union with other sessions' content for those days is preserved.
- `--all` — rebuild every day-file from the full transcript directory. Idempotent.
- `--dry-run` — print what would be written, don't touch disk.

## What it renders

- User turns and assistant turns with timestamps.
- Tool calls: rendered as inline one-liners like `_[tool: Bash({"command":"..."})]_`.
- Tool results: elided to first 200 chars so the log stays readable.

## What it skips

- Empty / system-reminder / hook messages.
- Full tool result bodies (too noisy for a recovery log — the goal is "remember what we talked about", not reconstruct every command output).

## When to run

- Anytime you see the chat approaching its visible scroll limit and you want insurance.
- Before `/compact`, so you have the pre-compact state preserved.
- End of session (though `/savestate` covers the structured summary; `/export-chat` covers the verbatim transcript).

## Related

- **T-chat-history-igor-backfill** (gated) — Igor background job that runs `--all` periodically to keep every day's transcript archived.
- **/savestate** — structured session summary; different shape, different purpose.

## Source location

- Transcripts: `~/.claude/projects/-home-akien-TheIgors/<session-id>.jsonl`
- Script:      `/home/akien/TheIgors/lab/claudecode/export_chat.py`
- Output:      `/home/akien/TheIgors/claude_chat_logs/YYYY-MM-DD.md`
