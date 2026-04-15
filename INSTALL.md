# Installation

## Supported operator environment

Очікуване операторське середовище: **Linux, macOS або WSL**.
Команди нижче описані для `bash`, `python3 -m venv`, Docker Compose і repo-local shell scripts.
Windows-native shell без WSL цим пакетом не покривається як first-class path.

## 0. Як читати цей install flow

Нормальна модель така:
- **ти** даєш секрети, підтверджуєш prompts і вирішуєш, який repo готувати;
- **Claude Code** читає цей файл і виконує кроки install/bootstrap;
- **цей пакет** автоматизує repo surfaces, hooks, memory і `codebase-memory-mcp` bootstrap.

Під час install від тебе можуть знадобитися лише чотири типи ручної участі:
- ввести API keys або інші env secrets;
- підтвердити plugin install prompts;
- підтвердити project MCP approvals;
- запустити Docker/інфраструктуру, якщо Claude Code не має доступу до цього напряму.

## 1. Передумови

Потрібні:
- Claude Code
- Python 3.10+
- `python3 -m venv`
- Git
- Docker + Docker Compose для live Graphiti backend
- Node.js / `npx` для `repomix`, `ccusage` і plugin ecosystem

## 2. Розпакуй пакет

```bash
mkdir -p ~/data
unzip /path/to/downloaded-package.zip -d ~/data/
cd ~/data/claude-code-framework-v7-ecosystem-final
```

## 3. Підготуй retained baseline і не змішай різні його частини

### 3.1 Repo-declared plugin portion — канонічний шлях для plugin layer
Repo bootstrap сам додасть у `.claude/settings.json`:
- `extraKnownMarketplaces`
- `enabledPlugins`

для ECC, context-mode і ui-ux-pro-max-skill.

Це відтворює **plugin portion** retained baseline на fresh clone і в cloud sessions, якщо є trust і доступ до marketplace source.

### 3.2 Локально для зручності — постав plugins одразу
```text
/plugin marketplace add https://github.com/affaan-m/everything-claude-code
/plugin install ecc@ecc
/plugin marketplace add mksglu/context-mode
/plugin install context-mode@context-mode
/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
/plugin install ui-ux-pro-max@ui-ux-pro-max-skill
/reload-plugins
```

### 3.3 ECC rules — окремий required step, якщо хочеш повний ECC rules surface
Актуальне обмеження ECC таке: plugin install не розносить `rules` автоматично. Для повного ECC rules surface зроби один із двох шляхів.

Найнадійніший:
```bash
git clone https://github.com/affaan-m/everything-claude-code.git ~/data/everything-claude-code
cd ~/data/everything-claude-code
npm install
./install.sh --profile full
```

Альтернатива — скопіювати `rules/common` і потрібні мовні директорії в `~/.claude/rules/` або в project `.claude/rules/`.

### 3.4 Local operator utilities
```bash
npx repomix@latest
npx ccusage@latest
```

Важливо:
- Context7, GitHub MCP і Sequential Thinking приходять через ECC.
- Їх не треба дублювати окремими repo entries у цьому фреймворку.
- Якщо ECC ставиться як plugin, не копіюй його hooks вручну в repo `settings.json`.
- `repomix` і `ccusage` не декларуються в repo settings; це operator-local CLI-утиліти.
- Перший plugin install і перший `npx` запуск можуть вимагати мережу, якщо локальні cache ще порожні.

