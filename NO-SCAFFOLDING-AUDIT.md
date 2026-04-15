# No scaffolding audit

Мета цього проходу — довести, що пакет не містить поверхонь, де текст уже обіцяє робочу поведінку, а коду або конфігу під нею немає.

## Що перевірено

### 1. Docs surface відповідає реальним package files
- усі основні markdown docs існують;
- усі relative links ведуть у наявні файли;
- README, GLOBAL-BASELINE, INSTALL, USER-MANUAL і SUPPORT-MATRIX описують одну й ту саму систему.

### 2. Repo overlay не є описовою оболонкою
- `templates/project/CLAUDE.md` реально існує;
- bootstrap реально додає working principles і tool priority в `CLAUDE.md`;
- `.mcp.graphiti.fragment.json` реально додає `graphiti-memory` і `codebase-memory-mcp`;
- hooks і support libs реально присутні.

### 3. Runtime path не лишився в напівстані
- runtime installer реально існує;
- admin CLI реально викликає repo wrapper;
- direct-ingest path реально реалізований кодом, а не лише описаний словами;
- flush має stale-lock recovery.

### 4. Merge/update path не вводить в оману
- bootstrap зберігає custom hooks;
- bootstrap зберігає custom MCP auth fields;
- bootstrap додає `codebase-memory-mcp` project entry;
- managed manifest реально використовується для stale-file pruning.

### 5. Global baseline описаний чесно
- docs не видають ECC, context-mode, ui-ux-pro-max-skill, repomix, ccusage і `codebase-memory-mcp` binary за package-managed installs;
- docs прямо кажуть, що це documented upstream flows, а не локальний installer цього repo;
- repo reproducibility surface для plugin baseline реально існує в `.claude/settings.json`;
- `baseline-doctor` реально перевіряє plugin declarations, недопущення дубля ECC MCP-ів і локальну invoker-ready поверхню.

### 6. Прихований first-run step більше не схований
- install flow реально запускає `codebase-memory-mcp config set auto_index true`;
- install flow реально запускає початковий `codebase-memory-mcp cli index_repository`;
- docs більше не лишають structural layer у стані “далі користувач якось сам здогадається”.

## Підсумок

У working surfaces пакета немає порожніх заглушок.
Якщо package щось описує як automated repo surface, у дереві є відповідний файл, скрипт або template.
Якщо package щось описує як external baseline component, docs прямо кажуть, що це upstream-managed install path.
