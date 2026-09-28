---
name: pr-feedback
description: Handle review comments on a pull request (from Copilot or people) - check each one against the code, reproduce it where possible, fix the valid ones with regression tests, then commit, push and reply in each thread after the user approves. Use when the user asks to look at, address, fix or reply to review comments on a PR, even if they only say "check Copilot's review".
argument-hint: "[PR number or URL, defaults to the current branch's PR]"
allowed-tools: Bash(gh pr view *) Bash(gh pr diff *) Bash(gh pr checks *) Bash(git status *) Bash(git diff *) Bash(git log *)
---

# aderx-dev pr-feedback

Reviewers can be wrong, and so can their examples. Judge every comment against the real code before touching anything, then fix, then answer each thread with what actually changed.

User argument: `$ARGUMENTS`

## Steps

### 1. Collect the feedback
- Resolve the PR: the argument, else `gh pr view --json number` for the current branch.
- Unresolved review threads with their comment ids:
  ```bash
  gh api graphql -F owner=<owner> -F repo=<repo> -F n=<number> -f query='
    query($owner:String!,$repo:String!,$n:Int!){repository(owner:$owner,name:$repo){pullRequest(number:$n){
      reviewThreads(first:100){nodes{isResolved isOutdated path line
        comments(first:20){nodes{databaseId author{login} body}}}}
      reviews(last:20){nodes{author{login} state body}}}}}'
  ```
  Skip resolved threads. Also read review summaries and `gh pr view <n> --json comments` for top-level comments, and `gh pr checks <n>`: a failing check is feedback too.
- If `.aderx-dev/specs/<TICKET>.md` exists for the branch, read it: a comment that asks for something the spec rules out is a question for the user, not a fix.

### 2. Check every comment
For each one, read the code it points at and, when it claims a bug, reproduce it (a quick script or a test in a scratch directory, never against the real remote). Give each a verdict:
- **Valid**: reproduced or clearly true from the code.
- **Right idea, wrong example**: the example fails, but a real problem exists nearby. Describe the real one.
- **Not valid**: explain why, with evidence.
- **Needs a decision**: design choice or scope question for the user.

Note whether the problem comes from this PR or from older code.

### 3. Report and agree on scope
Show a table: #, reviewer, file:line, the comment in a few words, verdict, proposed fix. Ask which to fix (the default is all valid ones). Nothing is changed before this answer.

### 4. Fix
- Turn each reproduction into a regression test that fails before the fix, then fix the cause.
- Run the affected areas' `lint`, `typecheck` and `test` commands from `.aderx-dev/config.json` (or the repo's usual commands without it).
- If a fix changes the spec's interface or scope, record it under `## Deviations` in the spec.
- Draft one reply per thread: what changed, the commit, and the test that covers it; for "not valid", a short polite explanation with the evidence.

### 5. Approve commit, push and replies
Show the diffstat, the commit message (`fix(<TICKET>): address review on PR #<n>`), the push command (`git push`, to the PR's existing branch, never a force push), and every reply. Ask one question with these choices: **commit, push and reply** / **commit only** / **change something first**.

- Replies go out only after the push, so a "fixed" reply never points at code that is not on the PR yet.
- If the push fails or its permission prompt is declined, stop and report. Do not switch remotes or protocols or find another way to publish.

### 6. Post
Post each reply in its own thread:
```bash
gh api repos/<owner>/<repo>/pulls/<number>/comments/<databaseId>/replies -F body=@<reply-file>
```
Do not resolve threads unless asked. Report the new commit, which threads got replies, and anything left open.
