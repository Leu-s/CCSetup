# Stack decisions

## Залишили в baseline
- ECC
- Context7 через ECC
- GitHub MCP через ECC
- Sequential Thinking через ECC
- context-mode
- ui-ux-pro-max-skill
- Graphiti
- codebase-memory-mcp
- repomix
- ccusage

## Як розведені ролі
- **ECC** — базовий Claude Code harness
- **context-mode** — зменшення output bloat
- **Graphiti** — довга пам’ять між сесіями
- **codebase-memory-mcp** — structural code intelligence
- **ui-ux-pro-max-skill** — design intelligence
- **repomix** — snapshot/export repo
- **ccusage** — usage/cost observability

## Що принципово не дублюємо
- другий canonical memory engine
- другий code-graph engine в core
- другий behavior plugin поверх правил у `CLAUDE.md`
- дубль ECC MCP entries у repo `.mcp.json`
- дубль ECC hooks у repo settings