## 4. Постав `codebase-memory-mcp` binary без автоконфігурації

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash -s -- --skip-config
```

Якщо binary не в PATH:
```bash
export CODEBASE_MEMORY_MCP_BIN="/absolute/path/to/codebase-memory-mcp"
```

Пакет потім сам виконає:
- `codebase-memory-mcp config set auto_index true`
- `codebase-memory-mcp cli index_repository '{"repo_path":"..."}'`

Тобто прихований first-run крок більше не лишається недописаним у документації.

## 5. Обери backend для Graphiti

### Canonical baseline
- backend: `neo4j`
- provider: `openai`
- MCP config file: `/graphiti-config/config-docker-neo4j.openai.yaml`

### Lightweight local path
- backend: `falkordb`
- provider: `openai`
- MCP config file: `/graphiti-config/config-docker-falkordb.openai.yaml`
- `SEMAPHORE_LIMIT=1`

### Gemini path
Заміни `GRAPHITI_MCP_CONFIG_PATH` на один із:
- `/graphiti-config/config-docker-neo4j.gemini.yaml`
- `/graphiti-config/config-docker-falkordb.gemini.yaml`

### OpenAI-compatible path (`openai_generic`)
`openai_generic` у цьому пакеті підтримується для **host direct-ingest runtime**.
Packaged MCP Docker configs тут є тільки для `openai` і `gemini`, тому для `openai_generic` використовуй:
- custom remote Graphiti MCP endpoint;
- або власний Graphiti MCP config поза shipped compose files.

## 6. Підготуй Docker env

### Neo4j
```bash
cp ops/env/graphiti.neo4j.env.example ops/env/graphiti.neo4j.env
```

Заповни мінімум:
- `OPENAI_API_KEY` або `GOOGLE_API_KEY`
- `NEO4J_PASSWORD`
- за потреби `GRAPHITI_MCP_CONFIG_PATH`

За замовчуванням:
- bind host — `127.0.0.1`
- demo password — `demodemo`

### FalkorDB
```bash
cp ops/env/graphiti.falkordb.env.example ops/env/graphiti.falkordb.env
```

Заповни мінімум:
- `OPENAI_API_KEY` або `GOOGLE_API_KEY`
- лиши `SEMAPHORE_LIMIT=1`
- за потреби зміни `GRAPHITI_MCP_CONFIG_PATH`

## 7. Підніми Graphiti stack

### Neo4j
```bash
cd ops
docker compose -f docker-compose.graphiti-neo4j.yml up -d
cd ..
```

### FalkorDB
```bash
cd ops
docker compose -f docker-compose.graphiti-falkordb.yml up -d
cd ..
```

## 8. Додай shell env для host direct-ingest runtime

### Neo4j + OpenAI
```bash
export OPENAI_API_KEY="..."
export GRAPHITI_MCP_ENDPOINT="http://127.0.0.1:8000/mcp/"
export GRAPHITI_HEALTH_URL="http://127.0.0.1:8000/health"
export NEO4J_URI="bolt://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="demodemo"
export GRAPHITI_OPENAI_MODEL="gpt-4.1"
export GRAPHITI_OPENAI_SMALL_MODEL="gpt-4.1-mini"
export GRAPHITI_OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
```

### Neo4j + Gemini
```bash
export GOOGLE_API_KEY="..."
export GRAPHITI_MCP_ENDPOINT="http://127.0.0.1:8000/mcp/"
export GRAPHITI_HEALTH_URL="http://127.0.0.1:8000/health"
export NEO4J_URI="bolt://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="demodemo"
```

### FalkorDB + OpenAI
```bash
export OPENAI_API_KEY="..."
export GRAPHITI_MCP_ENDPOINT="http://127.0.0.1:8000/mcp/"
export GRAPHITI_HEALTH_URL="http://127.0.0.1:8000/health"
export FALKORDB_URI="redis://127.0.0.1:6379"
export SEMAPHORE_LIMIT="1"
```

### OpenAI-compatible (`openai_generic`) direct-ingest runtime
```bash
export OPENAI_API_KEY="..."
export GRAPHITI_MCP_ENDPOINT="http://127.0.0.1:8000/mcp/"
export GRAPHITI_HEALTH_URL="http://127.0.0.1:8000/health"
export NEO4J_URI="bolt://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="demodemo"
export GRAPHITI_OPENAI_GENERIC_BASE_URL="https://your-openai-compatible-endpoint.example/v1"
export GRAPHITI_OPENAI_GENERIC_MODEL="your-model-name"
```

### Offline / wheelhouse runtime install
```bash
export GRAPHITI_SKIP_PIP_BOOTSTRAP=1
export GRAPHITI_RUNTIME_PIP_EXTRA_ARGS="--no-index --find-links /absolute/path/to/wheelhouse"
```

## 9. Bootstrap repo

```bash
./tools/install-graphiti-stack.sh /absolute/path/to/repo \
  --backend neo4j \
  --provider openai \
  --logical-group-id verbalium/mobile-app
