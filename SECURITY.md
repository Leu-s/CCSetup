# Security

## 1. Core principle

The package is designed as a **localhost-first** memory stack.
This now matches both the documentation and the shipped Compose defaults:
- published ports bind to `127.0.0.1` by default;
- remote exposure must be an explicit, deliberate choice.

## 2. Secrets must live in user env

Do not commit to the repo:
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `NEO4J_PASSWORD`
- bearer tokens for remote MCP
- local `.env` files

Repo surfaces should contain shared config and env expansion, not the secrets themselves.

The canonical runtime env file lives outside the repo: `~/.claude/graphiti.neo4j.env` (or `graphiti.falkordb.env`), `chmod 600`. Shipped Docker Compose stacks load it via `${HOME}/.claude/graphiti.<backend>.env` with `required: false`, so the stack comes up even without the file (using env defaults), and real secrets never land in the repo working tree.

## 3. Project-scoped MCP approvals — not bypass noise, actual protection

`graphiti-memory` lives in the repo `.mcp.json`.
That means Claude Code applies model approval for project-scoped MCP servers.
Do not cheat this model by moving sensitive config into shared files without reason.

## 4. Localhost template vs remote template

### Local template
`templates/project/.mcp.graphiti.fragment.json`

This is a simple localhost HTTP template.
It is a good fit for a local Graphiti stack on the same machine.

### Remote template
For the remote path you must add auth via `.mcp.json`:
- `headers`
- or `headersHelper`

Minimal examples are in:
- `ops/examples/mcp.graphiti.remote-bearer.example.json`
- `ops/examples/mcp.graphiti.remote-headers-helper.example.json`

## 5. Proxy example

`ops/caddy/graphiti.Caddyfile` is a **local reverse-proxy example** without auth.
Do not treat it as a production-ready remote exposure config.

## 6. `.claude/state/` — sensitive local state

It holds:
- summaries of past sessions
- queued payloads
- dead-letter records
- runtime stamp
- logs

Therefore:
- do not commit this tree
- do not sync it via git as shared team memory
- do not expose it to Claude as a regular knowledge corpus without an access policy

## 7. You should deny Claude from reading the raw state tree

In the repo `.claude/settings.json` you can add a deny policy such as:

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

## 8. If you do expose remote MCP externally

Then the following are mandatory:
- auth
- network-level access restriction
- separate password for Neo4j
- separate token for the MCP proxy
- verification that no MCP registration contains a hardcoded secret — project `.mcp.json`, user-scope entries in `~/.claude.json`, or plugin-supplied servers. URL-embedded keys (e.g. `?apiKey=...`) count as hardcoded for this rule.

## 9. Multi-user usage

Shared repo config is fine.
Shared `.claude/state/` across multiple people via git is not.
For a team, split:
- shared repo config
- local operator state
- remote Graphiti backend
