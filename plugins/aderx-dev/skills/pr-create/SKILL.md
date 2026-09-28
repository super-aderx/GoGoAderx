---
name: pr-create
description: Commit the built work and open a pull request whose description covers the changes, affected scope, tests and results, generated from the spec and the real diff. Use when the user wants to commit, push, open or create a PR for a built ticket.
disable-model-invocation: true
argument-hint: "[LINEAR-ID, defaults to the current ticket]"
allowed-tools: Bash(git status *) Bash(git diff *) Bash(git log *) Bash(git rev-parse *)
---

# aderx-dev pr-create

Turn verified work into commits and a pull request. Commits and the PR text need one approval; **the push needs its own, separate approval** (step 6).

User argument: `$ARGUMENTS`

## Steps

### 1. Load context
- Read `.aderx-dev/config.json`; if missing, tell the user to run `/aderx-dev:init` and stop.
- Resolve the ticket id: the argument, else `.aderx-dev/current`, else the current branch name.
- Read `.aderx-dev/specs/<TICKET>.md`. Require `status: built` and a `## Verification` section with no FAIL or UNVERIFIED items; otherwise tell the user to finish `/aderx-dev:build` and stop. If it is `pr-open`, show `pr_url` and ask whether to continue.

### 2. Pre-flight
- Confirm you are on the spec's branch, not the base branch or a protected one.
- `git status` and `git diff --stat <base_branch>`. Flag and leave out anything that must not be committed: `.env` files, credentials or keys, large binaries, build artifacts. Never commit `.aderx-dev/`.
- Re-run each affected area's `lint`, `typecheck` and `test` commands: code may have changed since the verifier ran. If anything fails, stop and report.

### 3. Draft commits and PR
- **Commits:** `<type>(<TICKET>): <summary>`, for example `feat(GGA-12): add invite endpoint`, with `<type>` from the spec's branch. One commit for a small change; split only for clearly separate concerns. Stage files by path, never `git add -A`.
- **PR title:** same format as the commit.
- **PR body:** if the repo has `.github/pull_request_template.md` (any casing), fill its sections. Otherwise:
  - **Summary:** what and why in two to four sentences, with the Linear link.
  - **Changes:** grouped by area.
  - **Interface changes** and **Dependencies:** from the spec, confirmed against the diff; or "None".
  - **Affected scope:** files plus the spec's blast radius, and the before/after diagrams if any.
  - **Testing:** the exact commands run and their real results, then each AC with its status and the test that proves it. Never claim a check that was not run.
  - **Deviations**, **Risks and rollout**, **Notes for reviewers:** where to start reading.

### 4. Approve the commits and the PR text
Show the branch and base, the commit messages, the files per commit, and the full PR title and body. Ask "Create these commits?" and wait for a clear yes. This is not approval to push.

### 5. Create the commits
Create them locally and show `git log --oneline` for the new commits.

### 6. Get explicit approval to push
Show the remote URL (`git remote get-url origin`), whether the branch already exists there (`git ls-remote --heads origin <branch>`), the commits and diffstat that would be published, and the exact command: `git push -u origin <branch>` (never a force push). Ask, for example, "Push these 2 commits to origin/feat/GGA-12 and open the PR?"

- Approval of step 4 is never approval to push.
- Approval covers exactly what you showed. If anything changes, show it and ask again.
- On a no or an unclear answer, do not push. Leave the commits local and say how to push later.
- If Claude Code's own permission prompt for the push is declined, that is a no. Do not retry, and do not look for another way to publish (another remote, protocol, tool or script).

### 7. Push and open the PR
- Run the approved push. If it fails, stop and report the error; do not work around it.
- Write the approved body to a temp file outside the repo (`mktemp`) and run `gh pr create --base <base> --title "<title>" --body-file <file>`.
- Set `status: pr-open` and `pr_url` in the spec frontmatter.
- Offer to move the Linear ticket to In Review and comment the PR link; do it only on a yes.
- Give the PR URL. When the review comes in (Copilot or people), `/aderx-dev:pr-feedback` handles it.
