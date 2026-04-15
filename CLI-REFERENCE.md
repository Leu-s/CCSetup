# CLI reference

## `./tools/install-graphiti-stack.sh`

Виконує повний repo bootstrap:
- seed-ить `CLAUDE.md`;
- мержить `.claude/settings.json`;
- мержить `.mcp.json`;
- ставить Graphiti runtime;
- вмикає `codebase-memory-mcp auto_index`;
- запускає первинний `index_repository`.

```bash
./tools/install-graphiti-stack.sh /absolute/path/to/repo \
  --backend neo4j \
  --provider openai \
  --logical-group-id verbalium/mobile-app
```

## `./tools/graphiti_admin.py baseline-doctor`

Перевіряє retained ecosystem contract:
- repo plugin declarations;
- відсутність repo-duplicate MCP entries для ECC-provided servers;
- invoker availability для `repomix` / `ccusage`;
- `codebase-memory-mcp` command resolution.

```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
```

## `./tools/graphiti_admin.py status`

Показує runtime state:
- group ids;
- MCP health;
- direct-ingest readiness;
- queue / archive / dead-letter metrics.

## `./tools/graphiti_admin.py doctor`

Глибша перевірка repo overlay:
- required hook events;
- project `.mcp.json` contract;
- `autoMemoryEnabled: false`;
- runtime readiness;
- registry collisions.

## `./tools/graphiti_admin.py flush`

Ручний flush pending memory payloads.

## `./tools/graphiti_admin.py requeue`

Повертає archived або dead-letter payloads назад у queue.

## `./tools/graphiti_admin.py migrate-logical-id`

Оновлює logical group id і за потреби storage id.
