# Quickstart

Це найкоротший робочий шлях для погодженого стеку.

Якщо ти хочеш, щоб install робив Claude Code, а не ти вручну, спершу відкрий [TUTORIAL.md](TUTORIAL.md), а потім дай Claude Code інструкцію з розділу 4.

## 1. Розпакуй пакет

```bash
mkdir -p ~/data
unzip /path/to/downloaded-package.zip -d ~/data/
cd ~/data/claude-code-framework-v7-ecosystem-final
```

## 2. Підготуй retained baseline

### Plugin portion
Repo все одно декларативно міститиме plugin layer через `.claude/settings.json`:
- ECC
- context-mode
- ui-ux-pro-max-skill

### Local operator utilities
Має бути доступно:
- `repomix` або `npx`
- `ccusage` або `npx`

### Важлива межа ECC
Repo-declared plugins не розносять ECC `rules` автоматично. Якщо хочеш повний ECC rules surface, один раз виконай upstream ECC install або скопіюй `rules/common` + потрібні мовні директорії. Деталі — в [INSTALL.md](INSTALL.md).

## 3. Постав `codebase-memory-mcp` binary без автоконфігурації

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash -s -- --skip-config
```

Якщо binary не лежить у PATH, задай:
```bash
export CODEBASE_MEMORY_MCP_BIN="/absolute/path/to/codebase-memory-mcp"
```

## 4. Підготуй Graphiti env

```bash
cp ops/env/graphiti.neo4j.env.example ops/env/graphiti.neo4j.env
```

У `ops/env/graphiti.neo4j.env` заповни мінімум:
- `OPENAI_API_KEY` або `GOOGLE_API_KEY`
- `NEO4J_PASSWORD`, якщо не хочеш demo default `demodemo`

## 5. Підніми Graphiti MCP + Neo4j

```bash
cd ops
docker compose -f docker-compose.graphiti-neo4j.yml up -d
cd ..
```

## 6. Додай shell env для host runtime

```bash
export OPENAI_API_KEY="..."
export GRAPHITI_MCP_ENDPOINT="http://127.0.0.1:8000/mcp/"
export GRAPHITI_HEALTH_URL="http://127.0.0.1:8000/health"
export NEO4J_URI="bolt://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="demodemo"
```

## 7. Bootstrap repo

```bash
./tools/install-graphiti-stack.sh /absolute/path/to/repo \
  --backend neo4j \
  --provider openai \
  --logical-group-id verbalium/mobile-app
```

Що відбудеться автоматично:
- bootstrap repo surfaces;
- runtime install;
- repo-declared plugin layer в `.claude/settings.json`;
- `graphiti-memory` + `codebase-memory-mcp` у `.mcp.json`;
- `codebase-memory-mcp config set auto_index true`;
- первинний `codebase-memory-mcp cli index_repository` для цього repo.

## 8. Перевір state

```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
./tools/graphiti_admin.py status /absolute/path/to/repo
./tools/graphiti_admin.py doctor /absolute/path/to/repo
```

Очікування:
- `.claude/settings.json` містить `extraKnownMarketplaces` + `enabledPlugins` для retained baseline;
- `.mcp.json` містить `graphiti-memory` і `codebase-memory-mcp`;
- `CLAUDE.md` містить working principles і memory ids;
- `.claude/settings.json` містить Graphiti hook events;
- runtime stamp існує;
- `doctor.direct_ingest.ready` дорівнює `true`.

## 9. Відкрий repo у Claude Code

У Claude Code треба:
1. відкрити корінь repo;
2. переконатися, що Claude бачить repo `.claude/settings.json` і `.mcp.json`;
3. погодити marketplace/plugin prompts, якщо Claude їх показує;
4. погодити project MCP servers, якщо approvals увімкнені;
5. виконати `/reload-plugins`, якщо щойно ставив plugins у live session.

Після цього:
- ECC дає базовий harness;
- context-mode зменшує шум від MCP output;
- `SessionStart` дає локальний memory checkpoint;
- `Stop` і `PreCompact` capture-ять summaries в queue;
- `codebase-memory-mcp` уже має `auto_index=true` і первинний index;
- Graphiti MCP tools доступні для ручного recall/search.

Примітка: перший plugin install і перший `npx` запуск можуть вимагати мережу, якщо локальні cache ще порожні.


## 10. Що сказати Claude Code після першого відкриття repo

Після того як repo відкритий у Claude Code, найзручніше дати одну з таких інструкцій.

### Зібрати контекст і почати працювати

```text
Перевір baseline-doctor, status і doctor для цього repo.
Поясни мені коротко результат, а потім почни працювати, використовуючи codebase-memory-mcp для структури коду, Graphiti для continuity і Context7 для актуальної документації.
```

### Продовжити попередню роботу

```text
Спершу підхопи memory checkpoint цього repo, перевір Graphiti continuity і структурний стан коду, а потім продовжуй задачу.
```

### Пояснити, що вже встановлено

```text
Поясни мені простими словами, що в цьому repo робить baseline, що додає overlay, які hooks активні і що автоматизовано без моєї участі.
```
