---
name: pm
description: End-to-end product-management pipeline that takes a raw feature idea all the way to Linear tickets — refine requirements, design the technical plan, break into parallelizable issues, create them in Linear. Use this whenever the user wants to go "from idea to tickets", says things like "PM this", "help me spec and plan this feature", "turn this into issues", or describes a new product/feature idea and wants it ready for implementation (including by multiple agents). Also use it to resume a half-finished spec in docs/specs/.
---

# PM pipeline (orchestrator)

This skill chains four stage skills. Each stage writes a markdown file, and the next stage reads that file, so the pipeline can stop and resume at any point, and every file can be reviewed by a human before moving on.

| Stage | Skill | Output file |
|---|---|---|
| 1. Refine requirements | `aderx-pm:refine` | `docs/specs/<slug>/requirements.md` |
| 2. Technical plan | `aderx-pm:tech-plan` | `docs/specs/<slug>/tech-plan.md` |
| 3. Break down | `aderx-pm:breakdown` | `docs/specs/<slug>/breakdown.md` |
| 4. Create Linear issues | `aderx-pm:linear-issues` | `docs/specs/<slug>/linear.md` + Linear tickets |

## How to run

1. **Pick the feature slug.** A short kebab-case name (e.g. `team-invites`). If `docs/specs/` already has a folder that matches what the user is talking about, confirm it's the same feature and resume it instead of starting over.
2. **Find the entry stage.** Start at the first stage whose output file is missing. If the user brings an already-detailed spec, they can skip stage 1 — but still sanity-check it against the readiness checklist in the refine skill and only grill on the gaps.
3. **Run each stage by invoking its skill** (via the Skill tool), passing the slug and any context.
4. **Checkpoint between stages.** After each stage, give a 3–5 line summary of what was produced and the path of the file, then ask whether to continue to the next stage. The user may want to edit the file, share it, or stop here — the checkpoint is what makes this a collaboration rather than a monologue. If the user said up front "run it all", you can skip checkpoints after stages 2 and 3, but never skip the Linear preview in stage 4: creating tickets is outward-facing and other people will see them.
5. **Finish** with the list of created issues, which ones can start in parallel right now (wave 0 / unblocked), and the next command for each: `/aderx-dev:plan <ID>`.

## If the user edits a file mid-pipeline

Downstream files may now be stale. Tell the user which later files were derived from the old version and offer to regenerate them rather than silently continuing.
