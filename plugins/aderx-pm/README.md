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

Each ticket's description links back to `docs/specs/<slug>/`, and `/aderx-dev:plan <ID>` picks up from there.

Requirements: a Linear connection, and `python3` for the breakdown checker. Tickets are filed to team Aderx3, project Constella (set in `skills/linear-issues/SKILL.md`).

## Where the gates are

- `refine` asks about product behavior only, never implementation, and stops when the readiness checklist passes.
- `tech-plan` puts real design decisions in front of you instead of choosing silently.
- `breakdown` runs `skills/breakdown/scripts/check_breakdown.py`, which works out the waves from `depends_on` and checks for unknown dependencies, cycles and same-wave file overlaps.
- `linear-issues` shows a preview and creates nothing without an explicit yes. It checks for duplicates and records what it created in `linear.md`, so running it again is safe.

## Layout

```
.claude-plugin/plugin.json
skills/                         pm (orchestrator), refine, tech-plan, breakdown, linear-issues
skills/breakdown/scripts/       check_breakdown.py (Python, stdlib only)
tests/                          python3 -m pytest tests/
```
