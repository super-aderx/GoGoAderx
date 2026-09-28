---
name: linear-issues
description: Create Linear tickets from a feature breakdown via the Linear MCP server — one parent issue with sub-issues, blocked-by relations between waves, the spec attached as a Linear document, duplicate checks, and a preview the user approves before anything is created. Use this whenever the user wants to "create the tickets", "push these issues to Linear", "file this in Linear", or has a docs/specs/<slug>/breakdown.md ready to ship to their tracker.
---

# Create Linear issues

Tickets are outward-facing: teammates get notified and they're tedious to clean up. So this stage is careful: preview first, create only after an explicit yes, never create duplicates, and keep a local record so a re-run is safe.

The Linear tools come from the Linear MCP server (`mcp__claude_ai_Linear__*` or similar). If they're not loaded, look them up with ToolSearch. If no Linear MCP is connected at all, say so and stop — don't fake it.

## 1. Load inputs

- `docs/specs/<slug>/breakdown.md` — the issues to create. If it's missing, offer to run `aderx-pm:breakdown` first.
- `docs/specs/<slug>/linear.md` — if it exists, this feature was (partly) filed before. Issues already listed there must not be created again.

## 2. Where do they go?

The target is fixed, so don't ask:

- **Workspace:** aderx3
- **Team:** Aderx3
- **Project:** Constella

Every ticket (parent and sub-issues) is created in team Aderx3 with `project` = Constella. Confirm with `list_projects` that Constella still exists; if it doesn't, stop and tell the user rather than filing elsewhere.

Labels: use exactly one of the existing labels to set the ticket type: **Feature** (new capability), **Improvement** (change to existing behavior), or **Bug** (broken behavior). Check `list_issue_labels` and don't create new labels unless the user agrees.

## 3. Check for duplicates

For the parent and each issue, search the team with `list_issues` using the key words of the title. If something looks like the same work, show it in the preview and let the user decide: skip, link as related, or create anyway.

## 4. Preview and get approval

Show a table before creating anything:

```
Team: Aderx3 · Project: Constella · Parent: "Team invites" (new)

| #  | Title                         | Type    | Wave | Blocked by | Est | Note                    |
|----|-------------------------------|---------|------|------------|-----|-------------------------|
| I1 | Invite data model & API types | Feature | 0    | —          | S   |                         |
| I2 | Send invite email             | Feature | 1    | I1         | M   | possible dup of CSA-88  |
...
Also: attach requirements.md + tech-plan.md as a Linear document on the parent.
```

Below the table, show the full rendered description (see "Ticket template" below) for at least the parent and one sub-issue, and for every Bug ticket, so the user can check the content, not just the titles.

Wait for an explicit go-ahead. Apply any edits the user asks for, and show the preview again if the changes are big.

## 5. Create in dependency order

1. **Parent issue**: title = feature name; description follows the ticket template, with the wave plan and links to the spec files added under Others.
2. **Spec document**: `save_document` with `issue` = the parent, containing requirements + tech plan (one document, or two if they're long).
3. **Sub-issues, wave by wave**: `save_issue` with `parentId` = the parent, and `blockedBy` = the Linear identifiers of the issues it depends on. Creating in wave order means blockers always exist before the issues that reference them.
   - Description follows the ticket template, filled from the issue's section in breakdown.md. Make it self-contained: an agent reading only this ticket should be able to implement it.
   - Map S/M/L to the team's estimate scale if it uses estimates.
   - Don't upload files to Linear. The user attaches screenshots, recordings, and other files to the ticket themselves.
4. **Record as you go**: after each successful create, append it to `linear.md`. If a call fails partway, stop, report what was created and what wasn't, and leave `linear.md` accurate so a re-run picks up where it stopped.

`linear.md` format:

```markdown
# <Feature> — Linear

Team: <team> · Project: <project>
Parent: ENG-120 <url>

| Local ID | Linear | Title | Wave | Blocked by |
|---|---|---|---|---|
| I1 | ENG-121 | ... | 0 | — |
```

Also add the Linear identifier next to each issue heading in breakdown.md (e.g. `### I1: <title> — ENG-121`) so the two files stay linked.

## Ticket template

Every ticket description uses these sections, in this order. Leave out a section only where noted.

```markdown
## Description
As a <role>, I want to <action>, so that <value>.
<!-- For a Bug: a short description of what's broken, who hits it, and how bad it is. -->

<Extra context the user and you agreed on in the earlier stages.>

## Proposed Solution
<!-- Base these on the current codebase (name real files, modules, APIs) and the tech plan.
     A decision already recorded in tech-plan.md is settled: write it as the one option, no alternatives.
     Give more than one option only for a choice that is still open. -->
### Option A: <name> (recommended)
<How it works, and which files and components it touches.>
- Pros: ...
- Cons: ...

### Option B: <name>
<How it works.>
- Pros: ...
- Cons: ...

**Recommendation:** <which option and why, in a sentence or two.>

## Expected Result / Actual Result
<!-- Bug tickets only; leave this section out for Feature and Improvement. -->
**Steps to reproduce**
1. ...
2. ...

**Expected result:** ...
**Actual result:** ...
**Environment:** <app version, commit, browser/OS/device, account or data needed>

## Acceptance Criteria
- [ ] <A specific check anyone can verify, not "works correctly".>
- [ ] <For a Bug: the repro steps above now give the expected result.>
- [ ] <Tests, or other ways to verify.>

## Blockers
- **Upstream:** <tickets or decisions this one waits on, such as CSA-12, or "None">
- **Downstream:** <tickets that wait on this one, or "None">
- **Parent:** <parent ticket, if this was split out of a larger one>

## Others
<Logs and links the user submitted. Put logs in code blocks and trim them to the relevant lines. For files the user will attach, list them by name, such as "Screenshot of error dialog (to be attached)". Write "None" if there's nothing.>
```

Rules:

- **Description** is the user story (or bug description) the user submitted, refined together with the user in earlier stages. Don't invent a new one here. If it's missing or vague, ask before filing.
- **Proposed Solution** must be grounded in the actual code and must not reopen decisions from tech-plan.md. Don't propose APIs or modules that don't exist unless the option is to create them.
- **Others** on every sub-issue starts with `Spec: docs/specs/<slug>/ (issue I<n>)`, so `/aderx-dev:plan` can find the tech plan and treat its contracts as settled.
- **Bug tickets** must include enough detail for someone else to reproduce the bug. If the steps, expected result, or actual result are missing, ask the user instead of guessing.
- **Blockers** in the text must match the `blockedBy` relations set on the issue.

## 6. Report

List the created issues with URLs, grouped by wave, and say plainly which ones can start in parallel **right now** (wave 0, or everything whose blockers are done).

If any ticket lists files "to be attached" under Others, remind the user which tickets need which files, so they can upload them.
