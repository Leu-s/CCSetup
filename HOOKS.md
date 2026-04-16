# Hooks

Цей документ описує **лише repo-owned hooks**, які ставить цей пакет.

Важливо:
- ECC має власні plugin/global hooks;
- context-mode має власні plugin hooks;
- цей пакет додає тільки **Graphiti memory lifecycle layer** на рівні repo.

## 1. `InstructionsLoaded`
- логування lifecycle-події;
- підтримка runtime exports у консистентному стані.

## 2. `SessionStart`
- resolve logical/storage ids;
- exports у `CLAUDE_ENV_FILE`;
- local recall із delivered ledger;
- короткий checkpoint у контекст.

## 3. `CwdChanged`
- оновлює watch paths;
- синхронізує env exports.

## 4. `FileChanged`
- реагує на зміну `CLAUDE.md`, `.mcp.json`, `.claude/settings*.json`, `.claude/graphiti.json`;
- підтримує config awareness і exports.

## 5. `PreCompact`
- capture summary перед compaction;
- пише payload у spool/ledger.

## 6. `Stop`
- capture summary після завершення відповіді;
- не чекає live network ingest — pack завжди пише payload тільки у локальний spool + ledger;
- додаткова опція `queue.asyncFlushOnStop` у `.claude/graphiti.json` керує тим, чи Stop також ініціює доставку в Neo4j:
  - `false` (default) — Stop тільки spools, delivery окремо (cron / systemd / manual flush);
  - `true` — Stop додатково спавнить detached flush subprocess (через `start_new_session=True`, з `GRAPHITI_ASYNC_FLUSH=1` у env), щоб доставка жила поза critical path завершення сесії і не блокувала повернення керування користувачу.

### 6.1 `Stop` (EN)
- captures a session-end summary once the assistant turn finishes;
- never waits on live network ingest — payload is always written to the local spool + ledger first;
- the `queue.asyncFlushOnStop` flag in `.claude/graphiti.json` controls optional post-spool delivery:
  - `false` (default) — Stop only spools, delivery is handled separately (cron, systemd, or manual flush);
  - `true` — Stop additionally spawns a detached flush subprocess (via `start_new_session=True`, with `GRAPHITI_ASYNC_FLUSH=1` in the child env) so Neo4j delivery runs off the session-end critical path and does not block the user.

## 7. `ConfigChange`
- блокує небажаний drift у package-managed project config.

## 8. `PostCompact`
- capture короткий anchor одразу після того, як Claude стиснув контекст;
- пише payload у spool/ledger, так само як `PreCompact`, але ПІСЛЯ compaction;
- матчер `manual|auto` охоплює обидва типи compaction;
- мета: зберегти continuity від compact-версії transcript-а, а не тільки від pre-compact snapshot.

## 9. `PostToolUseFailure`
- capture tool-level failure як boundary-signal memory (timeout, permission denial, unreachable backend);
- stdin payload містить `tool_name` і `tool_error`;
- non-blocking; записує в queue для подальшого аналізу повторюваних frictions.

## 10. Що hooks не роблять
- не підміняють ECC hooks;
- не підміняють context-mode hooks;
- не запускають plugin installation flows;
- не копіюють ECC/plugin hooks у repo config;
- не керують глобальним Claude Code plugin state.

## 11. Де живе `codebase-memory-mcp` first-run logic

Це більше не hook concern.

`codebase-memory-mcp` first-run activation тепер іде через install flow:
- `tools/configure-codebase-memory.sh`
- `config set auto_index true`
- первинний `cli index_repository`

Тобто structural layer приводиться в готовий стан **до** першої нормальної Claude сесії, а не через repo hooks.
