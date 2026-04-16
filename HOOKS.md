# Hooks

This document describes **only the repo-owned hooks** installed by this package.

Important:
- ECC has its own plugin/global hooks;
- context-mode has its own plugin hooks;
- this package only adds the **Graphiti memory lifecycle layer** at the repo level.

## 1. `InstructionsLoaded`
- logs the lifecycle event;
- keeps runtime exports in a consistent state.

## 2. `SessionStart`
- resolves logical/storage ids;
- exports to `CLAUDE_ENV_FILE`;
- local recall from the delivered ledger;
- brief checkpoint into context.

## 3. `CwdChanged`
- updates watch paths;
- synchronizes env exports.

## 4. `FileChanged`
- reacts to changes in `CLAUDE.md`, `.mcp.json`, `.claude/settings*.json`, `.claude/graphiti.json`;
- maintains config awareness and exports.

## 5. `PreCompact`
- captures a summary before compaction;
- writes the payload to spool/ledger.

## 6. `Stop`
- captures a summary after the response finishes;
- does not wait on live network ingest — the pack always writes the payload only to the local spool + ledger;
- the additional `queue.asyncFlushOnStop` option in `.claude/graphiti.json` controls whether Stop also initiates delivery to Neo4j:
  - `false` (default) — Stop only spools, delivery happens separately (cron / systemd / manual flush);
  - `true` — Stop additionally spawns a detached flush subprocess (via `start_new_session=True`, with `GRAPHITI_ASYNC_FLUSH=1` in env) so delivery lives off the session-end critical path and does not block handing control back to the user.

### 6.1 `Stop` (EN)
- captures a session-end summary once the assistant turn finishes;
- never waits on live network ingest — payload is always written to the local spool + ledger first;
- the `queue.asyncFlushOnStop` flag in `.claude/graphiti.json` controls optional post-spool delivery:
  - `false` (default) — Stop only spools, delivery is handled separately (cron, systemd, or manual flush);
  - `true` — Stop additionally spawns a detached flush subprocess (via `start_new_session=True`, with `GRAPHITI_ASYNC_FLUSH=1` in the child env) so Neo4j delivery runs off the session-end critical path and does not block the user.

## 7. `ConfigChange`
- blocks unwanted drift in package-managed project config.

## 8. `PostCompact`
- captures a brief anchor immediately after Claude has compacted context;
- writes the payload to spool/ledger the same way `PreCompact` does, but AFTER compaction;
- the `manual|auto` matcher covers both compaction types;
- goal: preserve continuity from the compacted version of the transcript, not only from the pre-compact snapshot.

## 9. `PostToolUseFailure`
- captures tool-level failure as boundary-signal memory (timeout, permission denial, unreachable backend);
- the stdin payload contains `tool_name` and `tool_error`;
- non-blocking; enqueues for later analysis of recurring frictions.

## 10. What hooks do not do
- do not replace ECC hooks;
- do not replace context-mode hooks;
- do not run plugin installation flows;
- do not copy ECC/plugin hooks into repo config;
- do not manage global Claude Code plugin state.

## 11. Where `codebase-memory-mcp` first-run logic lives

This is no longer a hook concern.

`codebase-memory-mcp` first-run activation now goes through the install flow:
- `tools/configure-codebase-memory.sh`
- `config set auto_index true`
- initial `cli index_repository`

In other words, the structural layer is brought to a ready state **before** the first normal Claude session, not via repo hooks.
