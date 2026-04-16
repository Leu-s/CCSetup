# Security

## 1. Основний принцип

Package задуманий як **localhost-first** memory stack.
Це тепер збігається і з документацією, і з shipped Compose defaults:
- published ports bind-яться до `127.0.0.1` за замовчуванням;
- remote exposure треба робити свідомо.

## 2. Secrets мають жити в user env

Не коміть у repo:
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `NEO4J_PASSWORD`
- bearer tokens для remote MCP
- локальні `.env` файли

Repo surfaces мають містити shared config і env expansion, а не самі секрети.

Canonical runtime env file живе поза repo: `~/.claude/graphiti.neo4j.env` (або `graphiti.falkordb.env`), `chmod 600`. Shipped Docker Compose стеки вантажать його через `${HOME}/.claude/graphiti.<backend>.env` з `required: false`, тому стек піднімається і без файлу (з env defaults), а реальні секрети ніколи не потрапляють у repo working tree.

## 3. Project-scoped MCP approvals — не обхідний шум, а захист

`graphiti-memory` живе в repo `.mcp.json`.
Це означає, що Claude Code застосовує model approval для project-scoped MCP servers.
Не обманюй цю модель тим, що переносиш чутливий конфіг у shared файли без потреби.

## 4. Localhost template vs remote template

### Локальний template
`templates/project/.mcp.graphiti.fragment.json`

Це simple localhost HTTP template.
Він хороший для локального Graphiti stack на тій самій машині.

### Remote template
Для remote path треба додати auth через `.mcp.json`:
- `headers`
- або `headersHelper`

Мінімальні приклади є в:
- `ops/examples/mcp.graphiti.remote-bearer.example.json`
- `ops/examples/mcp.graphiti.remote-headers-helper.example.json`

## 5. Proxy example

`ops/caddy/graphiti.Caddyfile` — це **local reverse-proxy example** без auth.
Його не треба трактувати як готову production remote exposure конфігурацію.

## 6. `.claude/state/` — чутливий локальний стан

Там лежать:
- summaries минулих сесій
- queued payload-и
- dead-letter записи
- runtime stamp
- logs

Тому:
- не коміть це дерево
- не синхронізуй його через git як shared team memory
- не відкривай його Claude як звичайний knowledge corpus без політики доступу

## 7. Варто заборонити читання raw state tree Claude-ом

У repo `.claude/settings.json` можна додати deny policy на кшталт:

```json
{
  "permissions": {
    "deny": [
      "Read(./.claude/state/**)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  }
}
```

## 8. Якщо все ж відкриваєш remote MCP зовні

Тоді обовʼязкові:
- auth
- мережеве обмеження доступу
- окремий пароль до Neo4j
- окремий токен для MCP proxy
- перевірка, що `.mcp.json` не містить hardcoded secrets

## 9. Multi-user usage

Shared repo config допустимий.
Shared `.claude/state/` між кількома людьми через git — ні.
Для команди розводь:
- shared repo config
- local operator state
- remote Graphiti backend
