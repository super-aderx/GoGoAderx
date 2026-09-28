---
name: init
description: Set up aderx-dev in the current repository. Detects the base branch, the Linear team key, and the test, lint, typecheck and format commands for each part of the codebase, then writes .aderx-dev/config.json. Use when the user wants to set up, configure or reconfigure aderx-dev, or when another aderx-dev skill says the config is missing.
disable-model-invocation: true
---

# aderx-dev init

Create `.aderx-dev/config.json`. Every other aderx-dev skill, subagent and hook reads it, so getting the commands right here is what stops later steps from guessing. Stack conventions (testing style, patterns, pitfalls) are not configured here: they belong in the repo's `CLAUDE.md`, which every step already reads.

## Steps

1. **Locate the repo.** Run `git rev-parse --show-toplevel` and work from there. If this is not a git repository, stop and say so.
2. **Existing config?** If `.aderx-dev/config.json` exists, show it and ask whether to update it or leave it alone. Never overwrite silently.
3. **Detect the settings.**
   - Base branch: `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`); fall back to `main`, then `master`.
   - Linear team key: from recent branch names or commit subjects matching `[A-Z]+-\d+`. If nothing matches, ask.
   - Areas: an area is a directory with its own build and test setup (a single-package repo has one area with `root` `"."`). Find them from the build or package manifests at the top level and one level down, and name them by role (`backend`, `frontend`, `app`, ...).
   - Commands per area: from CI workflows, Makefile or task-runner targets, manifest scripts, lockfiles (which runner or package manager), and the README. Leave out any command the project does not have.
4. **Show the draft and get confirmation.** Per area, a small table of the commands; flag anything you are unsure about. Also confirm each executable exists (`command -v <tool>`); report missing ones instead of quietly changing them. Do not run full test suites here.
5. **Write the files.**
   - `.aderx-dev/config.json`.
   - In the repo's local exclude file (`git rev-parse --git-path info/exclude`), append `.aderx-dev/current` and `.aderx-dev/specs/` if they are missing. Touch no other lines.
6. **Linear access.** Check that Linear tools are available (look them up with ToolSearch if they are deferred). If not, tell the user to connect Linear and sign in through `/mcp`.
7. **Finish** by pointing at `/aderx-dev:plan <TICKET-ID>`.

## Config schema

```json
{
  "linear": { "team": "GGA" },
  "git": {
    "baseBranch": "main",
    "protectedBranches": ["main", "master", "develop", "release/*"]
  },
  "areas": {
    "app": {
      "root": ".",
      "extensions": [".ext"],
      "test": "make test",
      "lint": "make lint",
      "typecheck": "make typecheck",
      "format": "make format-file FILE={file}"
    }
  }
}
```

The `areas` entry is only an illustration of the shape; write the real commands you detected.

- `linear.team`: a bare ticket number like `123` passed to `/aderx-dev:plan` expands to `<team>-123`.
- `git.protectedBranches`: the guard hook refuses pushes to these (glob patterns allowed). The base branch is always protected too.
- `areas.<name>.root`: directory relative to the repo root. All commands run from there.
- `areas.<name>.extensions`: which edited files the format hook handles for that area.
- `areas.<name>.format` must contain `{file}`: the format hook runs it on the single edited file after every edit, so a whole-project formatter would be slow and noisy. An area without `format` is not auto-formatted.
- `areas.<name>.test` must run once and exit; a watch mode would hang the workflow.
