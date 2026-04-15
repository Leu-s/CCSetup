# Config reference

## 1. Repo `.claude/settings.json`

Після bootstrap цей файл містить три типи даних:
1. Graphiti hooks;
2. `autoMemoryEnabled: false`;
3. reproducible plugin baseline.

### 1.1 Plugin baseline

```json
{
  "extraKnownMarketplaces": {
    "ecc": {
      "source": { "source": "github", "repo": "affaan-m/everything-claude-code" }
    },
    "context-mode": {
      "source": { "source": "github", "repo": "mksglu/context-mode" }
    },
    "ui-ux-pro-max-skill": {
      "source": { "source": "github", "repo": "nextlevelbuilder/ui-ux-pro-max-skill" }
    }
  },
  "enabledPlugins": {
    "ecc@ecc": true,
    "context-mode@context-mode": true,
    "ui-ux-pro-max@ui-ux-pro-max-skill": true
  }
}
```

Семантика:
- repo settings тепер є канонічним reproducibility layer для **plugin portion** retained baseline;
- user settings можуть лишатися для personal overrides, але не повинні бути єдиним місцем plugin baseline;
- plugins still require trust / install flow Claude Code client-а;
- ECC `rules`, `repomix` і `ccusage` цим JSON не встановлюються автоматично.

### 1.2 Graphiti hook events

- `InstructionsLoaded`
- `SessionStart`
- `CwdChanged`
- `FileChanged`
- `PreCompact`
- `Stop`
- `ConfigChange`

## 2. Repo `.mcp.json`

Після bootstrap `.mcp.json` містить:

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "type": "http",
      "url": "${GRAPHITI_MCP_ENDPOINT:-http://127.0.0.1:8000/mcp/}"
    },
    "codebase-memory-mcp": {
      "command": "${CODEBASE_MEMORY_MCP_BIN:-codebase-memory-mcp}",
      "args": []
    }
  }
}
```

Правила:
- не додавай сюди `context7`, `github`, `sequential-thinking`, якщо вони вже приходять через ECC;
- `codebase-memory-mcp` додається як project-scoped structural backend;
- Graphiti MCP може використовувати `headers` / `headersHelper` для remote auth, і bootstrap не повинен їх затирати.

## 2.1 Важлива межа ECC

ECC plugin layer і ECC rules surface — різні речі.
Plugin settings у `.claude/settings.json` не розносять `rules` автоматично. Якщо хочеш повний ECC rules surface, став його через upstream ECC installer або копіюй `rules/common` + потрібні мовні директорії окремо.

## 3. Repo `CLAUDE.md`

Шаблон містить:
- working principles;
- tool priority;
- `MEMORY_GROUP_ID`;
- `GRAPHITI_STORAGE_GROUP_ID`;
- Graphiti memory contract.

## 4. `codebase-memory-mcp` bootstrap policy

Пакет очікує manual binary install, але first-run activation тепер автоматизована:
- `tools/configure-codebase-memory.sh`
- `codebase-memory-mcp config set auto_index true`
- `codebase-memory-mcp cli index_repository '{"repo_path":"..."}'`

### Override

Щоб пропустити первинний індекс під час install flow:
```bash
export CODEBASE_MEMORY_MCP_SKIP_INITIAL_INDEX=1
```

## 5. Graphiti runtime config

Основний конфіг: `templates/project/.claude/graphiti.json`

Ключові секції:
- `engine.backend`: `neo4j` або `falkordb`
- `engine.provider`: `openai`, `openai_generic`, `gemini`
- `mcp.endpoint`
- `mcp.healthUrl`
- `groupIds.*`
- `queue.*`
- `runtime.*`

## 6. Важливі invariants

- `Graphiti` — canonical long-term memory.
- `codebase-memory-mcp` — canonical structural code layer.
- `autoMemoryEnabled` у project settings має бути `false`.
- repo settings не повинні дублювати ECC plugin hooks.
