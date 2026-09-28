# aderx-pm

A Claude Code plugin that takes a raw feature idea all the way to Linear tickets:

```
/aderx-pm:pm             run the whole pipeline below, with a checkpoint after each stage
/aderx-pm:refine         grill a vague idea → docs/specs/<slug>/requirements.md
/aderx-pm:tech-plan      requirements → codebase-grounded design → docs/specs/<slug>/tech-plan.md
/aderx-pm:breakdown      design → parallelizable issues in dependency waves → docs/specs/<slug>/breakdown.md
/aderx-pm:linear-issues  breakdown → Linear parent issue + sub-issues (preview first) → docs/specs/<slug>/linear.md
```

Each stage writes a markdown file that the next stage reads, so you can stop, edit a file, and resume at any point. The skills also trigger on their own when you describe what you want ("grill me on this idea", "split this into tickets").

## Install

From the `gogoaderx` marketplace (see the [repo README](../../README.md)):

```
/plugin install aderx-pm@gogoaderx
```

Or try it straight from a checkout:

```bash
claude --plugin-dir /path/to/GoGoAderx/plugins/aderx-pm
```

Requirements: a Linear connection for `linear-issues` that you set up yourself (for example the claude.ai Linear connector, or `claude mcp add --transport http linear https://mcp.linear.app/mcp`), and Python 3 as `python3` for the breakdown checker.

## Where the gates are

- `refine` asks about product behavior only, never implementation, and stops when the readiness checklist passes.
- `tech-plan` puts real design decisions in front of you instead of choosing silently.
- `breakdown` validates the issue graph with `skills/breakdown/scripts/check_breakdown.py` (unknown dependencies, cycles, wave ordering, same-wave file overlaps).
- `linear-issues` shows a preview and creates nothing without an explicit yes. It checks for duplicates and records what it created in `linear.md`, so running it again is safe.

## Layout

```
.claude-plugin/plugin.json
skills/                         pm (orchestrator), refine, tech-plan, breakdown, linear-issues
skills/breakdown/scripts/       check_breakdown.py (Python, stdlib only)
tests/                          python3 -m pytest tests/
```
