# Config reference

## 1. Repo `.claude/settings.json`

After bootstrap this file contains three kinds of data:
1. Graphiti hooks;
2. `autoMemoryEnabled: false`;
3. reproducible plugin baseline.

### 1.1 Plugin baseline

```json
{
  "extraKnownMarketplaces": {
    "everything-claude-code": {
      "source": { "source": "github", "repo": "affaan-m/everything-claude-code" }
    },
    "context-mode": {
      "source": { "source": "github", "repo": "mksglu/context-mode" }
    },
    "ui-ux-pro-max-skill": {
      "source": { "source": "github", "repo": "nextlevelbuilder/ui-ux-pro-max-skill" }
    }
  },
  "enabledPlugins": {
    "everything-claude-code@everything-claude-code": true,
    "context-mode@context-mode": true,
    "ui-ux-pro-max@ui-ux-pro-max-skill": true
  }
}
```

Semantics:
- repo settings are now the canonical reproducibility layer for the **plugin portion** of the retained baseline;
- user settings may remain for personal overrides, but must not be the only place the plugin baseline lives;
- plugins still require the Claude Code client trust / install flow;
- ECC `rules`, `repomix`, and `ccusage` are not installed automatically by this JSON.

### 1.2 Graphiti hook events

- `InstructionsLoaded`
- `SessionStart`
- `CwdChanged`
- `FileChanged`
- `PreCompact`
- `Stop`
- `ConfigChange`

## 2. Repo `.mcp.json`

After bootstrap, `.mcp.json` contains:

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "type": "http",
      "url": "${GRAPHITI_MCP_ENDPOINT:-http://127.0.0.1:8000/mcp/}"
    },
    "codebase-memory-mcp": {
      "command": "${CODEBASE_MEMORY_MCP_BIN:-codebase-memory-mcp}",
      "args": []
    }
  }
}
```

Rules:
- do not add `context7`, `github`, or `sequential-thinking` here if they already arrive via ECC;
- `codebase-memory-mcp` is added as a project-scoped structural backend;
- Graphiti MCP may use `headers` / `headersHelper` for remote auth, and bootstrap must not overwrite them.

## 2.1 Important ECC boundary

The ECC plugin layer and the ECC rules surface are different things.
Plugin settings in `.claude/settings.json` do not distribute `rules` automatically. If you want the full ECC rules surface, install it via the upstream ECC installer or copy `rules/common` plus the needed language directories separately.

## 3. Repo `CLAUDE.md`

The template contains:
- working principles;
- tool priority;
- `MEMORY_GROUP_ID`;
- `GRAPHITI_STORAGE_GROUP_ID`;
- Graphiti memory contract.

## 4. `codebase-memory-mcp` bootstrap policy

The package expects a manual binary install, but first-run activation is now automated:
- `tools/configure-codebase-memory.sh`
- `codebase-memory-mcp config set auto_index true`
- `codebase-memory-mcp cli index_repository '{"repo_path":"..."}'`

### Override

To skip the initial index during the install flow:
```bash
export CODEBASE_MEMORY_MCP_SKIP_INITIAL_INDEX=1
```

## 5. Graphiti runtime config

Primary config: `templates/project/.claude/graphiti.json`

Key sections:
- `engine.backend`: `neo4j` or `falkordb`
- `engine.provider`: `openai`, `openai_generic`, `gemini`
- `mcp.endpoint`
- `mcp.healthUrl`
- `groupIds.*`
- `queue.*`
- `runtime.*`

### 5.1 `queue.*` recognized fields

Paths, if not absolute, are resolved relative to repo root.

- `queue.ledgerPath` (string) — SQLite ledger that tracks pending / delivered / dead-letter episodes.
- `queue.spoolDir` (string) — directory for pending JSON payloads awaiting delivery.
- `queue.archiveDir` (string) — successfully delivered payloads are moved here.
- `queue.deadLetterDir` (string) — payloads that exhausted `maxAttempts` land here.
- `queue.logsDir` (string) — directory for JSONL hook/flush logs.
- `queue.locksDir` (string) — file locks (for example, `graphiti-flush.lock`).
- `queue.lastFlushPath` (string) — JSON snapshot of the last flush run (used by `status` / `doctor`).
- `queue.engineStatePath` (string) — per-engine runtime state snapshot for delivery.
- `queue.bootstrapReceiptsDir` (string) — receipts from `graphiti_bootstrap.py` runs.
- `queue.bootstrapBackupsDir` (string) — backups of files modified by bootstrap.
- `queue.maxAttempts` (int, default `6`) — how many times `graphiti_flush.py` tries to deliver a single payload before it becomes a dead-letter.
- `queue.baseRetrySeconds` (int, default `30`) — base backoff between retries.
- `queue.maxRetrySeconds` (int, default `3600`) — cap for exponential backoff.
- `queue.flushLockMaxAgeSeconds` (int, default `900`) — after this TTL a stale flush lock is considered leftover and is cleared automatically.
- `queue.asyncFlushOnStop` (bool, default `false`) — when `true`, the `Stop` hook (`graphiti_stop.py`) spawns a detached flush subprocess after enqueue so delivery does not block session end. When `false`, delivery is handled exclusively by the cron wrapper or manual `graphiti_admin.py flush`.

## 6. Important invariants

- `Graphiti` is the canonical long-term memory.
- `codebase-memory-mcp` is the canonical structural code layer.
- `autoMemoryEnabled` in project settings must be `false`.
- repo settings must not duplicate ECC plugin hooks.
- The `memory` MCP from the `everything-claude-code` bundle must not be enabled alongside Graphiti. Graphiti is this package's canonical long-term memory layer; enabling the bundled `memory` MCP creates split-state and conflicting recall across sessions.
