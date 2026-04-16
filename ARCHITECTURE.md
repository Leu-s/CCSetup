# Architecture

## 1. Верхньорівнева модель

Фреймворк має дві чіткі площини.

### A. Retained Claude Code baseline
- ECC
- Context7 / GitHub MCP / Sequential Thinking через ECC
- context-mode
- ui-ux-pro-max-skill
- repomix
- ccusage

### B. Repo-owned overlay
- Graphiti
- repo hooks
- `MEMORY_GROUP_ID`
- `GRAPHITI_STORAGE_GROUP_ID`
- `codebase-memory-mcp`
- project `.mcp.json`
- repo `.claude/settings.json`
- repo `CLAUDE.md`

## 2. Розподіл відповідальності

### ECC
Глобальний harness, не repo memory layer.

### context-mode
Контекстна гігієна, не довга пам’ять і не code graph.

### Graphiti
Канонічна довга пам’ять проекту.

### codebase-memory-mcp
Структурна карта коду. Не зберігає розмовну пам’ять і не дублює Graphiti.

### repo `.claude/settings.json`
Канонічний repo-level surface для:
- Graphiti hooks;
- reproducible plugin baseline (`extraKnownMarketplaces` + `enabledPlugins`).

### `CLAUDE.md`
Людські правила роботи й tool priority. Саме сюди перенесені принципи Karpathy.

## 3. Repo data flow

```text
Claude Code session
  -> repo .claude/settings.json declares plugin baseline + repo hooks
  -> repo CLAUDE.md defines working principles + ids
  -> SessionStart injects local checkpoint from delivered ledger
  -> code questions go first to codebase-memory-mcp
  -> continuity / memory questions go to Graphiti
  -> Stop / PreCompact capture a summary into local spool + ledger
  -> flush worker delivers payloads through graphiti_core
  -> Graphiti MCP exposes read/search tools to Claude
```

## 4. Чому тут немає другого code graph або другого behavior plugin

Щоб не дублювати відповідальність:
- один structural code layer — `codebase-memory-mcp`;
- один canonical long-term memory layer — Graphiti;
- один базовий harness — ECC;
- behavior principles — у `CLAUDE.md`, а не в окремому plugin.

## 5. Межі — що свідомо не автоматизується пакетом

Ці поверхні лишаються зовнішніми runtime boundaries Claude Code і не є пропусками пакета:
- interactive plugin download/install у Claude Code UI/CLI;
- ECC `rules` install — через upstream ECC installer або ручне копіювання;
- `repomix` / `ccusage` download через `npx`, якщо локальний кеш ще порожній;
- interactive project MCP approvals;
- remote auth login flow до зовнішніх MCP endpoints.

Додатково поза baseline залишаються:
- другий canonical memory engine;
- другий code-graph engine поверх `codebase-memory-mcp`;
- ще один behavior plugin поверх принципів у `CLAUDE.md`;
- broad plugin layer з auth/perms surface без критичної потреби.
