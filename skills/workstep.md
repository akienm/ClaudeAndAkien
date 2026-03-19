---
name: workstep
description: Compiled work discipline for TheIgors project. Enforces the full work loop including plan approval gate, forensic logging, hot-reload, and doc updates. Invoke when Akien says /workstep, "let's work on", "start on", or "ready to implement".
---

# Workstep — Compiled Work Discipline

This skill enforces the full work loop in order. Do not skip steps. Do not reorder.
Each gate marked **STOP** requires explicit confirmation before proceeding.

Session state accumulates automatically — each phase transition posts to the session record.

---

## Phase 1 — Orient

**1. Read the tickets.**
Read all relevant GitHub issues for this work. Understand scope, dependencies, acceptance criteria.
If no ticket exists for the work being requested, say so and offer to create one before continuing.

**Ticket size field — required on every ticket:**
- `Size: S` — single function or config change; one file touched
- `Size: M` — one module or a few related files; up to ~50 lines changed
- `Size: L` — multiple modules or architecture change; requires plan written before implementation begins

Worker rule: **L-size tasks must post a written plan and wait for Designer approval before writing a single line of code.**

**2. Chat about design issues.**
Surface ambiguities, architecture conflicts, inertia concerns. Ask questions now — not mid-implementation.
Check inertia levels for any files that will be touched (CLAUDE.md has the table).

**3. Update notes / create tickets from the discussion.**
Any decision or scope change that emerges → write a ticket or update the existing one.

---

## Phase 2 — Plan

**4. Group the work. Write a complete plan.**
List every file that will be touched, every function that will change, every new thing that will be created.
State what will NOT be changed (scope boundary).
Flag any HIGH or MEDIUM inertia files that need extra justification.

**5. ⛔ STOP — Get plan approval.**
Do not write a single line of code until Akien says "go", "approved", "looks good", or equivalent.
If Akien modifies the plan, restate the updated plan and get re-approval.

Record phase transition:
```bash
DB=$CC_DB_URL
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py append-change "workstep: plan approved for <ticket-id>"
```

---

## Phase 3 — Compact checkpoint (L-size only)

**6. ⛔ STOP — Compact checkpoint (L-size tasks only).**
For L-size work with a long design phase, say to Akien:
> "Design is locked. Please run `/compact` now to free context for implementation. Reply when done."

Use the preserve form if key state exists:
```
/compact preserve: open gaps [list them], files modified [list them], current goal [one line]
```

Skip this step for S and M size tickets — not worth the interruption.

---

## Phase 4 — Implement

**7. Start the implementation loop.**

Record phase transition:
```bash
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py append-change "workstep: implementing <ticket-id>"
```

Work ticket by ticket, function by function. Read each file before editing it.

**8. Fix each issue as planned.**
Stay in scope. If something unexpected surfaces that would change scope, stop and flag it — don't silently expand.

**9. Add forensic logging.**
Every non-trivial change gets logging. Timestamped. State changes, tool outputs, errors.
Log to the appropriate file in `~/.TheIgors/logs/`. This is not optional.

**10. Run live as a black-box test.**
Test against the live system, not mocks. Igor must be running.
Use the CC bridge to exercise the changed behavior end-to-end.
If Igor is not running, use the igor skill to start it.

**11. Update the ticket.**
Mark progress, note what was done, note anything that changed from the plan.

**12. Hot-reload the module.**
For LOW-inertia files: reload immediately via CC bridge.
For MEDIUM-inertia files: confirm with Akien first.
For HIGH-inertia files: do not hot-reload without explicit Akien approval.
Use the igor skill (§3) for the reload decision tree.

**13. Record decisions and changes — while context is fresh.**
For each design decision made during implementation:
```bash
DB=$CC_DB_URL
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/decision_manager.py add Dxxx "short-name" "status" "one-line"
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py append-decision Dxxx
```

For each ticket closed:
```bash
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py append-change "closed <ticket-id>: <what was built>"
```

---

## Phase 5 — Close

**14. Commit.**
```bash
/commit
```
Commit at logical checkpoints — a coherent unit of work reviewable standalone.
Never `--no-verify`. Never force-push main.

**15. Loop until all tickets closed.**
Return to step 7 for the next ticket in this workstep.

Record loop transition:
```bash
CC_DB_URL=$CC_DB_URL python3 $PROJECT_ROOT/claudecode/session_manager.py append-change "workstep: moving to next ticket"
```

---

## Hard Rules

- **Never start implementation without plan approval** (step 5 gate)
- **Never skip forensic logging** (step 9)
- **Never test against mocks** — live system only
- **Never edit HIGH-inertia files without Akien review**
- **Never commit without reading the diff first**
- **Correct scope creep immediately** — flag it, don't absorb it silently
- **Docs updates and GitHub discussion go in day-close, not here**

---

## Quick Phase Reference

| Phase | Steps | Gate |
|---|---|---|
| Orient | 1–3 | — |
| Plan | 4–5 | ⛔ Plan approval |
| Compact | 6 | ⛔ L-size only |
| Implement | 7–13 | — |
| Close | 14–15 | — |
