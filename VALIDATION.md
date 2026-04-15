# Validation

## Що фактично перевірено в цьому проході

### 1. Package validator
```bash
python3 tools/validate-package.py
```

### 2. Syntax / compile pass
```bash
python3 -m compileall templates/project/.claude/hooks tools tests
bash -n tools/install-graphiti-stack.sh
bash -n tools/install-hook-runtime.sh
bash -n tools/configure-codebase-memory.sh
bash -n tools/configure-codebase-memory.sh
bash -n templates/project/.claude/hooks/run_python.sh
```

### 3. Unit tests
Фактично прогнані:

```bash
python3 tests/test_admin_wrapper.py -v
python3 tests/test_baseline_doctor.py -v
python3 tests/test_bootstrap_hygiene.py -v
python3 tests/test_e2e_mock.py -v
python3 tests/test_group_ids.py -v
python3 tests/test_hook_contracts.py -v
python3 tests/test_install_flow_offline.py -v
```

### 4. Що підтверджують ці тести

Docs surface тепер також включає `TUTORIAL.md` як людський вхід у пакет; markdown link audit і package validator перевіряють його нарівні з рештою docs.

- bootstrap додає `codebase-memory-mcp` у project `.mcp.json`;
- bootstrap seed-ить `CLAUDE.md` із working principles і tool priority;
- bootstrap додає `extraKnownMarketplaces` + `enabledPlugins` у `.claude/settings.json`;
- custom hooks не губляться;
- custom MCP auth fields не губляться;
- stale flush lock recovery працює;
- `SessionStart`, `CwdChanged`, `FileChanged`, `ConfigChange` не зламані;
- installer викликає `codebase-memory-mcp config set auto_index true`;
- installer викликає первинний `codebase-memory-mcp cli index_repository`;
- baseline doctor підтверджує repo-declared plugin layer, repo MCP contract, local invoker availability і стан ECC rules surface.

### 5. Незалежний install/setup walkthrough
Цим пакетом підтверджено реальний offline/controlled install walkthrough:
- `install-graphiti-stack.sh`
- `graphiti_admin.py baseline-doctor`
- `graphiti_admin.py status`
- `graphiti_admin.py doctor`
- `graphiti_stop.py`
- `graphiti_flush.py`
- `session_start.py`

## Що verified локально цим пакетом
- package consistency;
- markdown link integrity;
- відсутність cache artifacts і незавершених маркерів;
- repo bootstrap;
- dedicated runtime install;
- queue-first stop capture;
- mock flush path;
- session-start recall from delivered ledger;
- `CLAUDE.md` seed;
- project `.mcp.json` merge для `graphiti-memory` і `codebase-memory-mcp`;
- repo `.claude/settings.json` plugin declarations для ECC / context-mode / ui-ux;
- `codebase-memory-mcp auto_index` + первинний index bootstrap.

## Що не видається за already-verified у кожному середовищі
- interactive Claude Code marketplace/plugin prompts;
- interactive Claude Code project approvals;
- live Docker bring-up у середовищі без Docker;
- remote auth login flow до зовнішніх MCP endpoints.

## Межа між package readiness і зовнішнім runtime

Цей пакет вважається готовим у межах свого scope, якщо:
- repo surfaces коректно seed-яться;
- Graphiti overlay працює;
- retained plugin baseline декларативно присутній у repo settings;
- codebase-memory bootstrap не має прихованого first-run кроку.

Interactive plugin download і approval state залишаються дією Claude Code client-а, а не невидимою недоробкою пакета.

## Supported operator environment used for validation

Validation surface цього пакета розрахована на Linux/macOS/WSL-style shell environment.
Windows-native shell path без WSL не позначається цим пакетом як verified target.
