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
- чи активний plugin `everything-claude-code@everything-claude-code`;
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

## 11. Cron flush на macOS не доставляє episodes

Симптом:
- `~/.claude/state/cron-flush.log` показує access errors або зовсім порожній, хоча `crontab -l` містить schedule;
- `./tools/graphiti_admin.py status <repo>` стверджує, що pending episodes не зменшуються між тиками;
- manual `./tools/graphiti_admin.py flush <repo>` з shell працює коректно.

Root cause:
- на macOS cron daemon (`/usr/sbin/cron`) за замовчуванням не має доступу до user data directories, bound-mounts і навіть до `~/.claude/state`. Без Full Disk Access (FDA) scheduled flushes тихо падають — файли hook wrapper-а або ledger просто недоступні для cron-процесу.

Fix:
1. System Settings → Privacy & Security → Full Disk Access.
2. Натисни `+` і додай `/usr/sbin/cron` (Cmd+Shift+G у Finder, введи шлях, якщо binary не видно).
3. Переконайся, що toggle поруч із `/usr/sbin/cron` увімкнений.
4. Після зміни FDA macOS перезапустить cron автоматично; додаткової reload-команди не потрібно.

Verification:
- `crontab -l` показує очікуваний schedule, що вказує на `~/.claude/hooks/graphiti-flush-cron.sh`;
- `tail -f ~/.claude/state/cron-flush.log` на наступному тіку показує успішні flush summaries (entry per run, без `Permission denied`);
- `./tools/graphiti_admin.py status <repo>` починає показувати спадний pending count і свіжий `lastFlush`.

## 12. Stop hook не запускає async flush

Симптом:
- queue / spool поступово накопичує payloads після сесій;
- очікуваний async flush після `Stop` hook не запускався (немає свіжого запису в `~/.claude/state/cron-flush.log` або в `graphiti-hooks.jsonl`);
- manual `graphiti_admin.py flush <repo>` успішно доставляє те, що встигло назбиратися.

Перевір:
1. У `.claude/graphiti.json` у секції `queue` виставлено `"asyncFlushOnStop": true`. За замовчуванням прапорець `false`, тому без явного увімкнення `Stop` hook лише enqueue-ує і повертає control — delivery лишається за cron або manual flush (див. `CONFIG-REFERENCE.md` §5.1).
2. Hook runtime встановлений. `./tools/graphiti_admin.py doctor <repo>` має пройти; `.claude/state/graphiti-runtime/` повинен існувати з робочим Python.
3. `runtime.pythonExecutable` (або `GRAPHITI_HOOK_PYTHON` env var) резолвиться у виконуваний Python, доступний із shell, що запускає Claude Code. Якщо він вказує на зламаний venv, detached subprocess exit-не миттєво і логів не лишить.
4. Sandbox / shell environment Claude Code дозволяє detached child processes. У строго sandboxed shells (наприклад, корпоративні wrapper-и, деякі IDE integrations) `subprocess.Popen(..., start_new_session=True)` тихо блокується — у такому випадку покладайся на cron wrapper `~/.claude/hooks/graphiti-flush-cron.sh` замість async-on-stop.
