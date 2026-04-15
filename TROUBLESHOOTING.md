# Troubleshooting

## 1. `baseline-doctor` каже, що repo plugin baseline не оголошений

Перевір:
- чи bootstrap реально створив `.claude/settings.json`;
- чи файл містить `extraKnownMarketplaces` і `enabledPlugins`;
- чи repo не було перезаписано старим ручним config copy.

## 2. `baseline-doctor` каже, що `.mcp.json` дублює ECC MCP-и

Прибери з repo `.mcp.json`:
- `context7`
- `github`
- `sequential-thinking`

Вони мають приходити через ECC.

## 3. `doctor` каже, що `codebase-memory-mcp` відсутній або не резолвиться

Перевір:
- чи binary встановлено;
- чи `.mcp.json` містить `codebase-memory-mcp`;
- чи задано `CODEBASE_MEMORY_MCP_BIN`, якщо binary не в PATH.

## 4. `codebase-memory-mcp` не готовий на першій сесії

Перевір, чи install flow пройшов до кінця.

Пакет повинен був виконати:
```bash
codebase-memory-mcp config set auto_index true
codebase-memory-mcp cli index_repository '{"repo_path":"/absolute/path/to/repo"}'
```

За потреби повтори вручну:
```bash
./tools/configure-codebase-memory.sh /absolute/path/to/repo
```

## 5. Context7 / GitHub MCP / Sequential Thinking не видно

Перевір:
- чи встановлений ECC;
- чи активний plugin `ecc@ecc`;
- чи repo trusted і Claude Code підхопив repo-declared plugins;
- чи не вимкнув ти ECC у user settings або managed settings.

## 6. Context-mode не працює

У Claude Code:
```text
/context-mode:ctx-doctor
```

Також перевір:
- чи `context-mode@context-mode` enabled;
- чи після інсталяції був `/reload-plugins`.

## 7. UI/UX skill не з’являється

Перевір:
- чи `ui-ux-pro-max@ui-ux-pro-max-skill` enabled;
- чи після інсталяції був `/reload-plugins`.

## 8. Є duplicate hooks або дивні подвійні спрацювання

Не копіюй ECC plugin hooks вручну в repo `settings.json`.

Repo hooks цього пакета повинні покривати тільки Graphiti lifecycle.

## 9. `doctor` каже, що Graphiti health ок, але ingest не ready

Це нормально можливо, бо:
- MCP HTTP health і direct ingest — різні шари;
- Graphiti HTTP server може бути reachable, а host runtime/env ще не готові.


## 10. Потрібен remote MCP із short-lived auth

Використай `.mcp.json` з `headersHelper` замість hardcoded bearer header.
Готовий shape є в `ops/examples/mcp.graphiti.remote-headers-helper.example.json`.
