---
name: review
description: Filing-time + standalone critical review. Primary use — called by /decided on each drafted ticket (duplicate/already-done/blocked-by/size/scope-creep/test-plan/HIGH-inertia). Also invokable directly on a risky diff/PR/plan, or before a sprint claim. Replaces the old /filter + /review with one skill covering both.
model: haiku
---

# /review — Filing-time + standalone critical review

Two modes; same checks applied to different inputs.

## Mode A — filing-time (called by /decided and /fixit)

Each drafted ticket, BEFORE it lands in queue.json, goes through these checks. Input: the ticket as a dict (id, title, size, tags, description). Output: verdict (PASS / AMEND / SPLIT / DISCARD), findings, optionally a modified ticket dict that `/decided` uses instead of the original.

### Checks (in order)

1. **Duplicate detection** — grep `queue.json` for tickets with overlapping id, title, or significant description n-grams across status `pending`, `in_progress`, and recent `done`. If found: output `DISCARD: duplicate of T-xxx (shipped|pending)`, or `AMEND: merge with T-xxx` if the new description adds material the existing one lacks.
2. **Already-done-in-code** — grep the codebase for the key symbols/tool-names/file-paths the ticket proposes to add. If they already exist with the described behaviour: output `DISCARD: already implemented in <file>:<line>`. This catches the "we wrote this last month, forgot, and re-ticketed it" failure mode.
3. **Blocked-by-pending** — if the ticket's description mentions code/features/tools described by another pending ticket, output `AMEND: add gate "<ticket-id>"` so it doesn't try to sprint before its dependency is real.
4. **Size sanity** — compare declared size vs description scope.
   - XL declared on ≤300 words of description → flag as possibly not-actually-XL
   - S declared on ≥800 words of description → flag as probably bigger than S
   - L or XL → nudge for breakdown: "does this want to be 2-3 child tickets?" Output `SPLIT: propose <N> children with <shapes>` if obvious cuts exist
5. **Scope-creep** — does the description actually contain multiple separable tickets? ("Also: refactor X", "While we're at it, Y"). If yes: `SPLIT: propose <N> children`.
6. **Test-plan** — emit a `test_plan:` field on the ticket if missing. At minimum: which new tests, which existing regressions, any real-DB integration test needed (no-mocks rule). Not writing the tests, just planning them.
7. **HIGH-inertia check** — if the description names `brainstem/`, `memory/models.py`, `cognition/reasoners/base.py`, or any other file flagged HIGH-inertia in the rules:
   - ASK AKIEN INLINE: "This ticket touches <file> (HIGH inertia). Pre-approve? y/n/reword"
   - If pre-approved: stamp ticket body: `pre-approved by Akien YYYY-MM-DD for touching <file> — reason: <reason>`
   - If not: `AMEND: rescope to avoid <file>`, or `DISCARD`

### Output format (filing-time)

```
/review — <ticket-id>
Verdict: PASS | AMEND | SPLIT | DISCARD

Findings:
- <finding 1>
- <finding 2>

Amended ticket (if AMEND): <diff from input>
Child proposals (if SPLIT): <list of {id, title, size, description-sketch}>
Discard reason (if DISCARD): <one line>
```

### Writes (for T-review-self-learning)

Every /review invocation writes a `review_findings` record to the DB (when T-review-self-learning ships). For now, log to `~/.TheIgors/claudecode/logs/YYYYMMDD.review.log` so the future self-learning pass can backfill.

## Mode B — standalone (code / plan / PR)

Same checks, different shape of input.

### Plan review

Given a plan-in-conversation (usually triggered pre-/sprint by Akien saying "/review this plan"):
1. Inertia — which files will be touched? HIGH needs justification.
2. Tests — will tests exist for this? Integration vs mocked?
3. Scope — in vs out. Scope creep?
4. Simplicity — standard pattern (registry, queue, observer) vs bespoke?
5. Reversibility — can this be undone cleanly if wrong?

### Code / diff review

Given a diff (staged changes or a specific commit range):
1. Secrets — no `.env`, keys, passwords, hardcoded paths
2. Dead code — commented-out blocks, unused imports, replaced-but-not-removed functions
3. Debug artifacts — print statements, temp files, TODO without ticket
4. Test coverage — new behaviour = new test
5. Matches ticket — diff reflects what the ticket asked for, nothing extra
6. Inertia violations — HIGH-inertia files changed without justification

### PR review

`/review <PR#>`: fetch via `gh api repos/<org>/<repo>/pulls/<N>/comments` + `gh pr diff <N>`. Apply the code-review checklist above.

### Output format (standalone)

```
REVIEW — <plan|code|PR#>
Verdict: PASS | MUST-FIX | DISCUSS

Must-fix: <blocking issues — do not proceed until resolved>
Suggestions: <non-blocking improvements>
```

## Hard rules

- Always actually look. "PASS" is a verdict earned by checking, not a default.
- Must-fix items always block sprint/filing until resolved.
- Always record Akien overrides on must-fix items — the override record is training data for the self-learning loop.
- Filing-time /review runs in seconds (Haiku-shaped checklist work). Standalone /review on a complex plan escalates to Sonnet reasoning when needed.
- Always log every invocation to the review log file — feeds T-review-self-learning later.

## Related

- **/decided** — calls /review in filing-time mode on each drafted ticket before adding to queue.
- **/fixit** — (after rewrite) same, since /fixit = /decided + /sprint-batch.
- **T-review-self-learning** (gated) — reads the review log to adjust per-flag confidence over time.
