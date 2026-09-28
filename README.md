# GoGoAderx

A Claude Code plugin marketplace (`gogoaderx`) with two plugins that cover the path from idea to merged code:

| Plugin | What it does | Start with |
|---|---|---|
| [aderx-pm](plugins/aderx-pm/) | Idea → requirements → technical plan → parallelizable issues → Linear tickets | `/aderx-pm:pm` |
| [aderx-dev](plugins/aderx-dev/) | Linear ticket → approved spec → implementation checked by an independent verifier → PR → handle review comments | `/aderx-dev:init`, then `/aderx-dev:plan <TICKET>` |

My own agentic workflow, tuned to how I work rather than for general use. The plugins connect through Linear: each ticket `aderx-pm` files links back to its tech plan, and `aderx-dev:plan` picks it up from there.

## Case studies

Both plugins used end to end on a real project (Constella):
- [aderx-pm](docs/aderx-pm-case-study.md): an idea to 11 Linear tickets in 4 dependency waves.
- [aderx-dev](docs/aderx-dev-case-study.md): review triage, then a ticket taken to an approved PR with an independent verifier.

## Install

```
/plugin marketplace add super-aderx/GoGoAderx
/plugin install aderx-pm@gogoaderx
/plugin install aderx-dev@gogoaderx
```

For a local checkout, use `/plugin marketplace add /path/to/GoGoAderx`, or `claude --plugin-dir plugins/<name>` for one session. Linear is not bundled: connect it yourself and sign in through `/mcp`.

## Layout

```
.claude-plugin/marketplace.json   marketplace catalog listing both plugins
plugins/aderx-pm/                 product-management plugin
plugins/aderx-dev/                development plugin
docs/                             case studies
```

## Development

Each plugin has its own tests, run from that plugin's folder:

```bash
(cd plugins/aderx-pm && python3 -m pytest tests/)
(cd plugins/aderx-dev && python3 -m pytest tests/)
```

Validate the manifests with `claude plugin validate --strict .` (marketplace) and `claude plugin validate --strict plugins/<name>`.
