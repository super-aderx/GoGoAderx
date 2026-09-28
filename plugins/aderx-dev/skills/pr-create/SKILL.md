---
name: pr-create
description: Commit the built work and open a pull request whose description covers the changes, affected scope, tests and results, generated from the spec and the real diff. Use when the user wants to commit, push, open or create a PR for a built ticket.
disable-model-invocation: true
argument-hint: "[LINEAR-ID, defaults to the current ticket]"
allowed-tools: Bash(git status *) Bash(git diff *) Bash(git log *) Bash(git rev-parse *)
---

# aderx-dev pr-create

Turn finished work into commits and a pull request. This is the step with real-world side effects (commits, a push, a PR, possibly a Linear update), so it always shows the user exactly what will happen first.

**Pushing code needs the user's explicit approval, every time.** It is asked for on its own (step 7), separately from approving the commits and the PR text, and it is enforced twice: by this skill, and by the plugin's guard hook, which makes Claude Code show its own confirmation prompt for every `git push` even if the user's settings would otherwise allow it. Never try to get around either gate.

The allowed-tools above pre-approve only read-only git commands. Pushing and `gh` calls are deliberately left out.

User argument: `$ARGUMENTS`

## Steps

### 1. Load context
- Read `.aderx-dev/config.json`; if missing, tell the user to run `/aderx-dev:init` and stop.
- Resolve the ticket id: the argument, else `.aderx-dev/current`, else the current branch name.
- Read `<specs.dir>/<TICKET>.md` (the specs directory is `specs.dir` in the config, default `.aderx-dev/specs`). It should have `status: built` and a `## Verification` section with no failures. If the spec is missing, continue in **diff-only mode**: ask for the ticket id, say the PR description will be based on the diff alone, and skip the acceptance-criteria parts. If verification shows FAIL or UNVERIFIED items, stop and tell the user to finish `/aderx-dev:build` first.

### 2. Pre-flight
- Confirm you are on the spec's feature branch and not on a protected branch or the base branch.
- Run `git status` and `git diff --stat` against the base branch. List any changed files that fall outside the spec's affected scope and ask the user whether they belong. Compare changes to dependency manifests and lockfiles (see the profiles' `Dependency manifests` sections) with the spec's **Dependencies** section; any dependency the spec does not allow is a stop-and-ask.
- Look for things that must not be committed: `.env` files, credentials or keys, large binaries, editor or build artifacts. Flag them and leave them out.
- Re-run each affected area's `lint`, `typecheck` and `test` commands from config. Code may have changed since the verifier ran. If anything fails, stop and report it.

### 3. Plan the commits
aderx-dev's own files are not part of the ticket's changes: leave `.aderx-dev/config.json` and `.aderx-dev/profiles/` out of these commits, and do not count them as out-of-scope files. If they are still untracked, mention once that the team would benefit from committing them separately. The spec is different: when `specs.commit` is true in the config, include the spec file (`<specs.dir>/<TICKET>.md`) in the commits, preferably as its own `docs(spec): ...` commit; when it is false, the spec is excluded from git and must not be committed.

Follow `git.commitStyle` (conventional commits by default: `feat(scope): summary`). Put the ticket id in the footer (`Refs: ENG-123`). One logical commit is fine for a small change; split into several only when the diff has clearly separate concerns (for example a migration, then the API, then the UI). Stage files explicitly by path, never with `git add -A`.

### 4. Draft the PR
Write the title (`<type>(<scope>): <summary> (ENG-123)`) and body. If `pr.template` exists, use its structure and fill every section. Otherwise use this:

- **Summary:** what changed and why, in two to four sentences, with the Linear link.
- **Changes:** the main changes grouped by area.
- **Interface changes:** new or changed arguments, endpoints, signatures, output formats, and error behavior, taken from the spec's interface contract and confirmed against the diff. Say "None" if there are none.
- **Dependencies:** added, removed or upgraded, with the reason; or "None".
- **Affected scope:** files and modules touched plus the blast radius from the spec (callers, API contracts, migrations, config, flags).
- **Before / after:** the Mermaid diagrams from the spec, if any.
- **Testing:** the exact commands run and their real results, then a table of each AC with its status and the test that proves it. Only report what was actually run; never claim a check passed that was not run.
- **Deviations from the spec:** or "None".
- **Risks and rollout:** migrations, flags, backwards compatibility, what to watch after merging.
- **Notes for reviewers:** where to start reading.

Build the description from the real diff and the verification results, not from the plan alone.

### 5. Approve the commits and the PR text
Show the user: the branch and base branch, the commit messages, the list of files to be committed, and the full PR title and body. State that the PR will be opened as a draft (per `pr.draft`). Ask: "Create these commits?" Wait for a clear yes. If they want changes, revise and ask again.

This approval covers the local commits and the PR wording only. **It is not approval to push.**

### 6. Create the commits
Create the commits you just showed, locally. Then show `git log --oneline` for the new commits so the user can see exactly what exists.

### 7. Get explicit approval to push
Stop before any `git push` and ask the user for approval of the push itself. First gather the facts and show them:
- the remote name and its URL (`git remote get-url origin`);
- the branch, and whether it already exists on the remote (`git ls-remote --heads origin <branch>`), so the user knows if this creates a new branch or updates one;
- the exact commits that would be published (`git log --oneline` for the commits not yet on the remote) and the diffstat;
- the exact command you will run: `git push -u origin <branch>`. It is never a force push.

Say plainly that pushing publishes code to the remote. Then ask a specific question, for example: "Push these 3 commits to origin/eng-123-rate-limit?" Wait for a clear yes.

Rules for this gate:
- Approval of step 5 is never approval to push. Ask separately, after the commits exist and after showing the details above.
- Approval covers exactly the command you showed. If anything changes (more commits, another branch or remote), show the new details and ask again.
- If the user says no, or does not answer clearly, do not push. Leave the commits local, say so, and explain how to push later.
- The user will normally also see Claude Code's own permission prompt with a summary of the push. That is expected: the guard hook forces it for every `git push`, and it is the harness confirming the same action. If that prompt is declined, treat it as a "no". Do not retry, and do not look for another way to publish the code (another tool, an alias, a script, a different command).

### 8. Push and open the PR
Only after the approval in step 7:
- Run the approved `git push -u origin <branch>`. If it is rejected, stop and report; do not work around it and never force-push.
- Write the PR body to a temporary file outside the repo (for example via `mktemp`) and open the PR with `gh pr create --base <base> --title "<title>" --body-file <file>`, adding `--draft` when `pr.draft` is true. Use the PR text the user approved in step 5; if anything changed since, show the change and get approval again.

### 9. Wrap up
- Set `status: pr-open` and add `pr_url` to the spec frontmatter.
- Offer to update Linear (move to `linear.statusOnPrOpen` and/or comment the PR link). Do it only if the user says yes. If the branch name contains the ticket id, Linear may already have linked the PR.
- Give the user the PR URL and suggest `/aderx-dev:pr-review <number>` for a fresh-eyes review.
