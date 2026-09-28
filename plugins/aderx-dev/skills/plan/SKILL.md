---
name: plan
description: Turn a Linear ticket into an implementation spec that a fresh agent can build from - requirements, interface and input/output contract (including error behavior), architecture, allowed dependencies, ordered steps, acceptance criteria and test plan - then get the user's approval and save it locally. Use whenever the user gives a Linear ticket id or URL (like GGA-123) and wants to plan, scope or spec it out before coding, even if they don't say "spec".
argument-hint: "[LINEAR-ID or URL, e.g. GGA-123]"
---

# aderx-dev plan

Produce a spec at `.aderx-dev/specs/<TICKET>.md` that `build` and `pr-create` treat as the source of truth. Its reader has none of this conversation, so it must stand on its own. Vague specs are the main way this workflow fails, so spend effort here.

User argument: `$ARGUMENTS`

## Steps

### 1. Preconditions
- Read `.aderx-dev/config.json`. If it is missing, tell the user to run `/aderx-dev:init` and stop.
- Resolve the ticket id from the argument (a Linear URL contains it). A bare number such as `123` means `<linear.team>-123`. If there is no argument, ask.
- If `.aderx-dev/specs/<TICKET>.md` already exists, show its status and ask whether to revise it or start over. Never overwrite silently.

### 2. Fetch the ticket
Use the Linear tools (look them up with ToolSearch if they are deferred) to get the issue: title, description, labels, parent, blockers, linked docs and **all comments** (they often hold the real requirements or later corrections). If Linear is not connected, tell the user to connect it through `/mcp` and stop.

If the ticket says `Spec: docs/specs/<slug>/ (issue I<n>)`, it was filed by aderx-pm: read `docs/specs/<slug>/tech-plan.md` and that issue's section in `breakdown.md`. Their contracts, decisions and `touches` list are **settled**: build on them, don't re-design them. Only raise a conflict you find in the code.

Anything ambiguous, contradictory or missing becomes an open question, not a guess.

### 3. Size check
If the ticket bundles independently shippable pieces, or will touch more than roughly 15 files, propose splitting it and ask. One reviewable PR per spec.

### 4. Explore the codebase
Read the repo's `CLAUDE.md` for conventions. Then launch the built-in `Explore` subagent (one per area in parallel if the ticket spans several) with the ticket summary and ask for: relevant files, the closest existing feature to copy, helpers to reuse, callers and consumers of what will change, existing tests and their conventions, and which existing dependencies already cover the need. Read the key files it points to yourself before relying on them.

### 5. Write the spec
Think in the skeleton's order: requirements, then the contract with the outside world, then design, then steps, then criteria. Write it to `.aderx-dev/specs/<TICKET>.md` with `status: draft`. Keep the headings exactly as written (other steps refer to them), omit an Interface sub-section that does not apply, and write no implementation code beyond signatures or short snippets. Only list files and callers you verified in the code.

````markdown
---
ticket: GGA-123
title: <ticket title>
linear_url: <url>
status: draft            # draft → approved → built → pr-open
base_branch: <git.baseBranch>
base_commit: <git rev-parse of the base branch>
branch: <type>/GGA-123   # type: feat, fix, refactor, docs, chore ... whichever fits the ticket
areas: [<area names from config>]
---

# GGA-123: <title>

## Overview
What is being built, its goal, and who uses it, when and why. Include anything from comments, linked docs or the tech plan that changes the interpretation.

## Goals and non-goals
**Goals:** ...
**Non-goals:** tempting things the builder should not do.
**Constraints:** performance, compatibility, environment.

## Interface and I/O contract
How it is used from outside: CLI arguments, endpoints, signatures, UI props and events, config keys, data schemas.

### Interface
| Name | Required | Type / default | Description |
|---|---|---|---|

### Input
Formats, sources, validation rules.

### Output
Formats, field or column names and types, ordering, units.

### Error behavior
Each failure condition and what happens. Unspecified error handling is where builders improvise.
| Condition | Behavior (message, exit code / status / UI state, partial output?) |
|---|---|

### Examples
Two or three realistic inputs → exact expected outputs.

## Architecture
Mermaid before/after in the same style (about 12 nodes, mark new or changed ones), or only "after" for a new component. For a small local change write "No diagram: the change is local to <X>".

## Dependencies
- **Reuse (already in the project):** ...
- **New (allowed):** name, version constraint, why. Or "No new dependencies".
- **Not allowed:** any dependency not listed above.

## Approach
Numbered steps in build order, each verifiable on its own, with the file paths and the existing helpers to reuse.
1. <step> - `path/to/file`: what and why.

## Affected scope
| Path | Change | Why |
|---|---|---|

**Blast radius:** callers/consumers, API contracts, migrations, config/env, flags, docs.

## Acceptance criteria
Numbered, Given/When/Then, each observable and testable. Every error-behavior row gets one. The IDs are reused by the verifier and the PR, so keep them stable.
- **AC1** Given ..., when ..., then ...

## Test plan
Every AC maps to at least one test, following the neighbouring tests' conventions.
| AC | Level | Test location and name | What it asserts |
|---|---|---|---|

**Manual verification:** only what automation cannot cover.

## Risks and open questions
- <question> - recommendation: ...

## Deviations
_Filled in by build._

## Implementation notes
_Filled in by build._

## Verification
_Filled in by build (verifier report)._
````

### 6. Review with the user
Give the file path, then summarize in chat: the requirements in a few lines, the interface and error behavior, dependencies, approach, affected scope, the acceptance criteria in full, and the open questions with your recommendations. Revise after each round of feedback and say what changed. Only a clear go-ahead ("approve", "LGTM", "go") is approval.

### 7. Save on approval
Set `status: approved`, write the ticket id to `.aderx-dev/current`, and point at `/aderx-dev:build <TICKET>` (running `/clear` first is fine: the spec is on disk). Offer to post a short plan summary as a Linear comment; do it only on a yes.
