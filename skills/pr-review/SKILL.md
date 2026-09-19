---
name: pr-review
description: Fetch a pull request from GitHub and review it with independent reviewer subagents, checking the code against the ticket's acceptance criteria as well as general quality, security and test coverage. Use when the user wants to review a PR, gives a PR number or URL, or asks for a second pair of eyes on a branch.
disable-model-invocation: true
argument-hint: "[PR number or URL, defaults to the current branch's PR]"
allowed-tools: Bash(gh pr view *) Bash(gh pr diff *) Bash(gh pr checks *) Bash(git fetch *) Bash(git show *) Bash(git log *) Bash(git diff *)
disallowed-tools: Edit Write
---

# gogoaderx pr-review

Review a PR the way a careful colleague would: does it do what the ticket asked, is it correct and safe, is it tested? The review is read-only. Findings are shown to the user first and only posted to GitHub if they say so.

User argument: `$ARGUMENTS`

## Steps

### 1. Resolve the PR
Use the argument (a number or URL). With no argument, use `gh pr view` to find the PR for the current branch. If none is found, ask. Read `.gogoaderx/config.json` if present (for area commands and `review.postComments`); the review still works without it.

### 2. Fetch the PR
- Metadata: `gh pr view <n> --json title,body,author,baseRefName,headRefName,isDraft,url,files,additions,deletions,commits,reviews,comments,statusCheckRollup`
- Diff: `gh pr diff <n>`. For very large diffs, list the files first and review them in groups by area.
- CI: `gh pr checks <n>`. Failing checks are findings in themselves.
- Context beyond the diff: if the PR branch is not checked out, run `git fetch origin pull/<n>/head:pr-<n>` (this creates a local ref and does not touch your working tree) and read surrounding code with `git show pr-<n>:<path>`. Do not switch branches or check out the PR without asking.

### 3. Find the requirements
Extract a ticket id (`[A-Z]+-\d+`) from the branch name, PR title or PR body.
- If `<specs.dir>/<ID>.md` exists locally (the specs directory is `specs.dir` in the config, default `.gogoaderx/specs`), use it: its acceptance criteria and affected scope are the yardstick.
- Otherwise, if the Linear tools are available, read the ticket and its comments and derive the criteria from them.
- If neither exists, review on general quality alone and say so.

### 4. Launch the reviewers
Launch the `reviewer` subagent (`gogoaderx:reviewer`). Give it the PR number, where to read the diff, the head and base refs, the spec path or ticket text, and the config path. It knows nothing about how the code was written, and that independence is the point. It reads the active profiles' `Review checklist` sections itself; if the PR is not in your local repo, tell it which profile files to apply. For a large PR that spans several areas, launch one reviewer per area in parallel and tell each which files are its own.

### 5. Verify and synthesize
Reviewers can be wrong. Before presenting anything:
- Open the code behind every BLOCKER and MAJOR finding and confirm it is real. Drop or downgrade findings you cannot substantiate.
- Merge duplicates across reviewers and sort by severity.
- Keep nitpicks to a few at most, and drop anything a formatter or linter already enforces.

### 6. Present locally
Show the user a verdict (APPROVE, COMMENT or REQUEST_CHANGES with one line of reasoning), the acceptance-criteria coverage table if you have criteria, then the findings by severity, each with file and line, the problem, why it matters and a suggested fix. Note anything you could not check.

### 7. Ask before posting
If `review.postComments` is `"never"`, stop after presenting. Otherwise ask what to post: nothing, a summary review only, or summary plus inline comments. Post only what they approve, using `gh pr review <n> --comment|--request-changes|--approve --body-file <file>` for the summary. If they approve inline comments, post them through the GitHub API with each comment anchored to its file and line, and show the exact text first. Never approve or request changes on the user's behalf without an explicit instruction to do so.
