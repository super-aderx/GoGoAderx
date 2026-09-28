---
name: tech-plan
description: Turn confirmed business requirements into a concrete technical plan grounded in the actual codebase — architecture, components, data model, interfaces, key flows, risks and testing strategy. Use this whenever the user has requirements, a PRD or a spec (e.g. docs/specs/<slug>/requirements.md) and asks "how should we build this", "design the solution", "technical design", "architecture for this feature", or "turn this into a tech plan". Produces docs/specs/<slug>/tech-plan.md.
---

# Technical plan

Translate *what* the product must do (requirements.md) into *how* it'll be built. A good plan fits the existing codebase, traces every requirement to a design element, and puts real decisions in front of the user instead of burying them.

## 1. Load requirements

Read `docs/specs/<slug>/requirements.md`. If it's missing, or clearly too thin to design against (no flows, no acceptance criteria), say so and offer to run `aderx-pm:refine` first. If the user wants to push on anyway, list the gaps as assumptions in the plan.

## 2. Explore the codebase first

Design in a vacuum produces plans that fight the codebase. Before designing, learn:

- Stack, frameworks, and how the project is structured
- Existing modules the feature will touch or reuse (search for related concepts by name)
- Similar features already built — copy their patterns
- Conventions: data access, API style, error handling, auth, state management, tests
- How tests are run and where they live

For a large repo, delegate the sweep to an Explore subagent and ask for concrete file paths. If there is no codebase (greenfield), say so and propose a stack with brief justification — that's itself a decision for the user (see step 3).

## 3. Surface decisions, don't bury them

When there's a real fork with tradeoffs (e.g. polling vs websockets, new service vs extending an existing one, build vs buy), present 2–3 options with pros/cons and your recommendation, and let the user choose. Batch these into one or two rounds of questions rather than asking one at a time. Don't ask about choices where the codebase already has a clear convention — just follow it and note that you did.

## 4. Write tech-plan.md

```markdown
# <Feature name> — Technical Plan

Requirements: ./requirements.md
Last updated: <YYYY-MM-DD>

## Summary
<one paragraph: the approach in plain words>

## Codebase context
<relevant existing modules, patterns being reused, with file paths>

## Components
<!-- A mermaid diagram above the list if the interactions aren't obvious. -->
### <Component>
- Responsibility:
- Location: <new/modified paths>
- Requirements covered: FR1, FR3

## Data model
<new/changed tables, fields, migrations>

## Interfaces & contracts
<API endpoints, events, shared types, function signatures — precise enough that two people could implement both sides independently>

## Decisions
- D1: <decision> — chosen because <reason>; alternatives: <...>

## Risks, rollout & open questions
<security/privacy/performance concerns, feature flags, backfills, backwards compatibility, anything unresolved>
```

The **Interfaces & contracts** section matters most for the next stage: parallel issues can only proceed independently if the contracts between them are pinned down here. Be specific — types, field names, endpoints, status codes.

Every FR in requirements.md should appear under some component's **Requirements covered**. If one doesn't fit the design, that's a sign either the design or the requirement needs revisiting — flag it.
