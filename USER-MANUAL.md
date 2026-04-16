# User manual

## 0. Як користуватися цим фреймворком як людині

Найчастіший режим такий:
- ти даєш Claude Code repo і цей пакет;
- Claude Code читає docs і робить install/bootstrap;
- далі ти ставиш задачі, а Claude Code користується agreed baseline автоматично.

Тобто цей manual не для того, щоб ти щодня вручну запускав усі інструменти.
Він потрібний, щоб ти розумів, **що робить система, що робить Claude Code і що маєш робити ти сам**.

Початковий маршрут для людини:
1. [TUTORIAL.md](TUTORIAL.md)
2. [QUICKSTART.md](QUICKSTART.md)
3. [INSTALL.md](INSTALL.md)
4. далі вже цей manual

## 1. Ментальна модель всього стеку

Система має чіткі ролі.

### Retained Claude Code layer
- **`everything-claude-code@everything-claude-code` (ECC bundle)** — базовий harness: skills, agents, hooks і bundled MCP surface.
- **ECC rules surface** — окремий upstream-owned шар; plugin install не розносить його автоматично.
- **Context7 / GitHub MCP / Sequential Thinking** — приходять через ECC bundle.
- **context-mode** — зменшує шум від великих tool outputs у контексті.
- **ui-ux-pro-max-skill** — design intelligence для UI/UX задач.
- **repomix** — operator-local CLI для AI-friendly snapshot усього repo.
- **ccusage** — operator-local CLI для usage/cost по Claude Code логах.

### Repo layer
- **Graphiti** — канонічна довга пам’ять проекту.
- **codebase-memory-mcp** — structural memory коду.
- **repo hooks** — автоматичний capture і delivery memory summaries.
- **`CLAUDE.md`** — working principles, tool priority і project identity.
- **repo `.claude/settings.json`** — hooks плюс reproducible plugin baseline.

## 2. Tool order

1. **`codebase-memory-mcp`** — structural questions про код.
2. **Graphiti** — continuity, decisions, constraints, unresolved risks.
3. **Context7** — current library/framework docs.
4. **GitHub MCP** — issues, PRs, branches, repo actions.
5. **raw file reads** — тільки після звуження пошуку.

## 3. Як працює automatic memory у repo

### На старті сесії
`SessionStart`:
- визначає logical/storage ids;
- export-ить env для решти сесії;
- читає локальний delivered ledger;
- друкує короткий checkpoint у контекст.

### Під час сесії
`InstructionsLoaded`, `CwdChanged` і `FileChanged`:
- тримають runtime exports в актуальному стані;
- оновлюють `watchPaths`;
- логують lifecycle події.

### Перед compaction і в кінці відповіді
`PreCompact` і `Stop`:
- збирають короткий summary з сесії;
- пишуть payload у spool і ledger;
- не чекають live network write.

### Поза Claude-відповіддю
`graphiti_flush.py`:
- читає due payloads зі spool;
- доставляє їх через `graphiti_core`;
- переносить успіх у archive;
- робить retry або dead-letter при збоях.

## 4. Як працює plugin baseline тепер

Retained plugin baseline більше не живе лише в user scope.

Після bootstrap repo `.claude/settings.json` уже декларує:
- marketplace source для `everything-claude-code@everything-claude-code` (ECC bundle), `context-mode@context-mode` і `ui-ux-pro-max@ui-ux-pro-max-skill`;
- `enabledPlugins` для цих трьох plugin-ів.

Наслідок:
- fresh clone отримує той самий **plugin contract**;
- cloud session може відтворити **plugin portion** baseline з repo;
- user preinstall лишається зручністю, а не єдиним способом налаштування.

Важлива межа:
- `repomix` і `ccusage` не ставляться через repo settings;
- ECC `rules` теж не розносяться plugin layer автоматично.

## 5. `codebase-memory-mcp`: що тепер автоматизовано

Раніше слабке місце було в тому, що після manual binary install треба було ще не забути:
- restart agent;
- сказати “Index this project”;
- або ввімкнути `auto_index`.

У цьому пакеті install flow тепер робить дві речі сам:
- `codebase-memory-mcp config set auto_index true`
- `codebase-memory-mcp cli index_repository '{"repo_path":"..."}'`

Тобто на момент першого відкриття repo в Claude Code structural layer уже не лишається “напівактивованим”.

## 6. Коли покладатися на automatic memory, а коли на MCP tools

### Покладайся на automatic memory коли
- треба, щоб важливі рішення не губилися між сесіями;
- хочеш мати короткий local checkpoint на старті;
- тобі достатньо summary-level continuity.

### Використовуй Graphiti MCP tools коли
- треба знайти конкретні facts або entities;
- треба дістати older history з remote graph;
- працюєш на новій машині і local ledger ще порожній.

### Використовуй `codebase-memory-mcp` коли
- треба знайти точку входу в незнайомий repo;
- треба зрозуміти, хто що викликає;
- треба оцінити impact до зміни коду;
- треба зменшити кількість raw file reads.

## 7. Як взаємодіють ECC hooks, context-mode і repo Graphiti hooks

Вони не повинні підміняти один одного.

- ECC дає свій global harness і global hooks.
- context-mode дає routing/sandbox hooks через plugin.
- repo `.claude/settings.json` із цього пакета додає Graphiti lifecycle hooks.

Важливе правило:
- **не копіюй ECC plugin hooks вручну в repo `settings.json`**;
- **не намагайся перенести context-mode hook config у repo hooks цього пакета**.

