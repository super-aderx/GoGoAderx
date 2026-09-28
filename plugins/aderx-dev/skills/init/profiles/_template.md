---
name: my-stack
description: One line saying which kind of code this profile covers, e.g. "Go services (go test, golangci-lint)".
---

<!--
HOW TO USE THIS TEMPLATE
A profile is plain markdown that teaches aderx-dev the conventions of one language or stack.
Copy this file to .aderx-dev/profiles/<name>.md, fill it in, and list <name> under "profiles"
in .aderx-dev/config.json. Keep every section heading exactly as written: skills and
subagents look them up by name. Delete the guidance comments when you are done.
Write only what is true for THIS repo. An empty or "n/a" section is better than a guess.
-->

# Profile: <name>

## Detect
<!-- Used by /aderx-dev:init. Which files or dependencies show this stack is present, and how to
derive the commands: runner or wrapper prefixes, how to tell test/lint/typecheck/format tools apart. -->

## Area defaults
<!-- Seed for an entry under "areas" in config.json. Commands run from "root". Use `{file}` in
"format" (the format hook runs it on one edited file). Test commands must run once and exit. -->

```json
{
  "profile": "<name>",
  "root": ".",
  "extensions": [".ext"],
  "test": "",
  "lint": "",
  "typecheck": "",
  "format": "<formatter> {file}"
}
```

## Where to look
<!-- For the explorer subagent while planning: entry points, layers, config, migrations, wiring,
and where the closest existing features usually live. -->

## Testing conventions
<!-- For the test plan and the build step: test framework, file placement and naming, fixtures and
mocking style, what to mock and what not to, how async/concurrency is tested. -->

## Build notes
<!-- Idioms and pitfalls specific to this stack that a builder should respect. -->

## Dependency manifests
<!-- Which files declare dependencies and which are lockfiles, how runtime and dev-only dependencies
are separated, and the command that adds a dependency correctly. The verifier diffs these files
against the spec's Dependencies section. -->

## Shortcuts to flag
<!-- Patterns the verifier greps for in the diff: ways of silencing checks or skipping tests, debug
leftovers. List concrete tokens, e.g. `skip(`, `@Ignore`, `// nolint`. -->

## Review checklist
<!-- For the reviewer subagent: stack-specific bugs, security issues, performance traps and
maintainability problems worth checking in a diff. -->
