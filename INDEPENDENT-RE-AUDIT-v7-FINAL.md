# Independent re-audit — closure pass

## Executive verdict

Після ще одного незалежного canonical-docs pass у межах **scope цього пакета** відкритих package-level gap-ів не залишилось.

У цьому проході були знайдені й закриті ще кілька останніх неузгодженостей у документації:
- repo-declared plugin layer був описаний ширше, ніж реально покриває retained baseline;
- не було явно зафіксовано, що ECC `rules` не розносяться через plugin layer;
- не було досить чітко розведено plugin layer, ECC rules surface і operator-local CLI-утиліти;
- `openai_generic` був у коді й support matrix, але майже не був описаний у install docs;
- платформа `systemd` на macOS залишалася implied, а не explictly bounded.

Пакет тепер покриває дві площини без розриву між docs, templates, tools і validation surface:
- **retained Claude Code ecosystem baseline** — ECC, Context7 / GitHub MCP / Sequential Thinking через ECC, context-mode, ui-ux-pro-max-skill, repomix, ccusage;
- **repo-owned Graphiti overlay** — Graphiti, queue-first Stop/PreCompact hooks, `MEMORY_GROUP_ID`, `GRAPHITI_STORAGE_GROUP_ID`, `codebase-memory-mcp`, repo `CLAUDE.md`, repo `.claude/settings.json`, repo `.mcp.json`, admin CLI й runtime.

## Що було перевірено наново

### Документація
Переперевірені всі top-level markdown docs, FILE-TREE, CONFIG-REFERENCE, CLI-REFERENCE, SECURITY, SUPPORT-MATRIX, VALIDATION, NO-SCAFFOLDING-AUDIT.

### Templates і config surfaces
Переперевірені:
- `templates/project/CLAUDE.md`
- `templates/project/.claude/settings.graphiti.fragment.json`
- `templates/project/.mcp.graphiti.fragment.json`
- `templates/project/.claude/graphiti.json`
- усі repo hooks і `lib/*`

### Tools
Переперевірені:
- `tools/graphiti_bootstrap.py`
- `tools/install-graphiti-stack.sh`
- `tools/install-hook-runtime.sh`
- `tools/configure-codebase-memory.sh`
- `tools/baseline_doctor.py`
- `tools/graphiti_admin.py`
- `tools/validate-package.py`

### Ops / examples
Переперевірені:
- Docker Compose для Neo4j і FalkorDB
- env examples
- Graphiti MCP config YAMLs
- systemd units
- Caddy example
- remote MCP examples (`headers` і `headersHelper`)

### Фактичні перевірки
Виконані команди:

```bash
python3 tools/validate-package.py
python3 -m compileall templates/project/.claude/hooks tools tests
bash -n tools/install-graphiti-stack.sh
bash -n tools/install-hook-runtime.sh
bash -n tools/configure-codebase-memory.sh
bash -n templates/project/.claude/hooks/run_python.sh
python3 tests/test_admin_wrapper.py -v
python3 tests/test_baseline_doctor.py -v
python3 tests/test_bootstrap_hygiene.py -v
python3 tests/test_e2e_mock.py -v
python3 tests/test_group_ids.py -v
python3 tests/test_hook_contracts.py -v
python3 tests/test_install_flow_offline.py -v
```

Окремо виконаний **незалежний install/setup walkthrough** у тимчасовий repo, без опори на test harness як єдиний доказ.

## П’ять пунктів, які були відкриті, і як вони закриті

### 1. Global baseline audit / doctor
**Було:** глобальний baseline був задокументований, але не мав окремої перевірки.

**Закрито:**
- додано `tools/baseline_doctor.py`;
- додано CLI entry `./tools/graphiti_admin.py baseline-doctor`;
- додано test `tests/test_baseline_doctor.py`;
- docs тепер ведуть через `baseline-doctor` як обов’язкову частину install verification.

**Що саме тепер перевіряється:**
- repo-declared plugin baseline в `.claude/settings.json`;
- marketplace declarations для ECC / context-mode / ui-ux-pro-max-skill;
- `enabledPlugins` для тих самих plugin-ів;
- відсутність forbidden duplicates для `context7`, `github`, `sequential-thinking` у project `.mcp.json`;
- invoker-ready path для `repomix`, `ccusage` і `codebase-memory-mcp`;
- informative state про локальний plugin cache і `claude` CLI.

### 2. Reproducibility plugin layer
**Було:** baseline повернувся в docs, але не був declared на repo рівні як канонічний surface.

**Закрито:**
- `templates/project/.claude/settings.graphiti.fragment.json` тепер містить `extraKnownMarketplaces` і `enabledPlugins`;
- `tools/graphiti_bootstrap.py` тепер реально мержить ці top-level keys, а не тільки hooks;
- docs переписані так, що repo `.claude/settings.json` — canonical reproducibility surface;
- validation тепер це перевіряє явно.

