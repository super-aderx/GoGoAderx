---
name: build
description: Implement an approved aderx-dev spec (feature code and tests), run lint, typecheck and tests, then have an independent verifier subagent check every acceptance criterion. Use when the user wants to build, implement or code up a planned ticket.
disable-model-invocation: true
argument-hint: "[LINEAR-ID, defaults to the current ticket]"
---

# aderx-dev build

Implement the approved spec, prove it works, and leave the work uncommitted on a feature branch for `/aderx-dev:pr-create`. You are not the judge of your own work: a separate `verifier` subagent is.

User argument: `$ARGUMENTS`

## Steps

### 1. Load the spec
- Read `.aderx-dev/config.json`. If missing, tell the user to run `/aderx-dev:init` and stop.
- Resolve the ticket id: the argument, else `.aderx-dev/current`, else the id in the current branch name, else ask.
- Read `.aderx-dev/specs/<TICKET>.md` in full. If it does not exist, tell the user to run `/aderx-dev:plan <TICKET>` and stop.
- Require `status: approved`. If it is `draft`, stop: an unapproved spec is not a contract. If it is `built` or `pr-open`, ask whether they want to rebuild or continue.

### 2. Prepare the branch
- Run `git status`. If there are unrelated uncommitted changes, ask the user whether to stash them or proceed.
- Switch to the spec's `branch`, creating it from `base_branch` if needed. Never build on a protected branch. If the base branch has moved a lot since `base_commit`, mention it.
- Turn the spec's Approach steps into a task list and tick them off as you go.

### 3. Implement, tests first
For each step of the Approach:
- Write or extend the tests from the spec's Test plan first, and run them to confirm they fail for the right reason. Then implement until they pass. This is what makes the tests prove something.
- Follow the repo's `CLAUDE.md`, its existing patterns, and the helpers the spec points to. Look at neighbouring code and tests before writing new ones.
- Build to the spec's **Interface and I/O contract** exactly: the names, parameters, formats, field names and error behavior it defines. Do not add dependencies beyond the spec's **Dependencies** section. If you find you need to go outside the affected scope, the contract or the dependency list, see step 4.
- Formatting runs automatically after each edit via a hook. If the hook reports a formatter error, fix it.

### 4. Handle deviations honestly
Reality sometimes disagrees with the plan.
- **Minor** (a name, an extra helper, a small detail that changes no AC, no scope, no interface and no dependency): proceed and record it under `## Deviations` in the spec.
- **Significant** (an AC cannot be met as written, the approach does not work, scope must grow, the interface or error behavior must change, or a new dependency is needed): stop, explain what you found, and ask the user. Update the spec only with their agreement.

### 5. Run the project checks
For every area listed in the spec's `areas`, run that area's `lint`, `typecheck` and `test` commands from `.aderx-dev/config.json`, from the area's `root`. Fix failures at the cause. Do not skip, delete or weaken tests, and do not add lint or type-check suppressions or focus/skip markers just to get green. If a failure is unrelated and pre-existing, prove it (for example by running it on the base branch) and report it instead of hiding it.

### 6. Independent verification
Launch the `verifier` subagent (`aderx-dev:verifier`), giving it the path to the spec and nothing else about your process. It checks each acceptance criterion against real evidence, and also the interface contract and the dependency list, and reports PASS, FAIL or UNVERIFIED.
- If anything is FAIL or UNVERIFIED, fix the code or add the missing test, then run the verifier again. Allow up to three rounds.
- Do not argue the verifier down. If you believe it is wrong, say so to the user with your evidence instead of overriding it.
- If it is still not clean after three rounds, stop and report exactly what remains.

### 7. Record the outcome
Update the spec:
- `## Deviations`: everything that differs from the plan (or "None").
- `## Implementation notes`: what was built, the files actually changed, and anything a reviewer should look at first.
- `## Verification`: paste the verifier's final report.
- Frontmatter `status: built`.

### 8. Hand off
Do not commit or push; that is `/aderx-dev:pr-create`'s job, behind a confirmation. Give the user a short summary: what was built, the AC results, any deviations, and any pre-existing failures. Then point at `/aderx-dev:pr-create`.
