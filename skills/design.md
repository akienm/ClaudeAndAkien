---
name: design
description: Mark the start of a design-mode block. Optional — /decided can infer scope retroactively without this. Use when you want to explicitly bracket a design session so /decided knows exactly where to start looking back.
model: haiku
---

# /design — Design-mode session marker

Lightweight boundary marker. Design conversations usually don't need this — /decided infers scope from "last N turns since previous /decided or session start." But sometimes you want to say explicitly "ok, from THIS point on we're designing, not building" — that's what /design is for.

## What it does

1. **Writes a DESIGN_START marker to the session record.** `session_manager.py append-change` records:
   `DESIGN_START YYYY-MM-DDTHH:MM:SSZ — <optional topic>`

2. **Sets a session tag.** In CC's current-session file, a `design_mode: true` flag is written so subsequent /decided invocations know to scope from this marker.

3. **(Optional nudge on CC's behaviour, self-imposed):** in design mode, bias toward discussion-shape responses — fewer proactive edits, more "what about X?" questions. Don't file tickets or start sprints until /decided closes the block.

## What it does NOT do

- Does not block other commands — you can still /commit, /ticket, /sprint during a design block if needed.
- Does not enforce anything — this is a marker, not a gate.
- Does not auto-close — the block ends at the next /decided or the end of the session, whichever comes first.

## Usage

```
/design
/design <topic or theme>
```

The topic is freeform text; it's recorded alongside the marker for future recall.

## Steps

1. Get current session id from `~/.TheIgors/cc_channel/current_session.txt`.
2. Compose marker: `DESIGN_START YYYY-MM-DDTHH:MM:SSZ — <topic or (none)>`.
3. Run:
   ```bash
   DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
   IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py append-change "<marker>"
   ```
4. Write `design_mode: true` + `design_mode_started_at: <iso timestamp>` to `~/.TheIgors/cc_channel/design_mode.json` (atomic: write to tmp, rename).
5. Acknowledge: "Design mode on, scope begins now. Use /decided to close the block and ticketize."

## Ending the block

Either:
- **/decided** — ticketizes the conversation since DESIGN_START; clears the design_mode flag.
- **End of session** — design_mode flag ages out on next session start.
- **Explicit:** `/design end` — clears the flag without filing tickets (if the design block produced no decisions worth ticketing).

## Relation to other skills

- **/decided** — reads the DESIGN_START marker to know where to look back from. Without /design, /decided falls back to "last /decided OR session start."
- **/note** — parallel path for insights that don't warrant a ticket. Can fire during design mode.
- **/fixit** — becomes `/decided + /sprint-batch` after T-fixit-rewrite lands. For bug-shaped reactive work, skip /design entirely.

## Hard rules

- Always reserve /design for blocks that will produce multiple decisions — skip it for single-question turns.
- /design always stays a marker — CC self-imposes the design-mode nudge; tool-use stays free.
- DESIGN_START markers are always single-firing per session — re-invoking /design just updates the topic.
