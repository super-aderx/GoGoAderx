# GoGoAderx

A Claude Code plugin marketplace (`gogoaderx`) with two plugins that cover the path from idea to merged code:

| Plugin | What it does | Start with |
|---|---|---|
| [aderx-pm](plugins/aderx-pm/) | Idea → requirements → technical plan → parallelizable issues → Linear tickets | `/aderx-pm:pm` |
| [aderx-dev](plugins/aderx-dev/) | Linear ticket → approved spec → implementation checked by an independent verifier → PR → review | `/aderx-dev:init`, then `/aderx-dev:plan <TICKET>` |

They connect through Linear: the tickets that `aderx-pm` files are what `aderx-dev:plan` picks up. Each plugin also works on its own.

## Install

```
/plugin marketplace add super-aderx/GoGoAderx
/plugin install aderx-pm@gogoaderx
/plugin install aderx-dev@gogoaderx
```

For a local checkout, use `/plugin marketplace add /path/to/GoGoAderx` instead, or load one plugin for a single session with `claude --plugin-dir plugins/<name>`.

Neither plugin ships a Linear connection: connect Linear to Claude Code yourself, for example with the claude.ai Linear connector or `claude mcp add --transport http linear https://mcp.linear.app/mcp`, then sign in through `/mcp`. Both plugins use whichever Linear tools are available.

## Layout

```
.claude-plugin/marketplace.json   marketplace catalog listing both plugins
plugins/aderx-pm/                 product-management plugin
plugins/aderx-dev/                development plugin
```

## Development

Each plugin has its own tests, run from that plugin's folder:

```bash
(cd plugins/aderx-pm && python3 -m pytest tests/)
(cd plugins/aderx-dev && python3 -m pytest tests/)
```

Validate the manifests with `claude plugin validate --strict .` (marketplace) and `claude plugin validate --strict plugins/<name>`.
