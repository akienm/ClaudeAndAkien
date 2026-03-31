---
name: review
description: Pre-decision design review for TheIgors. Checks latest thinking against CS and CogSci patterns — surfaces antipatterns, alternatives, simplifications. Runs before /decided when Akien says /review, "check this", "does this make sense", or "am I missing something". Lightweight speedbump, not a deep dive.
---

# Review — Pre-Decision Design Check

Fires before a design decision is locked. Not a deep research task.
Goal: catch the thing Akien didn't ask about. Surface it. Then get out of the way.

---

## Step 1 — Identify what's being reviewed

From recent conversation, identify:
- The design idea or decision under consideration (1-3 sentences max)
- What problem it's solving
- What layer it touches (graph, habits, inference, cognition, infra, process)

If ambiguous: ask "what's the decision?" before proceeding.

---

## Step 2 — Run the checklist

For each check, mark CONCERN / CLEAN / N/A:

### CS Antipatterns
- **Wrong layer**: Is the problem being solved at the right abstraction level? (e.g. fixing a data problem with code, fixing a code problem with config)
- **Premature abstraction**: Is this generalizing before there's a second case? One use = inline it.
- **Hidden coupling**: Does this create a dependency that isn't obvious from the call site?
- **Complexity budget**: Does the complexity added match the problem size? L-size fix for an S-size problem = flag.
- **Mock risk**: Is anything being faked that should be tested live?
- **print() instead of logging**: Does new/changed code use bare `print()` for observable output? Should be `logging.getLogger(__name__)` so the console handler (when it exists) can subscribe. Flag any new `print()` outside of main.py's Rich console path.

### CogSci / Architecture Antipatterns (TheIgors-specific)
- **Inference masking a gap**: Is this adding inference where a graph node should exist?
- **Habit over graph**: Is this encoding a response as a habit when it should be learned graph structure?
- **Wrong training signal**: Is the feedback loop teaching the right thing? (e.g. wg_cooccur is corpus stats, not cognitive relevance)
- **Anthropomorphizing too literally**: Is a human cognitive claim being mapped 1:1 to code without checking if the analogy holds at this level of detail?
- **Escalation hiding failure**: Would this make the system look like it's working when it's actually falling through to inference every time?

### Simplification check
- Is there a simpler thing that does 80% of this?
- Can this be done with existing infrastructure rather than new code?
- What's the minimum viable version of this idea?

---

## Step 3 — Output

```
REVIEW — <one-line description of what was reviewed>

Checks:
  [CONCERN] Wrong layer — <one sentence why>
  [CLEAN]   Hidden coupling
  [CONCERN] Habit over graph — <one sentence why>
  [CLEAN]   Simplification — existing infra covers this
  ...

Concerns: N
Simplification candidate: <yes/no + one line if yes>

Recommendation: <one of:>
  - "Looks clean — proceed to /decided"
  - "N concern(s) worth discussing before locking"
  - "Suggest simplification: <what>"
```

---

## What /review is NOT

- Not a blocker — Akien decides whether to act on concerns
- Not a deep CogSci literature dive — surface pattern matches only
- Not a repeat of /filter — filter checks plan completeness, review checks design quality
- Not a veto — concerns are inputs, not decisions

## Positioning in workflow

```
Discussion → /review → (address concerns or override) → /decided → /filter → work
```

If /review surfaces nothing: proceed to /decided immediately.
If /review surfaces concerns: discuss, then /decided captures whatever was resolved.
