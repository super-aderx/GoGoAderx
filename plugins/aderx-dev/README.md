# aderx-dev

A Claude Code plugin for a ticket-to-PR workflow that works with any language:

```
/aderx-dev:init      one-time setup per repo → .aderx-dev/config.json (+ optional language profiles)
/aderx-dev:plan      Linear ticket → spec (you approve it) → saved to .aderx-dev/specs/
/aderx-dev:build     implement spec (feature + tests) → independent verifier checks every AC
/aderx-dev:pr-create commit + PR description from spec and real diff (asks before pushing)
/aderx-dev:pr-review fetch a PR → independent reviewer subagents → findings (asks before posting)
```

The spec file is the handoff between steps, so you can `/clear` between them.

## Install

From the `gogoaderx` marketplace (see the [repo README](../../README.md)):

```
/plugin install aderx-dev@gogoaderx
```

Or try it straight from a checkout:

```bash
claude --plugin-dir /path/to/GoGoAderx/plugins/aderx-dev
```

Then, inside your repo:

1. Connect Linear if you haven't yet (one time): the claude.ai Linear connector, or `claude mcp add --transport http linear https://mcp.linear.app/mcp` and then sign in through `/mcp`.
2. `/aderx-dev:init` → confirm the detected commands and choose your profiles.
3. `/aderx-dev:plan ENG-123`

Requirements: `git`, the GitHub CLI `gh` (authenticated) for the PR steps, and Python 3.9+ available as `python3` for the two hook scripts. That is a requirement of the plugin's hooks, not of your project: your project can be in any language. On Windows you may need to change `python3` to `python` in `hooks/hooks.json`.

## What a spec contains

`/aderx-dev:plan` works through the spec in a fixed order, because each stage feeds the next:

**requirements → interface and inputs/outputs → architecture → dependencies → steps → acceptance criteria and tests**

| Section | What it pins down |
|---|---|
| Overview, Goals and non-goals | what is being built, its goal, usage scenarios, constraints, what is out of scope |
| Interface and I/O contract | arguments, endpoints or signatures (name, required/optional, type, default, meaning), input and output formats and field names, **error behavior** (condition → message, exit code or status, partial output), and concrete examples |
| Architecture | before/after Mermaid diagrams |
| Dependencies | what to reuse, which new dependencies are allowed and why, and "nothing else may be added" |
| Approach | ordered, individually verifiable steps with file paths |
| Affected scope | files and blast radius |
| Acceptance criteria, Test plan | numbered `AC1..ACn` (each error-behavior row gets one), each mapped to a test |

Downstream steps enforce the contract: `build` must follow the interface exactly and may not add unlisted dependencies (needing one is a stop-and-ask), `verifier` exercises the interface with the spec's examples and diffs dependency manifests against the Dependencies section, `reviewer` checks the code against the contract, and `pr-create` reports interface changes and dependency changes in the PR description.

## Language profiles (optional)

The skills, agents and hooks contain no language-specific knowledge. Everything specific to a stack lives in a **profile**: one markdown file per stack.

A profile has fixed sections that the workflow looks up by name:

| Section | Used by |
|---|---|
| Detect, Area defaults | `init`: how to recognize the stack and seed the config |
| Where to look | `explorer` subagent while planning |
| Testing conventions | `plan` (test plan) and `build` |
| Dependency manifests | `plan` (Dependencies section), `verifier` and `pr-create` (unlisted dependency changes) |
| Build notes | `build` |
| Shortcuts to flag | `verifier` (skipped tests, lint/type suppressions, debug leftovers) |
| Review checklist | `reviewer` |

**You decide what to use.** Built-in profiles ship in `skills/init/profiles/` (`python`, `react`). During `/aderx-dev:init`, each profile that matches your repo is offered and you say yes or no. Accepted ones are copied into your project at `.aderx-dev/profiles/<name>.md`, listed under `profiles` in the config, and from then on belong to your repo: edit them, commit them, share them with your team.

- **No profiles:** decline them all and aderx-dev runs on per-area commands alone (test, lint, typecheck, format from the config), with generic review and verification behavior.
- **Another language:** `init` offers to generate a custom profile for a stack with no built-in one, by filling `skills/init/profiles/_template.md` from evidence in your repo (build files, CI workflows, Makefile, README). You review it before it is written. You can also copy the template by hand.
- **Changing your mind later:** add or remove a name in `profiles` in the config, and add or delete the file in `.aderx-dev/profiles/`.

Because only `init` reads the plugin's own files, everything else works from the copies in your project.

## Layout

```
.claude-plugin/plugin.json
skills/                         init, plan, build, pr-create, pr-review
skills/init/profiles/           python.md, react.md, _template.md
agents/                         explorer (read-only), verifier, reviewer
hooks/hooks.json                registers the two hooks below
scripts/                        hook scripts (Python, stdlib only)
tests/                          python3 -m pytest tests/
```

