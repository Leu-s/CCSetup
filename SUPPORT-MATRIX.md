# Support matrix

## 1. The agreed baseline

### Supported operator environment
- Linux
- macOS
- WSL

Not a first-class target in this package:
- Windows-native shell without WSL


### Retained baseline
- ECC plugin layer
- ECC rules surface (upstream-owned, not distributed by the plugin automatically)
- Context7 via ECC
- GitHub MCP via ECC
- Sequential Thinking via ECC
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

## 2. What this package itself automates

### Automated here
- bootstrap repo surfaces
- repo `CLAUDE.md` seed and memory ids
- Graphiti hook runtime
- project `.mcp.json` merge
- `codebase-memory-mcp` project entry
- `codebase-memory-mcp auto_index=true`
- initial `codebase-memory-mcp index_repository`
- repo-declared plugin layer via `extraKnownMarketplaces` + `enabledPlugins`
- status / baseline-doctor / doctor / flush / requeue / migration utilities

### Installed via upstream or Claude Code itself
- actual plugin download/install for ECC, context-mode, ui-ux-pro-max-skill
- ECC rules install via upstream installer or manual rule copy
- `repomix` runtime code when invoked through `npx`
- `ccusage` runtime code when invoked through `npx`
- `codebase-memory-mcp` binary install command

## 3. What ships in the package code

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

## 4. What the package verifies locally

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

## 5. What is not marked as already-verified in every environment

- live Docker bring-up in a specific environment when Docker is not available
- interactive Claude Code marketplace/plugin prompt flow
- interactive Claude Code project approval state
- actual remote auth login flow to a cloud MCP
- a `headersHelper` example shape for remote `.mcp.json` is now shipped, but its concrete auth program remains project/operator-owned
- live Graphiti ingest into an external DB without a reachable backend
- actual ECC rules install in this environment, unless operator ran the upstream step here

## 6. What is deliberately excluded to avoid duplicating responsibility

- `graphify`
- `code-review-graph`
- `andrej-karpathy-skills` as a plugin
- `mcp-builder`
- `marketingskills`
- `backend-architect`
- `documentation-generator`
- `code-review`
- `connect-apps`
- `chrome-devtools-mcp`
