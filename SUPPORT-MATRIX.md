# Support matrix

## 1. Що є погодженим baseline

### Підтримуване операторське середовище
- Linux
- macOS
- WSL

Не first-class target у цьому пакеті:
- Windows-native shell без WSL


### Retained baseline
- ECC plugin layer
- ECC rules surface (upstream-owned, не дистрибується plugin-ом автоматично)
- Context7 через ECC
- GitHub MCP через ECC
- Sequential Thinking через ECC
- context-mode
- ui-ux-pro-max-skill
- repomix
- ccusage

### Repo baseline
- Graphiti
- `codebase-memory-mcp`
- repo `CLAUDE.md`
- repo `.claude/settings.json`
- repo `.mcp.json`
- Graphiti hooks, runtime, queue, ledger, admin CLI

## 2. Що автоматизує саме цей package

### Automated here
- bootstrap repo surfaces
- repo `CLAUDE.md` seed і memory ids
- Graphiti hook runtime
- project `.mcp.json` merge
- `codebase-memory-mcp` project entry
- `codebase-memory-mcp auto_index=true`
- первинний `codebase-memory-mcp index_repository`
- repo-declared plugin layer через `extraKnownMarketplaces` + `enabledPlugins`
- status / baseline-doctor / doctor / flush / requeue / migration utilities

### Installed via upstream or Claude Code itself
- actual plugin download/install for ECC, context-mode, ui-ux-pro-max-skill
- ECC rules install via upstream installer or manual rule copy
- `repomix` runtime code when invoked through `npx`
- `ccusage` runtime code when invoked through `npx`
- `codebase-memory-mcp` binary install command

## 3. Що входить у код пакета

- host-side direct ingest runtime:
  - `neo4j + openai`
  - `neo4j + openai_generic`
  - `neo4j + gemini`
  - `falkordb + openai`
  - `falkordb + openai_generic`
  - `falkordb + gemini`
- packaged MCP Docker configs:
  - `neo4j + openai`
  - `falkordb + openai`
  - `neo4j + gemini`
  - `falkordb + gemini`
- packaged localhost MCP template:
  - `graphiti-memory`
  - `codebase-memory-mcp`
- repo settings fragment:
  - Graphiti hooks
  - reproducible plugin baseline

## 4. Що verified локально пакетом

- repo bootstrap
- dedicated runtime install
- offline wheelhouse runtime path
- queue-first stop capture
- mock flush path
- session-start recall from delivered ledger
- admin wrapper path
- `codebase-memory-mcp` entry present in project `.mcp.json`
- `CLAUDE.md` seed with working principles and tool priority
- custom hook preservation
- custom MCP auth field preservation
- stale flush lock recovery
- lifecycle hook contracts for `CwdChanged`, `FileChanged`, `ConfigChange`
- repo-declared plugin layer present in `.claude/settings.json`
- `codebase-memory-mcp` auto-index bootstrap step executed by installer

## 5. Що не позначено як already-verified у будь-якому середовищі

- live Docker bring-up у конкретному середовищі, якщо Docker недоступний
- interactive Claude Code marketplace/plugin prompt flow
- interactive Claude Code project approval state
- реальний remote auth login flow до хмарного MCP
- `headersHelper` example shape для remote `.mcp.json` тепер у пакеті є, але його конкретна auth-програма лишається project/operator-owned
- live Graphiti ingest у зовнішній DB без доступного backend-а
- actual ECC rules install in this environment, unless operator ran the upstream step here

## 6. Що свідомо виключено, щоб не дублювати відповідальність

- `graphify`
- `code-review-graph`
- `andrej-karpathy-skills` як plugin
- `mcp-builder`
- `marketingskills`
- `backend-architect`
- `documentation-generator`
- `code-review`
- `connect-apps`
- `chrome-devtools-mcp`
