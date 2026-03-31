---
name: slate
description: Start-of-slate planning ritual for TheIgors. Reviews open tickets, gap analysis, and last audit results, then plans the current slate and discusses priorities. Use when Akien says /slate, "start a new slate", "plan the slate", or "what are we working on".
model: haiku
model_exception: Step 5 (propose the slate) and Step 6 (discussion) require Sonnet — the synthesis and priority judgment cannot be delegated.
---

# Slate — Start-of-Slate Planning

Runs at the start of a work block to orient and agree on what this slate covers.
Builds on /context-load (session record, channel, blobs) and adds planning discussion.

---

## Step 1 — Load context (if not already done)

If /context-load hasn't run this session:
```
/context-load
```

Otherwise skip — use the briefing already in context.

---

## Step 2 — Review open tickets

```bash
python3 ~/TheIgors/claudecode/cc_queue.py list
```

Note: pending tickets, in-progress tickets, anything blocked.

---

## Step 3 — Read gap analysis top

```bash
head -40 ~/TheIgors/design_docs/gap_analysis.md
```

Which open gaps are most relevant to what we might work on today?

---

## Step 4 — Skim last audit results (if recent)

```bash
ls -t ~/.TheIgors/logs/audit_*.log 2>/dev/null | head -1 | xargs head -30 2>/dev/null || echo "no recent audit log"
```

Any findings from last audit that should inform priority?

---

## Step 5 — Propose the slate

Based on steps 2-4, propose:
- What this slate is for (one sentence theme)
- Which 2-4 tickets are in scope
- Which tickets are explicitly out of scope for this slate
- Any gaps to address

Output format:
```
SLATE PROPOSAL — YYYY-MM-DD

Theme: <one sentence>
In scope: T-xxx, T-yyy, T-zzz
Out of scope: (everything else)
Gap attention: G-xxx (if relevant)
```

---

## Step 6 — Discuss

Wait for Akien to confirm, adjust, or redirect the slate before any work starts.
The slate is not locked until Akien says so.

After agreement: write the confirmed slate to `~/.TheIgors/cc_channel/slate.md`.

---

## Hard rules

- No work starts until the slate is agreed
- Slate.md is the authoritative record of what's in scope
- If slate.md already has content from a previous slate: run /slateclose first
