---
name: init
description: Set up aderx-dev in the current repository. Detects the base branch, the tooling for each part of the codebase (test, lint, typecheck and format commands), offers language profiles (built-in or generated) that the user can accept or decline, and writes .aderx-dev/config.json. Use when the user wants to set up, configure or reconfigure aderx-dev, or when another aderx-dev skill says the config is missing.
disable-model-invocation: true
---

# aderx-dev init

Create `.aderx-dev/config.json` and, if the user wants them, `.aderx-dev/profiles/*.md`. Every other aderx-dev skill, subagent and hook reads these, so getting the commands right here is what stops later steps from guessing.

**Language profiles are optional.** aderx-dev works for any stack with nothing but per-area commands in the config. A profile is a markdown file holding one stack's conventions (how to detect it, where to look in the code, testing conventions, shortcuts to flag, a review checklist). The user decides which ones to adopt; nothing language-specific is applied without their yes.

## Where the built-in profiles live

They ship inside this skill's folder: `${CLAUDE_SKILL_DIR}/profiles/`. List that directory. Every `*.md` file except `_template.md` is a built-in profile.

If the text `${CLAUDE_SKILL_DIR}` appears unexpanded, or the directory does not exist, locate it: run `find "$HOME/.claude/plugins" -type d -path '*aderx-dev*/skills/init/profiles' 2>/dev/null`. If that finds nothing (for example the plugin was loaded from a local folder), ask the user for the plugin's path. If profiles truly cannot be found, continue in profile-free mode and say so.

## Steps

1. **Locate the repo.** Run `git rev-parse --show-toplevel` and work from there. If this is not a git repository, stop and say so.

2. **Check for an existing config.** If `.aderx-dev/config.json` exists, show it and ask whether to update it or leave it alone. Never overwrite silently.

3. **Detect the language-independent settings.**
   - Base branch: `git symbolic-ref --short refs/remotes/origin/HEAD` (strip the `origin/` prefix); fall back to `main`, then `master`, whichever exists.
   - PR template: `.github/pull_request_template.md` or `.github/PULL_REQUEST_TEMPLATE.md`, if present.
   - Linear team key: infer from recent branch names or commit subjects matching `[A-Z]+-\d+`. If nothing matches, ask.

4. **Detect the parts of the codebase (areas).** List the top level and one level down to find build or package manifests and the directories that hold separate applications or libraries. An area is a directory with its own build and test setup; a single-package repo has one area with `root` `"."`. Name areas by role (`backend`, `frontend`, `app`, `cli`, and so on).

5. **Offer profiles, one decision per stack.**
   - For each built-in profile, read its `## Detect` section and check whether the repo matches. For each match, tell the user what the profile contains and ask whether to use it.
   - For an area that matches no built-in profile, offer to **generate a custom profile**: read `${CLAUDE_SKILL_DIR}/profiles/_template.md`, then fill every section from evidence in the repo (build files, CI workflows, a Makefile or task runner, CONTRIBUTING or README, existing tests and configs). Write only what you can support, mark unknowns `n/a`, and show the result for approval.
   - The user may decline profiles entirely. In that case configure the areas by inference alone (CI workflows, Makefile targets, README instructions) and confirm each command with them.

6. **Draft the config** using the schema below. For an area with an accepted profile, seed it from that profile's `## Detect` and `## Area defaults`. Leave out any command the project does not have. All commands run from the area's `root`. The exception is `format`, which must contain the `{file}` placeholder, because the format hook runs it after every single edit on only the edited file. A formatter that touches the whole project on each edit would be slow and noisy. Test commands must run once and exit; a watch mode would hang the workflow.

7. **Show the draft and get confirmation.** Present the profiles chosen and, per area, the commands as a small table, and flag anything you are unsure about. Wait for the user to confirm or correct.

8. **Check the commands can run.** For each command, confirm the executable exists (for example `command -v <tool>`). Report anything missing instead of quietly changing it. Do not run full test suites here.

9. **Write the files.**
   - `.aderx-dev/config.json`.
   - Copy each accepted built-in profile from the skill folder to `.aderx-dev/profiles/<name>.md`; write approved generated profiles to the same place. The project now owns those files: they can be edited and should be committed alongside the config.
   - Set up ignore rules without touching tracked files: append these lines to the repo's local exclude file (find it with `git rev-parse --git-path info/exclude`), skipping any already present: `.aderx-dev/current`, and `<specs.dir>/` (default `.aderx-dev/specs/`) when `specs.commit` is false.

10. **Linear access.** The plugin does not ship a Linear connection; the user brings their own. Check that Linear tools are available (look them up with ToolSearch if they are deferred). If there are none, tell the user to connect Linear, for example with the claude.ai Linear connector or `claude mcp add --transport http linear https://mcp.linear.app/mcp`, and to sign in through `/mcp`.

11. **Finish** by pointing at the next step: `/aderx-dev:plan <TICKET-ID>`.

## How the other skills use profiles

`profiles` in the config lists the active profile names. Skills and subagents read `.aderx-dev/profiles/<name>.md` for each one, and use these sections: `Where to look` (planning), `Testing conventions` (test plan and build), `Dependency manifests` (planning, verification and PR checks), `Build notes` (build), `Shortcuts to flag` (verification), `Review checklist` (review). If an area has a `profile`, that profile governs files in that area. If no profiles are listed, everything still works with generic behavior.

## Config schema

```json
{
  "version": 1,
  "profiles": [],
  "linear": { "team": "ENG", "statusOnPrOpen": "In Review" },
  "git": {
    "baseBranch": "main",
    "branchPattern": "{ticket}-{slug}",
    "commitStyle": "conventional",
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
  },
  "specs": { "dir": ".aderx-dev/specs", "commit": false },
  "pr": { "draft": true, "template": ".github/pull_request_template.md" },
  "review": { "postComments": "ask" },
  "hooks": { "formatIgnoreDirs": [] }
}
```

The `areas` entry above is only an illustration of the shape; write the real commands you detected. Add `"profile": "<name>"` to an area to tie it to a profile.

Field notes:

- `profiles`: names of the active profiles, i.e. the file names under `.aderx-dev/profiles/` without `.md`. Empty means profile-free.
- `git.branchPattern`: `{ticket}` is the lower-case ticket id (`eng-123`), `{slug}` is a kebab-case title of at most five words. Keeping the ticket id in the branch name lets Linear link the PR automatically.
- `git.protectedBranches`: the guard hook refuses pushes to these (glob patterns allowed). The base branch is always protected too.
- `areas.<name>.root`: directory relative to the repo root.
- `areas.<name>.extensions`: which edited files the format hook handles for that area. An area with no `format` command is simply not auto-formatted.
- `specs.dir`: where specs are saved (default `.aderx-dev/specs`); for example `docs/specs` if you want them committed in a visible place.
- `specs.commit`: whether approved specs are committed with the code (useful for reviewers) or kept local. `pr-create` includes the spec in its commits only when this is true.
- `linear.team`: your Linear team key; a bare ticket number like `123` passed to `/aderx-dev:plan` expands to `<team>-123`.
- `pr.draft`: open PRs as drafts by default.
- `review.postComments`: `"ask"` (default) shows findings locally and asks before posting; `"never"` never posts.
- `hooks.formatIgnoreDirs`: extra directory names the format hook should skip, on top of its built-in list of dependency and build directories.