```

Що робить bootstrap:
- створює або оновлює repo `CLAUDE.md`;
- додає working principles і tool priority;
- додає `MEMORY_GROUP_ID` і `GRAPHITI_STORAGE_GROUP_ID`;
- додає `graphiti-memory` і `codebase-memory-mcp` у `.mcp.json`;
- додає Graphiti hook groups у `.claude/settings.json`;
- додає `extraKnownMarketplaces` + `enabledPlugins` для retained plugin layer;
- ставить repo-owned hook runtime;
- конфігурує `codebase-memory-mcp auto_index=true`;
- запускає первинний `index_repository`.

## 10. Перевір install state

```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
./tools/graphiti_admin.py status /absolute/path/to/repo
./tools/graphiti_admin.py doctor /absolute/path/to/repo
```

Як читати результат:
- `baseline-doctor` показує reproducible plugin layer, repo MCP contract, local invokers і стан ECC rules surface;
- `mcp_http_health` показує reachability Graphiti MCP HTTP server-а;
- `direct_ingest.ready` показує готовність repo runtime для `graphiti_flush.py`;
- `codebase_memory` показує, чи є `codebase-memory-mcp` entry і чи резолвиться її command;
- `project_mcp_approval_verifiable_here: false` означає, що interactive approval state перевіряється вже в Claude Code.

## 11. Відкрий repo у Claude Code

Порядок такий:
1. відкрий repo;
2. переконайся, що Claude бачить `.claude/settings.json` і `.mcp.json`;
3. погодь plugin/marketplace prompts, якщо Claude їх показує;
4. схвали project MCP servers, якщо Claude Code питає;
5. виконай `/reload-plugins`, якщо plugins ставилися під час поточної сесії.

Корисні дії в Claude Code:
- `/status` — подивитися, які settings layers реально активні;
- `/hooks` — подивитися активні hook configurations;
- `/mcp` — подивитися servers і auth state;
- `/skills` — подивитися skills з project, user і plugin sources;
- `claude mcp reset-project-choices` — скинути project approvals, якщо попередній вибір заважає.

## 12. Що verified пакетом, а що ні

Локально пакетом verified:
- repo bootstrap;
- runtime install;
- queue/ledger/archive path;
- admin CLI path;
- mock ingest and local recall;
- `codebase-memory-mcp` entry у project `.mcp.json`;
- repo-declared plugin baseline у `.claude/settings.json`;
- `codebase-memory-mcp auto_index` + первинний `index_repository` install step.

Не видається за вже перевірене в кожному середовищі:
- live Docker bring-up тут і зараз, якщо Docker недоступний;
- interactive Claude Code marketplace/plugin prompt state;
- interactive Claude Code project approval state;
- remote auth flow у конкретного провайдера без реального входу.

## 13. Що в install потоці робить людина, а що Claude Code

### Людина
- розпаковує пакет або дає Claude Code шлях до нього;
- дає env secrets;
- підтверджує plugin / MCP prompts;
- вирішує, який саме repo bootstrap-нути.

### Claude Code
- читає docs пакета;
- запускає installer;
- перевіряє `baseline-doctor`, `status`, `doctor`;
- далі працює у вже підготовленому repo, спираючись на `CLAUDE.md`, `.claude/settings.json` і `.mcp.json`.

### Фреймворк
- створює repo surfaces;
- заводить hooks і memory pipeline;
- вмикає plugin baseline на repo рівні;
- доводить `codebase-memory-mcp` до ready state на першому repo.
