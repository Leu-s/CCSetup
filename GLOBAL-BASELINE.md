# Global baseline

Це retained baseline, який має бути доступний для кожного repo. Він складається з **трьох різних шарів**, і їх не треба змішувати:
- **repo-declared plugin layer** — через `.claude/settings.json` цього пакета;
- **ECC rules surface** — окремий upstream-owned шар, який plugin system не розносить автоматично;
- **operator-local utilities** — `repomix` і `ccusage`.

## 1. Repo-declared plugin layer — канонічний шлях для plugin portion

Після bootstrap repo `.claude/settings.json` уже містить:
- `extraKnownMarketplaces` для:
  - `ecc` → `affaan-m/everything-claude-code`
  - `context-mode` → `mksglu/context-mode`
  - `ui-ux-pro-max-skill` → `nextlevelbuilder/ui-ux-pro-max-skill`
- `enabledPlugins` для:
  - `ecc@ecc`
  - `context-mode@context-mode`
  - `ui-ux-pro-max@ui-ux-pro-max-skill`

Наслідок:
- fresh clone має той самий plugin contract;
- cloud sessions можуть підтягнути plugin portion baseline з repo;
- user-scoped plugin installs більше не є єдиним source of truth для plugin layer.

## 2. Optional user preinstall — для зручності локальної машини

### ECC
```text
/plugin marketplace add https://github.com/affaan-m/everything-claude-code
/plugin install ecc@ecc
/reload-plugins
```

Fallback через upstream installer:
```bash
git clone https://github.com/affaan-m/everything-claude-code.git ~/data/everything-claude-code
cd ~/data/everything-claude-code
npm install
./install.sh --profile full
```

### context-mode
```text
/plugin marketplace add mksglu/context-mode
/plugin install context-mode@context-mode
/reload-plugins
/context-mode:ctx-doctor
```

### ui-ux-pro-max-skill
```text
/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
/plugin install ui-ux-pro-max@ui-ux-pro-max-skill
/reload-plugins
```

## 3. ECC rules surface — окремий required шар для повного ECC

ECC plugin не розносить `rules` автоматично. Якщо хочеш повний ECC rules surface, виконай upstream install:

```bash
git clone https://github.com/affaan-m/everything-claude-code.git ~/data/everything-claude-code
cd ~/data/everything-claude-code
npm install
./install.sh --profile full
```

Альтернатива — копіювати `rules/common` і потрібні мовні директорії в `~/.claude/rules/` або project `.claude/rules/`.

## 4. Operator-local utilities

### repomix
```bash
npx repomix@latest
```
Або:
```bash
npm install -g repomix
```

### ccusage
```bash
npx ccusage@latest
```
Або:
```bash
npm install -g ccusage
```

## 5. Що покриває ECC

Через ECC приходять:
- Context7
- GitHub MCP
- Sequential Thinking

Їх не треба дублювати в repo `.mcp.json`.

## 6. Як перевірити baseline

Після bootstrap конкретного repo:
```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
```

Ця перевірка показує:
- чи repo settings декларують retained plugin baseline;
- чи `.mcp.json` не дублює ECC-provided MCP-и;
- чи `repomix` і `ccusage` invocable напряму або через `npx`;
- чи `codebase-memory-mcp` резолвиться;
- чи локальний plugin cache уже присутній, або plugin layer поки існує тільки як repo declaration;
- чи ECC `rules` уже присутні локально або в repo;
- чи `repomix` і `ccusage` доступні напряму або тільки через `npx`.

Перший plugin install і перший `npx` запуск можуть вимагати мережу, якщо локальні cache ще порожні.