### 3. Прихований first-run step для `codebase-memory-mcp`
**Було:** binary install був описаний, але activation/first index лишалися implicit.

**Закрито:**
- додано `tools/configure-codebase-memory.sh`;
- `tools/install-graphiti-stack.sh` тепер викликає цей script автоматично;
- install flow реально виконує:
  - `codebase-memory-mcp config set auto_index true`
  - `codebase-memory-mcp cli index_repository '{"repo_path":"..."}'`
- docs, CLI reference і troubleshooting тепер фіксують це прямо;
- unit test і independent walkthrough підтвердили обидва виклики фактично.

### 4. Застарілий carry-over report
**Було:** у пакеті лишався старий `RE-AUDIT-POST-FIX.md`, який створював scope drift.

**Закрито:**
- файл видалений;
- validator тепер окремо ламає pass, якщо цей stale report знову з’явиться;
- docs і FILE-TREE очищені від цього carry-over.

### 5. `VALIDATION.md` не відповідав новому scope
**Було:** validation surface описував старий repo-only шар і відставав від повернутого baseline.

**Закрито:**
- `VALIDATION.md` переписаний;
- тепер він покриває repo-declared plugin baseline, `baseline-doctor`, `codebase-memory-mcp` bootstrap, supported operator environment і межу між verified package scope та зовнішнім interactive client state;
- `tools/validate-package.py` тепер перевіряє, що docs справді містять supported platform contract і codebase bootstrap contract.

## Додаткові проблеми, знайдені під час closure pass, і виправлення

### A. `baseline_doctor` не розумів `${VAR:-default}` у `.mcp.json`
**Симптом:** doctor хибно вважав `codebase-memory-mcp` нерозв’язним, якщо команда була записана як `${CODEBASE_MEMORY_MCP_BIN:-codebase-memory-mcp}`.

**Виправлення:**
- додано shell-style env expansion у `tools/baseline_doctor.py`;
- test `tests/test_baseline_doctor.py` тепер проходить на реальному template path.

### B. FalkorDB compose мав зайвий exposed surface
**Симптом:** у FalkorDB compose ще був порт `3000`.

**Виправлення:**
- `ops/docker-compose.graphiti-falkordb.yml` більше не expose-ить `3000`;
- validator тепер окремо ламає pass, якщо `:3000:3000` повернеться.

### C. Remote auth examples були надто вузькими
**Симптом:** був лише bearer-header приклад.

**Виправлення:**
- додано `ops/examples/mcp.graphiti.remote-headers-helper.example.json`;
- SECURITY і TROUBLESHOOTING тепер описують `headersHelper` як правильний варіант для short-lived auth.

### D. Supported operator environment був implicit
**Симптом:** пакет явно орієнтувався на bash/venv/Docker/systemd, але docs не фіксували platform contract.

**Виправлення:**
- README, INSTALL, SUPPORT-MATRIX, VALIDATION тепер прямо фіксують: supported operator environment = Linux / macOS / WSL;
- Windows-native shell без WSL більше не лишається прихованою залежністю.

## Останні неузгодженості, знайдені під час canonical-docs pass

### A. ECC plugin layer ≠ повний ECC rules surface
**Було:** docs трактували repo-declared plugin layer як ніби він відтворює весь retained baseline.

**Виправлення:**
- README, TUTORIAL, QUICKSTART, INSTALL, USER-MANUAL, GLOBAL-BASELINE, SUPPORT-MATRIX, CONFIG-REFERENCE і VALIDATION тепер явно розводять:
  - plugin layer;
  - ECC rules surface;
  - operator-local CLI utilities.
- `tools/baseline_doctor.py` тепер показує стан ECC rules presence і попереджає, якщо rules ще не встановлені.

### B. `repomix` і `ccusage` були описані занадто близько до repo-declared reproducibility
**Було:** docs легко читалися так, ніби repo settings покривають увесь retained baseline, включно з локальними CLI.

**Виправлення:**
- docs тепер прямо кажуть, що `repomix` і `ccusage` — operator-local utilities;
- baseline doctor окремо показує invoker availability;
- docs додають примітку про мережу на першому `npx` запуску.

### C. `openai_generic` був недоописаний
**Було:** код і support matrix підтримували `openai_generic`, але install docs майже не пояснювали, як ним користуватися.

**Виправлення:**
- INSTALL тепер явно описує `openai_generic` як host direct-ingest path;
- docs пояснюють, що shipped MCP compose configs у пакеті є для `openai` і `gemini`, а для `openai_generic` потрібен custom/remote MCP config.

