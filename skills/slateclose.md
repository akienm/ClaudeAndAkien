---
name: slateclose
description: Closes the current work slate for TheIgors project. Reviews open tickets, notes what's done/deferred/carried, posts summary to GitHub discussion, archives slate.md. Use when Akien says /slateclose, "close the slate", "wrap up this slate", or "start a fresh slate".
model: haiku
---

# Slateclose — Close the Current Work Slate

Runs when a slate of work is complete or at a natural break point.
Not the same as day-close — a day can have multiple slates.
Not the same as savestate — session state is separate from slate state.

---

## Step 1 — Review open tickets

```bash
python3 ~/TheIgors/claudecode/cc_queue.py list
```

Categorize each ticket:
- **Done this slate**: closed during this slate
- **Deferred**: not started, pushed to next slate
- **Carried**: in-progress or partially done, continues next slate

---

## Step 2 — Post slate summary to GitHub discussion #62

Compose a 3-5 bullet summary and post:

```bash
gh api graphql -f query='mutation {
  addDiscussionComment(input: {
    discussionId: "D_kwDORR89g84AkjSM",
    body: "## Slate close YYYY-MM-DDx — <theme>\n\n**Done**: ...\n**Deferred**: ...\n**Carried to next slate**: ...\n**Next slate focus**: ..."
  }) { comment { id } }
}'
```

Post before archiving slate.md — in case of crash.

---

## Step 3 — Archive slate.md

```bash
cp ~/.TheIgors/cc_channel/slate.md \
   ~/.TheIgors/cc_channel/slate_archive_$(date +%Y-%m-%d-%H%M).md
> ~/.TheIgors/cc_channel/slate.md
```

The archive is the record. The empty slate.md is ready for the next `/slate`.

---

## Step 4 — Optionally trigger day-close

If this is the last slate of the day: run `/day-close`.
If more slates are planned today: skip.

---

## Hard rules

- Never delete archived slates — they're the record
- Always post to GitHub before clearing slate.md
- Carried tickets stay in queue as in_progress — do not close them