Repo hooks цього пакета — **додатковий project layer**, а не заміна ECC або context-mode.

## 8. Fresh machine / fresh clone semantics

`SessionStart` **не** робить remote search у Graphiti. Він читає тільки локальний delivered ledger у `.claude/state/graphiti-ledger.sqlite3`.

Наслідок:
- на новій машині memory checkpoint на старті може бути порожнім;
- це не означає, що remote Graphiti порожній;
- якщо треба відразу витягнути shared history, використай Graphiti MCP search tools вручну.

Plugin baseline при цьому поводиться інакше:
- якщо repo trusted і доступ до marketplace є, Claude Code може поставити repo-declared plugins на старті сесії;
- якщо plugin already preinstalled locally, prompts або не з’являться, або будуть мінімальні.

## 9. Best practices

1. **Одна канонічна long-term memory:** Graphiti.
2. **Не дублюй ECC MCP-и в repo `.mcp.json`:** Context7, GitHub MCP і Sequential Thinking already covered globally.
3. **Не дублюй ECC hooks у repo settings.**
4. **Для code questions спершу structural tools, потім files.**
5. **Не міняй `GRAPHITI_STORAGE_GROUP_ID` вручну без потреби.** Працюй через `MEMORY_GROUP_ID` і admin migration commands.
6. **Тримай секрети в env, а не в git.**
7. **Не плутай MCP health із ingest health.** Graphiti HTTP path і host-side direct ingest — різні перевірки.

## 9a. Excluded surfaces

Do not use the `memory` MCP shipped by the `everything-claude-code` bundle. Graphiti is the canonical long-term memory layer for this framework. Writing to two memory backends produces split state and conflicts with the queue/ledger/archive contract.

Практично це означає:
- не додавай bundled `memory` MCP у repo `.mcp.json`;
- не викликай його tools паралельно з Graphiti в одній сесії;
- якщо ECC bundle все одно його експонує, покладайся на `graphiti-memory` як єдиний write path.

## 10. Найкорисніші щоденні команди

### Ecosystem baseline check
```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
```

### Статус repo memory layer
```bash
./tools/graphiti_admin.py status /absolute/path/to/repo
```

### Doctor
```bash
./tools/graphiti_admin.py doctor /absolute/path/to/repo
```

### Manual flush
```bash
./tools/graphiti_admin.py flush /absolute/path/to/repo --limit 20
```

### Requeue
```bash
./tools/graphiti_admin.py requeue /absolute/path/to/repo --source dead-letter --limit 20
```

### Repomix snapshot
```bash
npx repomix@latest
```

### Claude usage report
```bash
npx ccusage@latest
```

Примітка: `npx`-шлях для `repomix` і `ccusage` може вимагати мережу на першому запуску, якщо npm cache ще порожній.

## 11. Щоденні сценарії користувача

### Сценарій A. Я щойно відкрив новий repo
Попроси Claude Code:
- перевірити `baseline-doctor`, `status`, `doctor`;
- пояснити, що вже готово;
- далі працювати через agreed tool order.

### Сценарій B. Я повернувся до задачі наступного дня
Попроси Claude Code:
- спершу підхопити startup checkpoint;
- при потребі дочитати remote Graphiti history;
- потім продовжити задачу.

### Сценарій C. Я не розумію, що відбувається у framework
Попроси Claude Code:
- пояснити repo baseline;
- сказати, які hooks активні;
- сказати, що автоматизовано, а що все ще потребує твоєї участі.

### Сценарій D. Мені треба швидко зрозуміти незнайомий codebase
Попроси Claude Code почати з `codebase-memory-mcp`, а не з хаотичного читання файлів.

### Сценарій E. Мені треба UI/UX задача
Скажи явно, що можна спертися на `ui-ux-pro-max-skill`.

## 12. Готові запити до Claude Code

### Поясни поточний стан repo

```text
Поясни мені поточний стан цього repo за фреймворком: що вже встановлено, які hooks і MCP-и працюють, що автоматизовано, а що ще потребує моєї участі.
```

### Підготуй repo з нуля

```text
Прочитай README.md, TUTORIAL.md, QUICKSTART.md, INSTALL.md і USER-MANUAL.md з цього пакета.
Потім підготуй цей repo за фреймворком.
Перед ручними кроками коротко скажи, що саме мені треба підтвердити або ввести самому.
```

### Продовж попередню роботу

```text
Почни з memory checkpoint і structural overview цього repo, а потім продовжуй задачу.
```

### Поясни framework людською мовою

```text
Поясни мені цей фреймворк людською мовою: що тут робить baseline, що додає repo overlay, як працюють пам'ять, hooks, plugins і коли я маю щось підтверджувати сам.
```

## 13. Що людина все ще робить сама

Людина все ще відповідає за:
- правильні secrets і env values;
- довіру до repo;
- plugin approvals;
- MCP approvals;
- вибір реального робочого завдання.

Фреймворк і Claude Code знімають з людини багато ручної роботи, але не повинні приховувати ці точки контролю.

## 14. Найважливіше правило користування

Не намагайся обійти framework ручними дублями.

Не треба:
- вдруге додавати ті самі MCP-и в repo `.mcp.json`;
- вручну копіювати plugin hooks у repo settings;
- вручну крутити storage ids;
- вручну лагодити `.claude/state/`, поки не зрозумів, що саме зламалось.

Спершу проси Claude Code пояснити і перевірити стан через docs та admin commands.
