# CLI reference

## `./tools/install-graphiti-stack.sh`

Runs the full repo bootstrap:
- seeds `CLAUDE.md`;
- merges `.claude/settings.json`;
- merges `.mcp.json`;
- installs the Graphiti runtime;
- enables `codebase-memory-mcp auto_index`;
- runs the initial `index_repository`.

```bash
./tools/install-graphiti-stack.sh /absolute/path/to/repo \
  --backend neo4j \
  --provider openai \
  --logical-group-id verbalium/mobile-app
```

## `./tools/graphiti_admin.py baseline-doctor`

Verifies the retained ecosystem contract:
- repo plugin declarations;
- absence of repo-duplicate MCP entries for ECC-provided servers;
- invoker availability for `repomix` / `ccusage`;
- `codebase-memory-mcp` command resolution.

```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
```

## `./tools/graphiti_admin.py status`

Shows runtime state:
- group ids;
- MCP health;
- direct-ingest readiness;
- queue / archive / dead-letter metrics.

## `./tools/graphiti_admin.py doctor`

Deeper check of the repo overlay:
- required hook events;
- project `.mcp.json` contract;
- `autoMemoryEnabled: false`;
- runtime readiness;
- registry collisions.

## `./tools/graphiti_admin.py flush`

Manual flush of pending memory payloads.

## `./tools/graphiti_admin.py requeue`

Returns archived or dead-letter payloads back into the queue.

## `./tools/graphiti_admin.py migrate-logical-id`

Updates the logical group id and, when needed, the storage id.
