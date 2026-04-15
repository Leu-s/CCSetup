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
- не чекає live network ingest.

## 7. `ConfigChange`
- блокує небажаний drift у package-managed project config.

## 8. Що hooks не роблять
- не підміняють ECC hooks;
- не підміняють context-mode hooks;
- не запускають plugin installation flows;
- не копіюють ECC/plugin hooks у repo config;
- не керують глобальним Claude Code plugin state.

## 9. Де живе `codebase-memory-mcp` first-run logic

Це більше не hook concern.

`codebase-memory-mcp` first-run activation тепер іде через install flow:
- `tools/configure-codebase-memory.sh`
- `config set auto_index true`
- первинний `cli index_repository`

Тобто structural layer приводиться в готовий стан **до** першої нормальної Claude сесії, а не через repo hooks.