## Where the gates are

| Step | Model can auto-trigger it | Confirmation before side effects |
|---|---|---|
| plan | yes | posting a comment to Linear |
| build | no (`disable-model-invocation`) | none needed: local edits on a feature branch |
| pr-create | no | commits and PR text need a yes; **the push needs its own separate yes** (plus Claude Code's own prompt, forced by the guard hook); Linear update needs a yes |
| pr-review | no | posting anything to GitHub needs a yes; `review.postComments: "never"` disables posting |

`pr-create` pre-approves only read-only git commands in `allowed-tools`.

### Pushing needs your approval, twice over

1. **In the skill:** after the commits are created, `pr-create` stops and asks about the push on its own, showing the remote URL, the branch (new or existing), the exact commits and diffstat, and the exact command. A yes to the commits or the PR text does not count. If anything changes afterwards it asks again, and a "no" leaves the commits local.
2. **In the harness:** the `guard_git` hook answers every real `git push` with `permissionDecision: "ask"`, so Claude Code shows its own confirmation prompt listing what will be published. This applies to any push in an initialized repo (not just from `pr-create`), and it applies even if your settings have an allow rule for pushes. `--dry-run` pushes are not prompted.

Force pushes, pushes to protected branches and `gh pr merge` are not prompted at all: they are blocked outright.

**Limits, so you know what this does and doesn't promise.** The hook recognizes `git push` written in a Bash command; a push made some other way (a script that pushes internally, or a GitHub API call) is not recognized. `git -C <path> push` is checked against the repository at `<path>`, but a `cd <path> && git push` is checked against the session's own repository. Claude Code's "ask" is also reported not to prompt in some permission modes and surfaces: reports say it is honored in the terminal CLI, including auto-accept, but not in the VS Code panel's auto mode nor in the `auto` permission mode. There is also a report that an "ask" from a hook can override a `permissions.deny` rule for the same command. Treat the skill's own approval question as the layer that always applies, and check how your setup behaves once: run `git push --dry-run` (no prompt expected), then a real push on a scratch branch (prompt expected).

`pr-review` sets `disallowed-tools: Edit Write`, and the `reviewer` and `explorer` subagents have no Edit or Write tools. They do have Bash (to run `gh` and `git`), so staying read-only is an instruction they follow, not something the harness enforces: a Bash command could still change files.

## Hooks

Both hooks only act in repos that contain `.aderx-dev/config.json`.

- **format_on_edit** (PostToolUse on Edit/Write): runs the matching area's `format` command on the single edited file. Which area owns a file is decided by extension and by the file living under the area's `root`. If the formatter fails, Claude sees the error; if it isn't installed the hook stays silent. Dependency and build directories are skipped, and `hooks.formatIgnoreDirs` in the config adds more.
- **guard_git** (PreToolUse on Bash): blocks force pushes, pushes to protected branches (`git.protectedBranches` plus `git.baseBranch`, including a bare `git push` while on one), `git push --all`, and `gh pr merge`. Every other real `git push` triggers a confirmation prompt that describes what will be published (see "Pushing needs your approval" above).

Ideas to add later if you feel the need: a spec gate (block source edits while the active spec is `draft`), a SessionStart hook that prints the current ticket and status, and a Stop hook that keeps the builder going while tests fail (guard it with the `stop_hook_active` flag to avoid loops).

## Config

`.aderx-dev/config.json` is created by `/aderx-dev:init`; the schema and field notes are in `skills/init/SKILL.md`. Commit it so your team shares the same commands. Specs are saved in `specs.dir` (default `.aderx-dev/specs/`). They are excluded from git through `.git/info/exclude` unless you set `specs.commit: true`, in which case `pr-create` commits the spec with the ticket's changes. `linear.team` lets you type `/aderx-dev:plan 123` instead of `ENG-123`. `.aderx-dev/config.json` and `.aderx-dev/profiles/` are never part of a ticket's commits; commit them on their own.

## Tests

```bash
python3 -m pytest tests/
```

`test_hooks.py` exercises both hook scripts. `test_plugin_structure.py` guards the design: skills and agents must contain no language-specific terms (those belong in profiles), every profile must have all the sections the skills look up, and the config example and hook wiring must be valid.

## Not yet verified (check on first run)

The hook scripts and structure are tested. The skills and agents are prompts and were not run end to end against a real repo, so expect to tune them:

- Linear tool names from whichever Linear connection you use.
- Whether `init` finds its bundled profiles through `${CLAUDE_SKILL_DIR}` on your Claude Code version (it has a fallback search and will ask for the path if needed), and how well it detects commands on your layout.
- That `verifier` and `reviewer` are invoked as subagents from the skills (referenced as `aderx-dev:verifier` and so on).
- Skill frontmatter behavior (`disable-model-invocation`, `allowed-tools`, `disallowed-tools`) on your Claude Code version.
