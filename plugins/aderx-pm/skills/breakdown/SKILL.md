---
name: breakdown
description: Break a technical plan or large requirement into small, self-contained issues that can be implemented independently and in parallel (by multiple engineers or AI agents) without merge conflicts — ordered into dependency waves with a contracts-first issue and a file-ownership map. Use this whenever the user asks to "split this into tickets/issues/tasks", "break down this epic", "plan work for multiple agents", "parallelize this", or has a docs/specs/<slug>/tech-plan.md ready for implementation. Produces docs/specs/<slug>/breakdown.md.
---

# Break down into parallelizable issues

The goal is a set of issues where each one can be picked up by an agent with no chat history, implemented in one PR, and merged without stepping on the others. A good breakdown lets several agents work at once; a bad one makes them fight over the same files.

## 1. Load inputs

Read `docs/specs/<slug>/tech-plan.md` and `requirements.md`. If there's no tech plan, offer to run `aderx-pm:tech-plan` first — breaking down without knowing the file layout and contracts makes conflict-free parallel work mostly guesswork.

## 2. Is it even big enough?

If the whole thing is roughly one PR (one agent session, a few hundred lines, one area of the code), say so and produce a single issue. Splitting small work only adds coordination overhead.

## 3. Principles

- **Contracts first (wave 0).** Put shared foundations — types/interfaces, API schemas, DB migrations, stubs, feature flags — into a small first issue. Once it's merged, everything that depends only on the contract can proceed in parallel. This is what makes parallelism safe.
- **Vertical slices over horizontal layers.** Prefer "user can accept an invite (API + UI + tests)" over "all backend" / "all frontend". Slices can be tested on their own and are less likely to be blocked.
- **File ownership.** List the files/directories each issue will create or modify (`touches`). Two issues in the **same wave must not touch the same file**. If they'd have to, either move the shared part into the contracts issue, or put one issue in a later wave.
- **Right-sized.** One issue ≈ one PR ≈ one focused agent session. If an issue needs more than ~5 acceptance criteria or touches many unrelated areas, split it.
- **Self-contained.** Each issue carries its own context: why it exists, what exactly to build, the relevant contract, the files, and how to verify. An implementer shouldn't need to read the whole spec to do it.
- **Traceable.** Every FR/AC from requirements.md is covered by at least one issue.

## 4. Build the waves

Wave N contains issues whose dependencies are all in waves < N. Issues within a wave run in parallel. Keep the dependency chain shallow — a long chain of single-issue waves means little parallelism, which is a sign the slicing could be better.

## 5. Validate

Write the machine-readable issue graph (see template) and run:

```bash
python3 <this-skill-dir>/scripts/check_breakdown.py docs/specs/<slug>/breakdown.md
```

It checks for unknown dependencies, cycles, dependencies that aren't in an earlier wave, and same-wave file overlaps. Fix anything it reports and re-run until it passes. Mention the parallelism summary it prints when you report back.

## 6. Write breakdown.md

~~~markdown
# <Feature name> — Breakdown

Tech plan: ./tech-plan.md
Last updated: <YYYY-MM-DD>

## Overview
<N issues in M waves; max parallelism; critical path>

## Waves
- Wave 0: I1 — <title>
- Wave 1: I2, I3, I4 (parallel)
- Wave 2: I5

## Coverage
| Requirement | Issues |
|---|---|

## Issue graph
```json
{
  "feature": "<slug>",
  "issues": [
    {"id": "I1", "title": "...", "wave": 0, "depends_on": [], "touches": ["src/types/invite.ts", "db/migrations/"]}
  ]
}
```

## Issues

### I1: <title>
- **Wave:** 0 · **Depends on:** — · **Estimate:** S/M/L
- **Why:** <user/business reason, link to FR/AC IDs>
- **Scope:** <exactly what to build>
- **Out of scope:** <what the neighbours handle, to prevent overlap>
- **Contract:** <interfaces this issue defines or consumes, copied from the tech plan>
- **Files:** <paths to create/modify>
- **Acceptance criteria:**
  - Given ..., when ..., then ...
- **How to verify:** <tests to add/run, commands>
~~~

Directory entries in `touches` end with `/` and cover everything beneath them. Keep `touches` as specific as you honestly can — overly broad entries create false conflicts, overly narrow ones hide real ones.
