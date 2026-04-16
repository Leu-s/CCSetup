# Architecture

## 1. High-level model

The framework has two clear planes.

### A. Retained Claude Code baseline
- ECC
- Context7 / GitHub MCP / Sequential Thinking via ECC
- context-mode
- ui-ux-pro-max-skill
- repomix
- ccusage

### B. Repo-owned overlay
- Graphiti
- repo hooks
- `MEMORY_GROUP_ID`
- `GRAPHITI_STORAGE_GROUP_ID`
- `codebase-memory-mcp`
- project `.mcp.json`
- repo `.claude/settings.json`
- repo `CLAUDE.md`

## 2. Split of responsibility

### ECC
The global harness, not a repo memory layer.

### context-mode
Context hygiene, not long-term memory and not a code graph.

### Graphiti
The canonical long-term memory of the project.

### codebase-memory-mcp
The structural map of the code. It does not store conversational memory and does not duplicate Graphiti.

### repo `.claude/settings.json`
The canonical repo-level surface for:
- Graphiti hooks;
- the reproducible plugin baseline (`extraKnownMarketplaces` + `enabledPlugins`).

### `CLAUDE.md`
Human-facing working rules and tool priority. The Karpathy principles live here.

## 3. Repo data flow

```text
Claude Code session
  -> repo .claude/settings.json declares plugin baseline + repo hooks
  -> repo CLAUDE.md defines working principles + ids
  -> SessionStart injects local checkpoint from delivered ledger
  -> code questions go first to codebase-memory-mcp
  -> continuity / memory questions go to Graphiti
  -> Stop / PreCompact capture a summary into local spool + ledger
  -> flush worker delivers payloads through graphiti_core
  -> Graphiti MCP exposes read/search tools to Claude
```

## 4. Why there is no second code graph or second behavior plugin

To avoid duplicating responsibility:
- one structural code layer — `codebase-memory-mcp`;
- one canonical long-term memory layer — Graphiti;
- one baseline harness — ECC;
- behavior principles — in `CLAUDE.md`, not in a separate plugin.

## 5. Boundaries — what the package intentionally does not automate

These surfaces remain external runtime boundaries of Claude Code and are not package omissions:
- interactive plugin download/install in the Claude Code UI/CLI;
- ECC `rules` install — via the upstream ECC installer or manual copy;
- `repomix` / `ccusage` download via `npx` if the local cache is still empty;
- interactive project MCP approvals;
- the remote auth login flow to external MCP endpoints.

Additionally, the following stay outside the baseline:
- a second canonical memory engine;
- a second code-graph engine on top of `codebase-memory-mcp`;
- yet another behavior plugin on top of the principles in `CLAUDE.md`;
- a broad plugin layer with an auth/perms surface without critical need.
