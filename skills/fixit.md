---
name: fixit
description: Fast reactive shortcut — /decided (implicit design over the just-discussed thing) + /sprint-batch on the just-filed tickets. For bug-shaped quick reactions. Replaces the old /ticket + /sprint single-ticket shortcut as of 2026-04-20.
model: sonnet
---

# /fixit — Implicit design, batch sprint

The fast path. Use when Akien says "fix this", "quick fix", "/fixit", or when a bug is known and the discussion is short. More considered work uses the explicit `/design` → discussion → `/decided` loop instead.

## What /fixit is

`/fixit` = `/decided` + `/sprint-batch` on the just-filed tickets. Nothing more.

That means:
- Implicit design scope — the "thing just discussed" covers the recent conversation turns
- Full filing-time `/review` runs on every drafted ticket (duplicate / already-done-in-code / blocked-by-pending / size sanity / scope-creep / test-plan / HIGH-inertia inline approval + stamp)
- Every ticket that gets filed also gets sprinted in this same invocation
- Multiple tickets is fine — /fixit is not limited to a single ticket, it inherits /sprint-batch's multi-ticket handling

## Steps

1. **Invoke /decided** with implicit scope (recent conversation since last /decided or session start). This:
   - Summarizes the decision (1-2 sentences; assigns a D-... id)
   - Drafts ticket(s) needed to implement
   - Runs /review on each drafted ticket; applies AMEND / SPLIT / DISCARD based on findings; stamps HIGH-inertia approvals
   - Files the surviving tickets into queue.json + slate + session + Igor palace

2. **Invoke /sprint-batch** with selector `decision:D-<just-created-id>` — runs all tickets spawned by step 1 in topo-sorted dependency order. Per ticket: claim → build → test → cleanup → doc-refresh → commit+push → close. Retroactive "oh, and I also fixed this" incidental tickets are filed automatically if the commit includes debris-scope fixes.

3. **/savestateauto** at batch end (handled by /sprint-batch).

## Report

```
/fixit — <one-line summary>
Decision: D-... (spawned <N> tickets)
Sprinted: T-x, T-y, T-z (<M> completed, <P> skipped/blocked)
Commits: <hash1>, <hash2>, ...
```

## When NOT to use /fixit

- When the scope is load-bearing or architectural — use explicit `/design` → discussion → `/decided` → `/sprint-batch` instead. /fixit's implicit scope inference is fine for small reactive work; for bigger work, explicit design brackets are worth the ceremony.
- When the work needs multiple days to ship — /fixit is a single-session shortcut. Multi-day efforts file tickets via `/decided` and get sprinted later.
- When Akien wants to stop after /decided and review tickets before sprint. Say `/decided` directly instead of `/fixit`; then `/sprint-batch <selector>` later.

## Flow comparison

**Considered design loop:**
```
/design (optional)
  → discussion, exploration, questions
/decided
  → tickets filed with /review applied
/sprint-batch (later, after approval or at a natural moment)
  → tickets shipped
```

**/fixit (reactive shortcut):**
```
"fix this" or "/fixit :)"
  → /decided (implicit scope on recent turns)
  → /sprint-batch (immediately, on the just-filed tickets)
  → done
```

## Hard rules

- Never skip /review — even in the fast path, filing-time quality gate applies.
- Never bypass HIGH-inertia approval — the inline prompt fires even during /fixit; Akien pre-approves and the stamp lands in the ticket body.
- Never sprint past a gated ticket — /sprint-batch filters gated tickets; a ticket gated by /review (e.g. "needs pre-approval") must clear its gate before sprinting.
- Never combine tickets from different decisions — if /decided during /fixit produces multiple distinct decisions, each gets its own D- id; /sprint-batch scopes to just the current /fixit invocation's decision id.

## Related

- **/decided** — the filing half of /fixit; invokable standalone for design-mode work that should queue up, not sprint immediately.
- **/sprint-batch** — the sprint half of /fixit; invokable standalone against any selector (today-slate, tag:..., explicit ids).
- **/review** — invoked per-ticket by /decided during /fixit; also standalone for diff/PR/plan review.

## Historical note

Before 2026-04-20, /fixit = `/ticket last` + `/sprint last` — single-ticket shortcut for pre-filed work. The rewrite aligns with the broader workflow overhaul (D-workflow-overhaul-2026-04-20) that introduced /decided + /review-as-filing-time + /sprint-batch.
