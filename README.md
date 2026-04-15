# Claude Code Ecosystem Baseline + Graphiti Overlay

Це фреймворк для **узгодженого baseline-стеку Claude Code** з керованою **Graphiti-пам’яттю на рівні репозиторію**.

Він фіксує дві площини:
- **retained Claude Code ecosystem baseline**: ECC, Context7/GitHub/Sequential Thinking через ECC, context-mode, ui-ux-pro-max-skill, repomix, ccusage;
- **repo-owned overlay**: Graphiti, queue-first Stop/PreCompact hooks, `MEMORY_GROUP_ID`, `GRAPHITI_STORAGE_GROUP_ID`, `codebase-memory-mcp`, repo `CLAUDE.md`, `.claude/settings.json`, `.mcp.json`.

## Рекомендований шлях встановлення і налаштування

**Рекомендований шлях встановлення і налаштування — через Claude Code.**

Практичний порядок такий:
1. підготувати retained plugin layer один раз на машині або дати Claude Code поставити repo-declared plugins на першому trusted open;
2. окремо подбати про operator-local utilities (`repomix`, `ccusage`) і, якщо потрібен повний ECC rules surface, встановити ECC rules через upstream installer або ручне копіювання;
3. встановити `codebase-memory-mcp` binary;
4. підняти Graphiti MCP + backend;
5. bootstrap-нути конкретний repo цим пакетом;
6. відкрити repo в Claude Code і дати йому підхопити repo `.claude/settings.json` та `.mcp.json`.

## Якщо ти людина, а основну роботу робитиме Claude Code

Почни з цього порядку:
1. [TUTORIAL.md](TUTORIAL.md) — людський сценарій використання;
2. [QUICKSTART.md](QUICKSTART.md) — найкоротший install path;
3. [INSTALL.md](INSTALL.md) — повний install path;
4. [USER-MANUAL.md](USER-MANUAL.md) — щоденна робота і best practices.

Найкраща стартова інструкція для Claude Code:

```text
Прочитай README.md, TUTORIAL.md, QUICKSTART.md, INSTALL.md і USER-MANUAL.md з цього пакета.
Потім підготуй repo за цим фреймворком.
Перед ручними кроками коротко скажи, що саме мені треба підтвердити або ввести самому.
```

## Підтримуване операторське середовище

Пакет орієнтований на **Linux, macOS і WSL**.
`bash`, `python3 -m venv` і Docker Compose описані саме для цього середовища.
`systemd` user timer-и в пакеті — це Linux/WSL path; на macOS використовуй manual flush або власний scheduler (`launchd` пакет не постачає).
Windows-native flow без WSL не є first-class target у цьому пакеті.

## Що входить у погоджений baseline

### Retained ecosystem baseline
- ECC / everything-claude-code
- Context7, GitHub MCP, Sequential Thinking — через ECC
- context-mode
- ui-ux-pro-max-skill
- repomix
- ccusage

### Repo overlay
- Graphiti
- Stop + PreCompact capture flow
- `MEMORY_GROUP_ID`
- `GRAPHITI_STORAGE_GROUP_ID`
- `codebase-memory-mcp`
- repo `.claude/settings.json`, `CLAUDE.md`, `.mcp.json`, hooks і state tree

## Що тепер є source of truth

- **Repo `.claude/settings.json`** — канонічне місце для repo-declared plugin layer, repo hooks і project behavior.
- **Repo `.mcp.json`** — канонічне місце для Graphiti + `codebase-memory-mcp`.
- **Repo `CLAUDE.md`** — робочі принципи, tool priority, memory ids.
- **User/global preinstalls** — лише пришвидшують перший запуск, але більше не є єдиним способом відтворити baseline.

## Важлива межа retained baseline

Repo `.claude/settings.json` відтворює **plugin portion** retained baseline.
Вона **не** встановлює за тебе operator-local CLI-утиліти (`repomix`, `ccusage`) і **не** розносить ECC `rules`, бо ECC plugins не можуть автоматично дистрибутувати rules.

Практичний наслідок:
- plugin layer Claude Code може підтягнути з repo на першому trusted open;
- `repomix` і `ccusage` лишаються локальними CLI-утилітами;
- для повного ECC rules surface треба окремо виконати ECC upstream install або скопіювати `rules/common` + потрібні мовні директорії.

Перший plugin install і перший `npx` запуск можуть вимагати мережу, якщо локальні cache ще порожні.

## Що пакет реально автоматизує

Пакет автоматизує:
- bootstrap repo surfaces;
- dedicated hook runtime для host-side Graphiti ingest;
- queue-first capture через `Stop` і `PreCompact`;
- delivery path з retry / archive / dead-letter;
- deterministic mapping `MEMORY_GROUP_ID -> GRAPHITI_STORAGE_GROUP_ID`;
- repo-declared plugin layer через `extraKnownMarketplaces` + `enabledPlugins`;
- project `.mcp.json`, що додає `graphiti-memory` і `codebase-memory-mcp`;
- `codebase-memory-mcp` bootstrap: `auto_index=true` + первинний `index_repository` під час install flow;
- admin CLI, baseline doctor, doctor, status, flush і migration flow.

## Що пакет не підміняє

Пакет **не** підміняє upstream installers і не копіює чужі plugin hooks вручну:
- ECC hooks лишаються в ECC plugin/install layer;
- context-mode hooks лишаються в context-mode plugin layer;
- repo hooks цього пакета відповідають тільки за Graphiti lifecycle і repo env/state.

## Найкоротший шлях

```bash
mkdir -p ~/data
unzip /path/to/downloaded-package.zip -d ~/data/
cd ~/data/claude-code-framework-v7-ecosystem-final
```

Потім:
1. пройди [QUICKSTART.md](QUICKSTART.md);
2. пройди [INSTALL.md](INSTALL.md);
3. bootstrap-нь repo;
4. виконай `./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo`;
5. відкрий repo у Claude Code.

## Що читати далі

1. [TUTORIAL.md](TUTORIAL.md)
2. [GLOBAL-BASELINE.md](GLOBAL-BASELINE.md)
3. [STACK-DECISIONS.md](STACK-DECISIONS.md)
4. [QUICKSTART.md](QUICKSTART.md)
5. [INSTALL.md](INSTALL.md)
6. [USER-MANUAL.md](USER-MANUAL.md)
7. [HOOKS.md](HOOKS.md)
8. [OPERATIONS.md](OPERATIONS.md)
9. [CONFIG-REFERENCE.md](CONFIG-REFERENCE.md)
10. [SUPPORT-MATRIX.md](SUPPORT-MATRIX.md)
11. [VALIDATION.md](VALIDATION.md)
12. [INDEPENDENT-RE-AUDIT-v7-FINAL.md](INDEPENDENT-RE-AUDIT-v7-FINAL.md)
