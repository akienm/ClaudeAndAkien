---
name: filter
description: Plan verification filter for TheIgors work. Checks that inertia levels are stated, tests exist or are planned, forensic logging is in plan, and scope boundary is explicit. Use when Akien says /filter, "verify the plan", "check the plan", or "is this ready to implement?".
model: haiku
---

# Filter — Plan Verification

The Filter runs mechanically before implementation starts. No judgment — just verification.
It does not verify the code. It verifies the **plan** is complete enough to execute safely.

**Called from**: workstep Phase 2, step 4b — runs automatically before plan approval gate.
Can also be called standalone when Akien asks "is this ready?" or "check the plan".

---

## Check 1 — Inertia levels stated

For every file in the plan, inertia level must be declared:

| Level | Files | Requirement |
|---|---|---|
| HIGH | `brainstem/`, `memory/models.py`, `cognition/reasoners/base.py` | Must have Akien sign-off noted in plan |
| MEDIUM | `cognition/`, `memory/cortex.py`, `anthropic.py`, `main.py` | Must note "discussed with Akien" |
| LOW | Everything else | No requirement |

**Fail condition**: plan touches a file but doesn't state its inertia level.

---

## Check 2 — Tests exist or are in plan

For each non-trivial change, one of:
- A matching `tests/test_<module>.py` already exists, OR
- The plan explicitly includes "write tests for X" as a step

**Fail condition**: change is non-trivial and tests are neither present nor planned.

---

## Check 3 — Forensic logging in plan

For any non-trivial logic change:
- The plan must mention what will be logged and to which log file (`~/.TheIgors/logs/`)

**Fail condition**: plan modifies non-trivial logic with no mention of logging.

---

## Check 4 — Scope boundary stated

The plan must say what will NOT be changed. Explicit scope exclusions prevent drift.

**Fail condition**: no "out of scope" or "not changing" section.

---

## Check 5 — Size classification matches scope

- `Size: S` — one file, one function: verify the plan touches ≤1 file
- `Size: M` — one module, ≤50 lines: verify the plan matches
- `Size: L` — multiple modules or architecture: verify a written plan was posted and approved

**Fail condition**: claimed size doesn't match actual scope.

---

## Output format

```
FILTER RESULT: PASS / FAIL

Checks:
  [PASS] Inertia levels stated
  [FAIL] Tests missing for word_graph.py changes — no test in plan
  [PASS] Forensic logging mentioned
  [PASS] Scope boundary stated
  [PASS] Size matches scope

Blocking issues: 1
Recommendation: Add test step for word_graph.py before proceeding.
```

On FAIL: list blocking items. Akien decides whether to unblock or proceed anyway.
On PASS: say "Filter passed — ready for implementation."
