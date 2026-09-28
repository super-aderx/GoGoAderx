# aderx-dev

Ticket-to-PR workflow:

```
/aderx-dev:init         one-time per repo → .aderx-dev/config.json (base branch, Linear team, per-area commands)
/aderx-dev:plan GGA-12  Linear ticket → spec you approve → .aderx-dev/specs/GGA-12.md
/aderx-dev:build        implement the spec, tests first → independent verifier checks every AC
/aderx-dev:pr-create    commits + PR from spec and real diff (approve commits, then approve the push)
/aderx-dev:pr-feedback  triage Copilot/reviewer comments → fix → commit, push, reply in each thread
```

The spec is the handoff between steps, so `/clear` between them is fine. If the ticket came from aderx-pm, `plan` reads the linked `docs/specs/<slug>/tech-plan.md` and treats its decisions as settled.

Naming follows the GGA-1 style: branch `feat/GGA-12`, commits and PR title `feat(GGA-12): summary`, PR ready for review.

Stack conventions (test style, patterns, pitfalls) live in each repo's `CLAUDE.md`, not in this plugin.

## Requirements

`git`, an authenticated `gh`, a Linear connection (claude.ai connector or `claude mcp add --transport http linear https://mcp.linear.app/mcp`), and `python3` for the hooks.

## Gates

| Step | Asks before |
|---|---|
| plan | approving the spec; posting to Linear |
| build | nothing (local edits on the feature branch); stops on significant deviations |
| pr-create | creating commits; **pushing, as a separate question**; updating Linear |
| pr-feedback | changing code (you pick which comments to fix); commit, push and replies together |

`build`, `pr-create` and `init` only run when you call them. `plan` and `pr-feedback` can also trigger from plain requests.

## Hooks

Both only act in repos with `.aderx-dev/config.json`.

- **format_on_edit** (after Edit/Write): runs the owning area's `format` command on the edited file. A formatter error is shown to Claude; a missing formatter is ignored.
- **guard_git** (before Bash): blocks force pushes, pushes to the base or a protected branch (including a bare `git push` while on one, and `git -C <path>`), `git push --all`/`--branches`, and `gh pr merge`. Everything else goes through Claude Code's normal permission prompt. Branch protection on GitHub is still the real safety net.

## Layout

```
skills/   init, plan, build, pr-create, pr-feedback
agents/   verifier (read-only, independent AC check)
hooks/    hooks.json → scripts/*.py (stdlib only)
tests/    python3 -m pytest tests/
```