### D. systemd/macOS boundary була implicit
**Було:** README говорив про systemd user timers поруч із macOS, не відокремлюючи Linux/WSL path.

**Виправлення:**
- README і OPERATIONS тепер прямо кажуть, що `ops/systemd/*` — Linux/WSL path;
- для macOS пакет пропонує manual flush або власний scheduler, але не прикидається, що `launchd` уже постачається.

## Що підтверджено фактично незалежним walkthrough

В окремому тимчасовому repo було фактично підтверджено:
- `install-graphiti-stack.sh` створює repo surfaces і runtime;
- installer реально викликає `codebase-memory-mcp config set auto_index true`;
- installer реально викликає `codebase-memory-mcp cli index_repository`;
- `baseline-doctor` повертає `ok: true`;
- `status` повертає `graphiti_memory_present: true`, `codebase_memory_mcp_present: true`, resolvable command і правильні group ids;
- `doctor` повертає `ok: true`;
- `graphiti_stop.py -> graphiti_flush.py -> session_start.py` дають реальний recall checkpoint з delivered ledger.

## Що я встиг зробити

### Зроблено повністю
- закрито всі 5 пунктів попереднього аудиту;
- закрито останні canonical-docs неузгодженості між plugin layer, ECC rules і operator-local utilities;
- додано missing automation для global baseline і `codebase-memory-mcp`;
- прибрано stale drift artifact;
- вирівняно docs, templates, tools і validation surface;
- проведено повторну фактичну валідацію й незалежний walkthrough;
- package очищено від cache artifacts після перевірок.

### Що не встиг зробити
У межах **package scope** незакритих пунктів не залишилось.

Не виконувались лише зовнішні дії, які цей repo не може “імплементувати всередині себе”:
- interactive marketplace/plugin prompts усередині живого Claude Code client-а;
- interactive project MCP approvals усередині Claude Code;
- live remote auth login до зовнішнього MCP endpoint;
- live Docker bring-up у середовищі без Docker.

Після closure pass це **не вважається недоробкою пакета**, бо тепер ці межі явно описані в docs і validation, а не замовчуються.

## Підсумкова оцінка готовності

### У межах package scope
**100% готовий.**

### Що це означає practically
- retained baseline тепер не загублений;
- repo overlay не загублений;
- memory path працює;
- hooks підключені;
- `CLAUDE.md` і repo settings реально інструктують Claude Code користуватися цією інфраструктурою;
- hidden install/setup gaps більше не лишилися;
- verification surface відповідає тому, що пакет реально обіцяє.


## Фінальний canonical pass після tutorial/docs round

Після окремого ще одного проходу поверх уже оновленого tutorial/docs пакета були знайдені й закриті останні дрібні неузгодженості:
- plugin layer був описаний надто широко відносно ECC rules surface;
- `repomix` і `ccusage` потрібно було чіткіше розвести як operator-local utilities;
- `openai_generic` треба було доописати як host direct-ingest path;
- Linux/WSL `systemd` path треба було жорстко відділити від macOS;
- `baseline_doctor` треба було навчити коректно читати `${VAR:-default}` для `codebase-memory-mcp`.

Після цих виправлень я ще раз фактично перепровірив пакет:
- `python3 tools/validate-package.py` → `ok: true`;
- `python3 tests/test_baseline_doctor.py -v` → `OK`;
- `python3 tests/test_admin_wrapper.py -v` → `OK`;
- `python3 tests/test_bootstrap_hygiene.py -v` → `OK`;
- `python3 tests/test_group_ids.py -v` → `OK`;
- `python3 tests/test_hook_contracts.py -v` → `OK`;
- `python3 tests/test_install_flow_offline.py -v` → `OK`;
- `python3 tests/test_e2e_mock.py` → `OK`.

Окремо був повторно виконаний незалежний walkthrough у тимчасовий repo:
- `install-graphiti-stack.sh`;
- `graphiti_admin.py baseline-doctor`;
- `graphiti_admin.py status`;
- `graphiti_admin.py doctor`;
- `graphiti_stop.py` → `graphiti_flush.py` → `session_start.py`.

У цьому walkthrough використано:
- `GRAPHITI_MOCK_INGEST=1` для deterministic offline ingest path;
- dummy `OPENAI_API_KEY`, щоб direct-ingest readiness пройшов у mock mode;
- stub `codebase-memory-mcp` binary, який імітує вже встановлений prerequisite з install docs.

Це важливо не як обхід, а як чесний спосіб підтвердити саме **package-managed install/setup logic** у середовищі без live Docker backend і без реального upstream binary installer. У межах package scope це відповідає documented offline validation path.

Після цього проходу нових package-level проблем не знайдено.
