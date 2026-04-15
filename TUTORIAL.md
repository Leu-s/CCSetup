# Tutorial

Це найлюдяніший спосіб користуватися цим фреймворком.

Його нормальний режим такий:
- **людина** завантажує пакет, дає секрети й підтверджує prompts;
- **Claude Code** читає docs, робить install/bootstrap і далі працює всередині repo;
- **сам фреймворк** автоматизує hooks, memory, repo settings, MCP wiring і частину first-run setup.

## 1. Що це за пакет на практиці

Пакет дає два шари:
- **базовий Claude Code baseline**: ECC, Context7/GitHub/Sequential Thinking через ECC, context-mode, ui-ux-pro-max-skill, repomix, ccusage;
- **repo overlay**: Graphiti memory, `codebase-memory-mcp`, repo `CLAUDE.md`, `.claude/settings.json`, `.mcp.json`, hooks і state tree.

Тобто це не просто "пам'ять". Це робоче середовище для Claude Code навколо конкретного репозиторію.

## 2. Хто що робить

### Що робиш ти
- розпаковуєш пакет;
- даєш Claude Code доступ до repo;
- задаєш потрібні env secrets;
- підтверджуєш plugin / MCP prompts;
- за потреби просиш Claude Code пояснити, що відбувається.

### Що робить Claude Code
- читає `README.md`, `QUICKSTART.md`, `INSTALL.md`, `USER-MANUAL.md`;
- виконує install flow і bootstrap repo;
- далі працює через agreed tool order: `codebase-memory-mcp` → Graphiti → Context7 → GitHub MCP → raw files.

### Що робить фреймворк автоматично
- сідає repo `CLAUDE.md`, `.claude/settings.json`, `.mcp.json`;
- підключає Graphiti hooks;
- створює queue/ledger/archive path для пам'яті;
- вимикає built-in auto memory на repo рівні;
- вмикає `codebase-memory-mcp auto_index` і робить первинну індексацію repo;
- декларує retained **plugin** layer у repo settings.

## 3. Що саме змінює bootstrap у repo

Після install/bootstrap у repo з’являються або оновлюються:
- `CLAUDE.md`;
- `.claude/settings.json`;
- `.mcp.json`;
- `.claude/graphiti.json`;
- `.claude/hooks/*`;
- `.claude/rules/graphiti-memory.md`;
- `.claude/state/.gitignore`;
- `.claude/state/graphiti-runtime/` і runtime stamp;
- локальні queue/ledger/archive файли вже під час роботи hooks.

Що **не** приїжджає в repo автоматично:
- `repomix` і `ccusage` як локальні CLI;
- ECC `rules`, бо plugin layer не розносить їх автоматично.

## 4. Перший шлях з нуля

1. Пройди [QUICKSTART.md](QUICKSTART.md).
2. Якщо треба повний install з поясненнями — відкрий [INSTALL.md](INSTALL.md).
3. Після bootstrap виконай:
   - `./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo`
   - `./tools/graphiti_admin.py status /absolute/path/to/repo`
   - `./tools/graphiti_admin.py doctor /absolute/path/to/repo`
4. Відкрий repo у Claude Code.
5. Погодь plugin / MCP prompts, якщо вони з'являться.

## 5. Що сказати Claude Code

### Варіант 1. Постав фреймворк з нуля

```text
Прочитай README.md, TUTORIAL.md, QUICKSTART.md, INSTALL.md і USER-MANUAL.md з цього пакета.
Потім підготуй цей repo за цим фреймворком.
Спочатку скажи, які ручні кроки й підтвердження потрібні від мене, а далі виконуй install послідовно.
Не дублюй ECC MCP-и в repo .mcp.json і не копіюй plugin hooks вручну.
```

### Варіант 2. Перевір, чи все вже встановлено правильно

```text
Перевір цей repo на відповідність фреймворку.
Почни з baseline-doctor, status і doctor.
Поясни простими словами, що вже гаразд, а що ще треба доробити.
```

### Варіант 3. Поясни фреймворк людською мовою

```text
Поясни мені цей фреймворк як користувачу: що він автоматизує, що робить Claude Code, що маю робити я сам, і як мені працювати з ним щодня.
Спирайся на TUTORIAL.md і USER-MANUAL.md.
```

## 6. Що побачиш у Claude Code на першому відкритті repo

Нормальна послідовність така:
- Claude Code бачить repo `.claude/settings.json`;
- може попросити підтвердити plugins із retained baseline;
- може попросити підтвердити project MCP servers;
- після цього repo уже має working plugin baseline, hooks, `graphiti-memory` і `codebase-memory-mcp`.

Важлива межа: repo settings відтворюють **plugin layer**, але не встановлюють за тебе `repomix`, `ccusage` і не розносять ECC `rules`. Для повного ECC rules surface окремо постав upstream ECC rules або скопіюй `rules/common` + потрібні мовні директорії.

Якщо щось із цього незрозуміло, не намагайся вгадувати вручну. Просто попроси Claude Code пояснити, який prompt з'явився і навіщо він потрібний.

## 7. Як користуватися фреймворком щодня

### Коли треба зрозуміти новий repo
Скажи Claude Code, щоб він почав із `codebase-memory-mcp`, а не читав файли навмання.

### Коли треба продовжити вчорашню роботу
Попроси спершу перевірити Graphiti memory і startup checkpoint, а потім перейти до конкретної задачі.

### Коли треба поточна документація бібліотеки
Скажи використати Context7.

### Коли треба GitHub-операції
Скажи використати GitHub MCP.

### Коли треба повний snapshot repo
Скажи використати `repomix`.

### Коли треба подивитися usage/cost
Скажи використати `ccusage`.

### Коли задача UI/UX
Скажи явно, що можна спертися на `ui-ux-pro-max-skill`.

## 8. Що автоматизовано, а що ні

### Автоматизовано
- Graphiti capture через `Stop` і `PreCompact`;
- local checkpoint на `SessionStart`;
- reproducible plugin baseline у repo settings;
- `codebase-memory-mcp` first-run bootstrap;
- admin CLI для health/status/flush/requeue.

### Не автоматизовано повністю
- введення секретів;
- live approvals у Claude Code;
- ECC rules install, якщо хочеш повний rules surface від ECC;
- зовнішній Docker/runtime bring-up, якщо середовище цього не дозволяє;
- рішення, який саме task ти хочеш робити далі.

## 9. Типові помилки користувача

Не треба:
- вручну дублювати Context7/GitHub/Sequential Thinking у repo `.mcp.json`;
- вручну копіювати ECC hooks у repo hooks;
- думати, що repo-declared plugin layer автоматично встановив `repomix`, `ccusage` або ECC `rules`;
- міняти `GRAPHITI_STORAGE_GROUP_ID` руками без migration flow;
- редагувати `.claude/state/` як звичайну конфігурацію;
- чекати, що нова машина автоматично матиме той самий local startup checkpoint.

## 10. Якщо щось незрозуміло

Найкращий шлях — не шукати відповідь навмання, а попросити Claude Code пояснити систему по docs.

Почни з цього:

```text
Поясни мені поточний стан цього фреймворку за його документацією.
Скажи, що тут є базовим baseline, що додається на рівні repo, що автоматизовано, що потребує мого підтвердження, і як мені правильно користуватися цим стеком.
```
