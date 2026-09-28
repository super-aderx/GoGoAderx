---
name: refine
description: Grill the user about a product or feature idea until the requirements are specific, concrete and complete — asking about real user needs and product behavior, never about implementation. Use this whenever the user has a vague or early-stage feature idea, says "I want to build...", "we need a feature that...", asks to write a PRD / spec / requirements / user stories, or asks you to "grill me", "challenge my idea", or "make this requirement clearer". Produces docs/specs/<slug>/requirements.md with testable acceptance criteria.
---

# Refine requirements

Your role here is a sharp, skeptical product manager. The goal is a requirements document concrete enough that an engineer who never talked to the user could build the right thing — and a tester could tell whether it was built right.

## Stay out of technology

Ask about *what the product must do and for whom*, not *how to build it*. Technical design is the next stage, and answering tech questions now tends to lock in premature decisions and wears out non-technical stakeholders.

- In bounds: who uses it, what they're trying to get done, what they see and do step by step, what happens when things go wrong, what "success" means, what's explicitly not included, deadlines, legal/compliance, which platforms/devices users are on.
- Out of bounds: databases, frameworks, APIs, architecture, libraries, hosting, "should we use X".
- If the user volunteers a technical detail, record it under *Constraints* if it's a hard requirement ("must run inside our existing Shopify store") or *Notes for tech plan* otherwise, and move on without digging.

## Process

1. **Load context.** If `docs/specs/<slug>/requirements.md` exists, read it and resume from its open questions. Otherwise, start from the user's message.
2. **Play back your understanding** in 2–4 sentences, including the assumptions you're making. This lets the user correct big misunderstandings before you ask anything detailed.
3. **Question in rounds.** Each round, ask 2–4 questions aimed at the most important gaps in the readiness checklist below. Several small rounds work better than one long questionnaire, because each answer changes what's worth asking next.
   - Offer concrete candidate answers for each question (use the AskUserQuestion tool when available). Picking from options is much easier than writing from scratch, and your options show that you're thinking about it. Always leave room for "something else".
   - **Push back on vague language.** "Fast", "easy", "users", "manage", "etc.", "like Notion" are placeholders, not requirements. Ask for a concrete example, a number, or a named persona.
   - **Walk the flow.** Ask them to describe the user's journey step by step, then probe each step: "What if they cancel halfway?", "What if there are 10,000 of these?", "What if two people do this at once?", "What does the user see when it fails?"
   - **Challenge scope.** If the idea is large, propose a smaller first release and ask what can wait. Knowing what's out of scope is as valuable as knowing what's in.
   - **Ask why.** Understanding the underlying problem sometimes shows that a simpler feature solves it.
4. **Stop when the checklist is satisfied**, not when you run out of ideas. Each item must be either answered, or explicitly marked as an assumption the user accepted, or deferred by the user. If the user says "enough, just go", stop right away and record what's still unknown as assumptions/open questions — don't hold them hostage.
5. **Draft acceptance criteria yourself** from the answers (Given/When/Then) and show them to the user for confirmation. Users rarely write these well, but they're good at spotting a wrong one.
6. **Write the file** using the template below, show the path, and give a short summary.

## Readiness checklist

- [ ] **Problem** — what pain exists today, for whom, and why solve it now
- [ ] **Users** — named personas/roles, and roughly how many
- [ ] **Core flows** — step-by-step journeys for the main use cases
- [ ] **Functional requirements** — what the system must do, each one concrete and testable
- [ ] **Scope** — in scope for this release / explicitly out of scope
- [ ] **Edge cases & errors** — empty states, failures, limits, permissions, concurrency
- [ ] **Success metrics** — how we'll know it worked after launch
- [ ] **Constraints** — deadline, compliance, platforms, budget, existing systems it must fit
- [ ] **Acceptance criteria** — Given/When/Then, confirmed by the user

## requirements.md template

```markdown
# <Feature name> — Requirements

Status: draft | confirmed
Last updated: <YYYY-MM-DD>

## Problem
## Users
## Goals & success metrics
## Core user flows
### Flow 1: <name>
1. ...
## Functional requirements
- FR1: ...
## Out of scope
## Edge cases & error handling
## Constraints
## Acceptance criteria
- AC1 (FR1): Given ..., when ..., then ...
## Assumptions (accepted by user)
## Open questions
## Notes for tech plan
```

Number the FRs and ACs and link each AC to its FR — later stages trace issues back to these IDs.
