# Operations

## 1. Базові перевірки

```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
./tools/graphiti_admin.py status /absolute/path/to/repo
./tools/graphiti_admin.py doctor /absolute/path/to/repo
```

## 2. Queue operations

```bash
./tools/graphiti_admin.py flush /absolute/path/to/repo --limit 20
./tools/graphiti_admin.py requeue /absolute/path/to/repo --source dead-letter --limit 20
```

## 3. Що не керується цим repo runtime

Global/plugin lifecycle для:
- ECC
- context-mode
- ui-ux-pro-max-skill

Вони керуються Claude Code plugin system або upstream installers.

## 4. Що тепер керується цим repo runtime

- Graphiti repo overlay
- queue / ledger / archive / dead-letter
- repo-declared plugin baseline
- `codebase-memory-mcp` first-run bootstrap

## 5. Scheduler boundary

`ops/systemd/*` — це Linux/WSL path. На macOS пакет не постачає `launchd` plist; використовуй manual flush або власний scheduler.
