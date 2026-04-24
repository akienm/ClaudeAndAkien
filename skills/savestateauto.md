---
name: savestateauto
description: Lightweight state flush — update session record, flush to Igor, remove debug flag, AND emit a compact preserve string so Akien can manually /compact at a clean boundary if desired. Does not itself compact.
---

# /savestateauto — Quick state flush (+ compact preserve string)

Called automatically by /ticket, /sprint, /day-close. Also callable directly.

Since 2026-04-20: the final step always emits a compact-ready preserve string. Akien can copy/paste it into `/compact` at any clean boundary. Paired with `/export-chat`, this means unexpected auto-compact is rare — when compact happens, it happens on command, with known preservation instructions.

## Steps

1. **State hypothesis**: Always write one sentence naming what's in-flight and why. Use NONE when the session is clean — the slate says something either way.

2. **Flush to Igor** (non-fatal):
   ```bash
   python3 ~/TheIgors/lab/claudecode/cc_queue.py flush_session <session_id> "theme: ...; next: ..."
   ```

3. **Append hypothesis to session key_changes** (T-savestate-append-change-gap):
   ```bash
   DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
   IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py append-change "<hypothesis from step 1>"
   ```
   Why: flush_session only posts to the Igor channel; it does not touch infra.sessions.key_changes. Without this step, the session DB record stays empty between /sprint invocations, making "what changed" unrecoverable after compact.

4. **Finalize session record** (if session ending):
   ```bash
   DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
   IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py finalize "YYYY-MM-DDx" \
     "Next: top priorities" "In-flight: hypothesis or NONE"
   ```

5. **Remove debug flag**:
   ```bash
   rm -f ~/.TheIgors/Igor-wild-0001/debug_session.flag
   ```

6. **Emit compact preserve string** (always, even if Akien doesn't ask for compact):

   Render a block that Akien can hand to `/compact` if he chooses. Shape:
   ```
   preserve: Session <session-id>. <theme short>.
   Today's commits: <hashes>.
   Done this session: <T-x, T-y, ...>.
   Filed: <T-a (gated on ...), T-b, ...>.
   Active decisions: <D-x (N open), D-y (done)>.
   In-flight: <hypothesis or NONE>.
   Next: <top 1-3 priorities>.
   Rules: <any load-bearing context rules CC should remember>.
   ```

   Build from:
   - Session id: `cat ~/.TheIgors/cc_channel/current_session.txt`
   - Theme + key_changes + decisions: query `infra.sessions` for current session
   - Today's commits: `git log --oneline --since=midnight`
   - Active decisions: group by `decision_id` in queue.json, count open vs closed tickets each
   - In-flight hypothesis: from step 1 above
   - Next priorities: from today's slate `## Planned` (top few)

   Print the block at the end of the /savestateauto output, clearly labeled:

   ```
   ── COMPACT PRESERVE STRING (copy if you want to /compact now) ──
   preserve: ...
   ───────────────────────────────────────────────────────────────
   ```

That's it. No compact (Akien decides), no file rewrites, no DSB updates. Just DB + Igor flush + a compact-ready block on standby.
