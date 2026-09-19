---
name: react
description: React and TypeScript/JavaScript frontends (vitest or jest, Testing Library, eslint or biome, prettier; npm, pnpm, yarn or bun)
---

# Profile: React

## Detect
Applies when a `package.json` (at the root or in a sub-directory such as `frontend/`, `web/`, `client/`, `app/` or `apps/*`) lists `react` as a dependency. The area's `root` is that directory.

- **Package manager** from lockfiles: `pnpm-lock.yaml` → pnpm; `yarn.lock` → yarn; `bun.lock` or `bun.lockb` → bun; `package-lock.json` → npm.
- **Executing local tools:** `pnpm exec`, `yarn`, `bunx`, or `npx --no-install` (which refuses to download anything).
- **test:** vitest → `<exec> vitest run`; jest → `<exec> jest --ci`; otherwise the `test` script. The command must run once and exit; a watch mode would hang the workflow.
- **lint:** the `lint` script if present; otherwise `<exec> eslint .` or `<exec> biome check .` depending on what is configured.
- **typecheck:** the `typecheck` script if present; otherwise `<exec> tsc --noEmit` when a `tsconfig.json` exists. Omit for plain JavaScript projects.
- **format:** `<exec> prettier --write {file}` if prettier is configured; `<exec> biome format --write {file}` for biome. Omit if none.
- **extensions:** `[".ts", ".tsx", ".js", ".jsx"]`, plus `".css"` and `".scss"` if the formatter handles them.

## Area defaults

```json
{
  "profile": "react",
  "root": ".",
  "extensions": [".ts", ".tsx", ".js", ".jsx", ".css"],
  "test": "npx --no-install vitest run",
  "lint": "npm run lint",
  "typecheck": "npx --no-install tsc --noEmit",
  "format": "npx --no-install prettier --write {file}"
}
```

Adapt the commands to the package manager and tools detected, and drop the keys for tools the project does not use.

## Where to look
- Routing and pages: Next.js `app/` or `pages/`, React Router configuration, route loaders.
- Components (shared UI library versus feature folders), hooks, and context providers.
- State and data fetching: Redux, Zustand, React Query or SWR, and the API client layer with any generated types.
- Forms and validation schemas, i18n message files, styling (CSS modules, Tailwind, styled-components), and Storybook stories.
- Test setup files (`setupTests`, MSW handlers, custom render helpers).

## Testing conventions
- Use Testing Library: query by role, label or visible text; drive interaction with `userEvent`; avoid testing implementation details such as internal state or component structure.
- Mock the network at the boundary (MSW or the repo's existing approach), not the component's internals.
- Cover loading, error and empty states as well as the happy path.
- Keep component tests next to the component, following the repo's naming (`*.test.tsx`). Reuse the existing custom render helper and providers.
- Reserve end-to-end tests (Playwright, Cypress) for critical user flows.
- Use snapshot tests sparingly; prefer explicit assertions.

## Build notes
- Follow the rules of hooks; derive values during render instead of syncing them through state and effects.
- Give list items stable keys; avoid index keys for reorderable lists.
- Respect accessibility: labels for inputs, semantic elements, keyboard operability.
- Reuse generated or shared API types; avoid `any`. Handle the loading and error states of every async call.

## Dependency manifests
- Declared in `package.json` (`dependencies`, `devDependencies`, `peerDependencies`), one per package in a workspace or monorepo.
- Lockfiles: `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock` or `bun.lockb`.
- Add dependencies with the project's package manager so the lockfile stays in sync; keep build-time and test-only packages in `devDependencies`.

## Shortcuts to flag
`// @ts-ignore`, `// @ts-expect-error`, `eslint-disable`, `biome-ignore`, `.only(`, `.skip(`, `xit(`, `xdescribe(`, `test.todo`, new `as any` casts, leftover `console.log`, newly added `dangerouslySetInnerHTML`, and new `TODO` or `FIXME`.

## Review checklist
- Hook dependency arrays that are wrong or suppressed; stale closures; effects that should be derived state or event handlers.
- Missing or unstable `key` props; unnecessary re-renders on hot paths (new objects or functions created in render and passed to memoized children).
- Missing loading, error and empty states; unhandled promise rejections.
- `any` casts and non-null assertions hiding real type errors; API types drifting from the backend contract.
- XSS vectors: `dangerouslySetInnerHTML`, unsanitized URLs in `href` or `src`, secrets or tokens exposed in client bundles or local storage.
- Accessibility: unlabeled controls, click handlers on non-interactive elements, focus management in dialogs.
- Tests that query by implementation details (test ids, class names) instead of role or text, or that never fail.
- Bundle impact of new heavy dependencies; work done on every render that could be memoized or moved out.
