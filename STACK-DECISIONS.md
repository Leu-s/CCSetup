# Stack decisions

## Kept in the baseline
- ECC
- Context7 via ECC
- GitHub MCP via ECC
- Sequential Thinking via ECC
- context-mode
- ui-ux-pro-max-skill
- Graphiti
- codebase-memory-mcp
- repomix
- ccusage

## How roles are separated
- **ECC** — the baseline Claude Code harness
- **context-mode** — reduces output bloat
- **Graphiti** — long-term memory across sessions
- **codebase-memory-mcp** — structural code intelligence
- **ui-ux-pro-max-skill** — design intelligence
- **repomix** — snapshot/export of the repo
- **ccusage** — usage/cost observability

## What we deliberately do not duplicate
- a second canonical memory engine
- a second code-graph engine in the core
- another behavior plugin on top of the rules in `CLAUDE.md`
- duplicate ECC MCP entries in the repo `.mcp.json`
- duplicate ECC hooks in the repo settings
