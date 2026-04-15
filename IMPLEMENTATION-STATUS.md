# Implementation status

## Статус

Пакет імплементує свій заявлений scope як **retained Claude Code baseline + automated Graphiti repo overlay**.

Його scope поділений на дві частини:
- **reproducible retained baseline** для Claude Code через repo `.claude/settings.json`;
- **automated repo overlay** для Graphiti memory + `codebase-memory-mcp`.

## Що входить у package scope

### Docs
- `README.md`
- `GLOBAL-BASELINE.md`
- `STACK-DECISIONS.md`
- `QUICKSTART.md`
- `INSTALL.md`
- `USER-MANUAL.md`
- `HOOKS.md`
- `OPERATIONS.md`
- `TROUBLESHOOTING.md`
- `ARCHITECTURE.md`
- `GROUP-ID-POLICY.md`
- `SECURITY.md`
- `CONFIG-REFERENCE.md`
- `CLI-REFERENCE.md`
- `FILE-TREE.md`
- `SUPPORT-MATRIX.md`
- `VALIDATION.md`
- `NO-SCAFFOLDING-AUDIT.md`

### Repo templates
- `templates/project/CLAUDE.md`
- `.claude/graphiti.json`
- `.claude/settings.graphiti.fragment.json`
- `.mcp.graphiti.fragment.json`
- `.claude/rules/graphiti-memory.md`
- `.claude/state/.gitignore`

### Hooks and support libraries
- lifecycle hooks for `InstructionsLoaded`, `SessionStart`, `CwdChanged`, `FileChanged`, `PreCompact`, `Stop`, `ConfigChange`
- admin hooks for `status`, `doctor`, `flush`, `requeue`
- `lib/*` support modules for config, queue, ledger, runtime, ids, capture and observability

### Provisioning and runtime
- `graphiti_bootstrap.py`
- `install-hook-runtime.sh`
- `configure-codebase-memory.sh`
- `install-graphiti-stack.sh`
- `graphiti_admin.py`
- `baseline_doctor.py`
- dedicated repo runtime in `.claude/state/graphiti-runtime`

### Ops surface
- Compose files for Neo4j and FalkorDB
- env examples
- packaged MCP config YAMLs for OpenAI and Gemini
- systemd user timer/service
- remote MCP auth example
- local-only Caddy reverse proxy example

## Що тепер автоматизується кодом

- repo-declared plugin layer (`extraKnownMarketplaces` + `enabledPlugins`)
- Graphiti repo overlay
- `codebase-memory-mcp` first-run bootstrap (`auto_index` + initial index)
- baseline doctor для retained ecosystem contract

## Що свідомо не автоматизується кодом

- реальне interactive plugin download/install усередині Claude Code UI/CLI
- ECC rules install через upstream ECC installer або manual rule copy
- `repomix` / `ccusage` download через `npx`, якщо вони ще не кешовані локально
- interactive project MCP approvals
- зовнішній remote auth login flow

Це не пропуски пакета, а зовнішні runtime boundaries Claude Code.

## Що свідомо лишається поза baseline

- ще один code-graph engine поверх `codebase-memory-mcp`
- ще один behavior plugin поверх принципів, уже вшитих у `CLAUDE.md`
- ще один broad plugin layer, який додає auth/perms surface без критичної потреби
