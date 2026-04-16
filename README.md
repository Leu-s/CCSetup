# Claude Code Ecosystem Baseline + Graphiti Overlay

This is a framework for a **consistent Claude Code baseline stack** with a managed **Graphiti memory layer at the repository level**.

It pins down two planes:
- **retained Claude Code ecosystem baseline**: ECC, Context7/GitHub/Sequential Thinking via ECC, context-mode, ui-ux-pro-max-skill, repomix, ccusage;
- **repo-owned overlay**: Graphiti, queue-first Stop/PreCompact hooks, `MEMORY_GROUP_ID`, `GRAPHITI_STORAGE_GROUP_ID`, `codebase-memory-mcp`, repo `CLAUDE.md`, `.claude/settings.json`, `.mcp.json`.

## Recommended install and configuration path

**The recommended install and configuration path is via Claude Code.**

The practical order is:
1. prepare the retained plugin layer once on the machine, or let Claude Code install the repo-declared plugins on the first trusted open;
2. separately take care of operator-local utilities (`repomix`, `ccusage`) and, if you need the full ECC rules surface, install ECC rules via the upstream installer or manual copy;
3. install the `codebase-memory-mcp` binary;
4. bring up Graphiti MCP + backend;
5. bootstrap the specific repo with this package;
6. open the repo in Claude Code and let it pull in the repo `.claude/settings.json` and `.mcp.json`.

## If you are a human and Claude Code will do the main work

Start with this order:
1. [TUTORIAL.md](TUTORIAL.md) — human-facing usage scenario;
2. [QUICKSTART.md](QUICKSTART.md) — the shortest install path;
3. [INSTALL.md](INSTALL.md) — the full install path;
4. [USER-MANUAL.md](USER-MANUAL.md) — day-to-day work and best practices.

The best starter instruction for Claude Code:

```text
Read README.md, TUTORIAL.md, QUICKSTART.md, INSTALL.md and USER-MANUAL.md from this package.
Then prepare the repo according to this framework.
Before any manual steps, briefly tell me exactly what I need to confirm or enter myself.
```

## Supported operator environment

The package targets **Linux, macOS and WSL**.
`bash`, `python3 -m venv` and Docker Compose are described specifically for this environment.
The `systemd` user timers in the package are a Linux/WSL path; on macOS use manual flush or your own scheduler (the package does not ship `launchd`).
Windows-native flow without WSL is not a first-class target for this package.

## What is in the agreed baseline

### Retained ecosystem baseline
- ECC / everything-claude-code
- Context7, GitHub MCP, Sequential Thinking — via ECC
- context-mode
- ui-ux-pro-max-skill
- repomix
- ccusage

### Repo overlay
- Graphiti
- Stop + PreCompact capture flow
- `MEMORY_GROUP_ID`
- `GRAPHITI_STORAGE_GROUP_ID`
- `codebase-memory-mcp`
- repo `.claude/settings.json`, `CLAUDE.md`, `.mcp.json`, hooks and state tree

## What is now the source of truth

- **Repo `.claude/settings.json`** — the canonical location for the repo-declared plugin layer, repo hooks and project behavior.
- **Repo `.mcp.json`** — the canonical location for Graphiti + `codebase-memory-mcp`.
- **Repo `CLAUDE.md`** — working principles, tool priority, memory ids.
- **User/global preinstalls** — only speed up the first run; they are no longer the sole way to reproduce the baseline.

## Important boundary of the retained baseline

The repo `.claude/settings.json` reproduces the **plugin portion** of the retained baseline.
It does **not** install operator-local CLI utilities (`repomix`, `ccusage`) for you, and it does **not** distribute ECC `rules`, because ECC plugins cannot automatically distribute rules.

Practical consequence:
- the Claude Code plugin layer can be pulled in from the repo on the first trusted open;
- `repomix` and `ccusage` remain local CLI utilities;
- for the full ECC rules surface, run the ECC upstream install separately or copy `rules/common` + the language directories you need.

The first plugin install and the first `npx` run may require the network if local caches are still empty.

## What the package actually automates

The package automates:
- bootstrapping repo surfaces;
- a dedicated hook runtime for host-side Graphiti ingest;
- queue-first capture via `Stop` and `PreCompact`;
- a delivery path with retry / archive / dead-letter;
- deterministic mapping `MEMORY_GROUP_ID -> GRAPHITI_STORAGE_GROUP_ID`;
- the repo-declared plugin layer via `extraKnownMarketplaces` + `enabledPlugins`;
- project `.mcp.json` that adds `graphiti-memory` and `codebase-memory-mcp`;
- `codebase-memory-mcp` bootstrap: `auto_index=true` + initial `index_repository` during the install flow;
- admin CLI, baseline doctor, doctor, status, flush and migration flow.

## What the package does not replace

The package does **not** replace upstream installers and does not copy third-party plugin hooks by hand:
- ECC hooks stay in the ECC plugin/install layer;
- context-mode hooks stay in the context-mode plugin layer;
- repo hooks in this package are responsible only for the Graphiti lifecycle and repo env/state.

## The shortest path

```bash
mkdir -p ~/data
unzip /path/to/downloaded-package.zip -d ~/data/
cd ~/data/claude-code-framework-v7-ecosystem-final
```

Then:
1. walk through [QUICKSTART.md](QUICKSTART.md);
2. walk through [INSTALL.md](INSTALL.md);
3. bootstrap the repo;
4. run `./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo`;
5. open the repo in Claude Code.

## What to read next

1. [TUTORIAL.md](TUTORIAL.md)
2. [GLOBAL-BASELINE.md](GLOBAL-BASELINE.md)
3. [STACK-DECISIONS.md](STACK-DECISIONS.md)
4. [QUICKSTART.md](QUICKSTART.md)
5. [INSTALL.md](INSTALL.md)
6. [USER-MANUAL.md](USER-MANUAL.md)
7. [HOOKS.md](HOOKS.md)
8. [OPERATIONS.md](OPERATIONS.md)
9. [CONFIG-REFERENCE.md](CONFIG-REFERENCE.md)
10. [SUPPORT-MATRIX.md](SUPPORT-MATRIX.md)
