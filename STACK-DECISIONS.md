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
- serena
- repomix
- ccusage

## How roles are separated
- **ECC** — the baseline Claude Code harness
- **context-mode** — reduces output bloat
- **Graphiti** — long-term memory across sessions
- **codebase-memory-mcp** — relationship-graph intelligence: callers, transitive reach, data-flow, IMPORTS edges, architectural slices, change-impact
- **serena** — LSP-backed symbolic navigation and symbolic edits: file outline, symbol lookup, atomic refactors (rename, replace body, insert-before/after-symbol, safe-delete). Read-and-edit surface that `codebase-memory-mcp` does not cover
- **ui-ux-pro-max-skill** — design intelligence
- **repomix** — snapshot/export of the repo
- **ccusage** — usage/cost observability

## What we deliberately do not duplicate
- a second canonical memory engine (Graphiti is canonical; `serena`'s internal memory tools must stay disabled via `no-memories` mode)
- a second relationship-graph engine alongside `codebase-memory-mcp` — note: `serena` is LSP-symbolic, not a relationship graph, so it is NOT a duplicate
- another behavior plugin on top of the rules in `CLAUDE.md`
- duplicate ECC MCP entries in the repo `.mcp.json`
- duplicate ECC hooks in the repo settings
