# Global baseline

This is the retained baseline that must be available for every repo. It consists of **four distinct layers**, and they should not be mixed:
- **repo-declared plugin layer** — via this package's `.claude/settings.json`;
- **ECC rules surface** — a separate upstream-owned layer that the plugin system does not distribute automatically;
- **user-scope MCP tools** — `serena` for LSP-backed symbolic navigation and symbolic edits;
- **operator-local utilities** — `repomix` and `ccusage`.

## 1. Repo-declared plugin layer — the canonical path for the plugin portion

After bootstrap, the repo `.claude/settings.json` already contains:
- `extraKnownMarketplaces` for:
  - `ecc` → `affaan-m/everything-claude-code`
  - `context-mode` → `mksglu/context-mode`
  - `ui-ux-pro-max-skill` → `nextlevelbuilder/ui-ux-pro-max-skill`
- `enabledPlugins` for:
  - `ecc@ecc`
  - `context-mode@context-mode`
  - `ui-ux-pro-max@ui-ux-pro-max-skill`

Consequence:
- a fresh clone gets the same plugin contract;
- cloud sessions can pull in the plugin-portion baseline from the repo;
- user-scoped plugin installs are no longer the only source of truth for the plugin layer.

## 2. User preinstall — first-open convenience for the local machine

### ECC
```text
/plugin marketplace add https://github.com/affaan-m/everything-claude-code
/plugin install ecc@ecc
/reload-plugins
```

Fallback via the upstream installer:
```bash
git clone https://github.com/affaan-m/everything-claude-code.git ~/data/everything-claude-code
cd ~/data/everything-claude-code
npm install
./install.sh --profile full
```

### context-mode
```text
/plugin marketplace add mksglu/context-mode
/plugin install context-mode@context-mode
/reload-plugins
/context-mode:ctx-doctor
```

### ui-ux-pro-max-skill
```text
/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
/plugin install ui-ux-pro-max@ui-ux-pro-max-skill
/reload-plugins
```

## 3. ECC rules surface — the separate required layer for full ECC

The ECC plugin does not distribute `rules` automatically. If you want the full ECC rules surface, run the upstream install:

```bash
git clone https://github.com/affaan-m/everything-claude-code.git ~/data/everything-claude-code
cd ~/data/everything-claude-code
npm install
./install.sh --profile full
```

An alternative is to copy `rules/common` and the needed language directories into `~/.claude/rules/` or the project `.claude/rules/`.

## 4. User-scope MCP tools

### serena
Serena is the LSP-backed symbolic-navigation and symbolic-edit surface. It is distinct from `codebase-memory-mcp` (relationship-graph reads) and from Graphiti (cross-session memory). Required flags: `--context claude-code` (auto-excludes tools overlapping with Claude Code's built-ins), `--mode no-memories` (disables Serena's memory surface so Graphiti stays canonical).

```bash
uv tool install -p 3.13 serena-agent@1.1.2 --prerelease=allow
claude mcp add --scope user serena -- \
  serena start-mcp-server \
    --context claude-code \
    --mode no-memories \
    --project-from-cwd
```

See [INSTALL.md](INSTALL.md) §4.5 for environment variables, LSP language server notes, and verification.

## 5. Operator-local utilities

### repomix
```bash
npx repomix@latest
```
Or:
```bash
npm install -g repomix
```

### ccusage
```bash
npx ccusage@latest
```
Or:
```bash
npm install -g ccusage
```

## 6. What ECC covers

ECC brings in:
- Context7
- GitHub MCP
- Sequential Thinking

Do not duplicate them in the repo `.mcp.json`.

## 7. How to verify the baseline

After bootstrapping a specific repo:
```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
```

This check shows:
- whether repo settings declare the retained plugin baseline;
- whether `.mcp.json` does not duplicate ECC-provided MCPs;
- whether `repomix` and `ccusage` are invocable directly or via `npx`;
- whether `codebase-memory-mcp` resolves;
- whether a local plugin cache is already present, or the plugin layer currently exists only as a repo declaration;
- whether ECC `rules` are already present locally or in the repo;
- whether `repomix` and `ccusage` are available directly or only via `npx`.

The first plugin install and the first `npx` run may require network access if local caches are still empty.
