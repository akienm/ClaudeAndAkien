---
name: decided
description: Batch-ticketize conversation decisions. Reads recent conversation turns (since /design marker or prior /decided), summarizes each decision, drafts tickets per decision, runs /review on each ticket filing-time, and writes to queue + slate + session record + Igor memory palace with two-way decision↔ticket backlinks.
model: sonnet
---

# /decided — Close a design block → batch tickets

The closing mark of a design conversation. Takes "the stuff we just talked about" and makes it durable — decisions in the palace, tickets in the queue, everything linked.

## Inputs

- Optional arg: a brief one-line summary of this decision, e.g. `/decided rename audit to day-close-audit`. If omitted, CC infers the summary from the scope.
- Scope boundary: look back to either:
  1. The most recent `DESIGN_START` marker in the session record (written by /design), OR
  2. The most recent prior /decided boundary, OR
  3. The session start, whichever is most recent.

## Steps

### 1. Determine scope

```bash
DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
# Find the last boundary (DESIGN_START or prior /decided) in the current session's key_changes
IGOR_HOME_DB_URL=$DB python3 -c "
import psycopg2, os
sid = open(os.path.expanduser('~/.TheIgors/cc_channel/current_session.txt')).read().strip()
conn = psycopg2.connect(os.environ['IGOR_HOME_DB_URL'])
cur = conn.cursor()
cur.execute('SET search_path TO instance, infra, public')
cur.execute('SELECT key_changes FROM sessions WHERE id = %s', (sid,))
row = cur.fetchone()
kc = (row[0] if row else '') or ''
# Most recent DESIGN_START marker wins; else oldest content is the start
for line in reversed(kc.splitlines()):
    if 'DESIGN_START' in line or 'DECIDED ' in line:
        print(line)
        break
"
```

If no prior boundary, treat the whole session as the scope.

### 2. Summarize the decision

One to two sentences. Assign a decision id: `D-<kebab-slug-of-topic>-YYYY-MM-DD`.

### 3. Draft tickets

For each implementation unit the decision implies, draft a ticket:
```python
{
  "id": "T-<kebab-slug>",
  "title": "<short title, <80 chars>",
  "size": "S|M|L|XL",
  "tags": ["<Topic>", "<Area>"],
  "description": "<problem + proposed shape + scope boundary + blocked-by if any>",
  "decision_id": "D-...",
  "gate": null,  # set if depends on another pending ticket
  "priority": 0.5  # raise for unblockers
}
```

### 4. Run /review on each draft (filing-time mode)

Always invoke /review once per drafted ticket — filing-time quality is the whole point of /decided. /review returns one of:
- **PASS** → proceed to filing.
- **AMEND** → apply the amendments (or ask Akien if ambiguous), re-submit to /review.
- **SPLIT** → replace the single draft with N child drafts; run /review on each.
- **DISCARD** → drop the draft, note why in the decision narrative.

HIGH-inertia findings from /review surface inline to Akien for pre-approval; the approval stamp lands in the ticket body.

### 5. File the tickets

Write a batch JSON file to `/tmp/decided_batch_<decision-id>.json` containing the post-review tickets, then:
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py add /tmp/decided_batch_<decision-id>.json
```

### 6. Write to Igor memory palace

Create a decision node at `theigors/decisions/D-...` in the palace:
```bash
# After T-decisions-into-palace-subtree lands, this uses palace_write.
# Until then, use a file stub at lab/design_docs/decisions/D-....md
```

Fields on the palace node / file:
- `title`: one-line decision summary
- `content`: decision narrative (the 1-2 sentences from step 2 + context from the conversation scope)
- `spawned_tickets`: list of ticket ids created
- `date`: YYYY-MM-DD
- `status`: open (closes automatically when all spawned_tickets close, via decision-rollup)

### 7. Append to decisions log

Chronological append to the decisions file (palace-echoed once T-decisions-into-palace-subtree ships). Until then:
```bash
echo "$(date -Iseconds) | D-... | <summary> | tickets: T-x, T-y, T-z" >> ~/TheIgors/lab/design_docs_for_igor/decisions_log.dsb
```
(Note: auto-memory flags this file as "do not blindly write" — /decided is a structured writer, not a blind dump; this is the exception. After palace migration this file becomes a generated echo.)

### 8. Append to slate + session

```bash
# Today's slate: under ## Ad hoc
echo "- $D_ID: <summary> — T-x, T-y, T-z" >> ~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt

# Session record: boundary marker + decision
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py append-change "DECIDED $D_ID: <summary> → T-x T-y T-z"
IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py append-decision "$D_ID"
```

### 9. Clear /design flag (if set)

```bash
rm -f ~/.TheIgors/cc_channel/design_mode.json
```

### 10. Report

```
/decided <summary> — D-...
Tickets filed: T-x, T-y, T-z (<N> total)
All linked to D-... (two-way navigation via decision_id field + decision's spawned_tickets list)
```

## Flow integration

Design pattern:
```
/design (optional)
  → conversation turns (may include back-and-forth, questions, exploration)
/decided <summary>
  → tickets filed, decision recorded, design block closes
/sprint-batch decision:D-...
  → sprints all tickets from this decision
```

Or, with multiple decisions in one session:
```
/design
  → discuss topic A
/decided A — T-a1, T-a2
  → discuss topic B
/decided B — T-b1
  → discuss topic C
/decided C — T-c1, T-c2, T-c3
/sprint-batch today-slate
  → sprints all 6 tickets across the three decisions
```

## Invariants

- Every decision gets a D-id, even single-ticket ones — makes trace navigable.
- Every ticket in a /decided batch carries `decision_id` — no orphaned tickets.
- /review runs on EVERY draft, not just the first or biggest.
- HIGH-inertia approvals are recorded in the ticket body before filing, not remembered in CC's head (survives compaction).

## Hard rules

- Always run /review on every drafted ticket — filing-time quality is the whole point.
- Always treat a /review DISCARD as blocking — file only with explicit Akien override.
- Always give each distinct decision its own D-id. One session can hold many decisions.
- Always treat decisions as append-only. New context becomes a new decision, linked via metadata.
