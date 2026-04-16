# Quickstart

This is the shortest working path for the agreed stack.

If you want Claude Code to do the install instead of doing it by hand, first open [TUTORIAL.md](TUTORIAL.md) and then give Claude Code the instruction from section 4.

## 1. Unpack the package

```bash
mkdir -p ~/data
unzip /path/to/downloaded-package.zip -d ~/data/
cd ~/data/claude-code-framework-v7-ecosystem-final
```

## 2. Prepare the retained baseline

### Plugin portion
The repo still declaratively carries the plugin layer via `.claude/settings.json`:
- `everything-claude-code@everything-claude-code` (ECC bundle)
- `context-mode@context-mode`
- `ui-ux-pro-max@ui-ux-pro-max-skill`

Warning: the ECC bundle ships a `memory` MCP — **do not use it**. Graphiti is the canonical long-term memory layer in this framework; rationale is in [USER-MANUAL.md](USER-MANUAL.md).

Disable it immediately after plugin install:

```bash
claude mcp remove memory
```

Add `disabledMcpjsonServers: ["memory"]` to `~/.claude/settings.json` as a second barrier. See [INSTALL.md](INSTALL.md) §3.5 for details.

### Local operator utilities
These must be available:
- `repomix` or `npx`
- `ccusage` or `npx`

### Important ECC boundary
Repo-declared plugins do not distribute ECC `rules` automatically. If you want the full ECC rules surface, run the upstream ECC install once or copy `rules/common` + the language directories you need. Details are in [INSTALL.md](INSTALL.md).

## 3. Install the `codebase-memory-mcp` binary without auto-configuration

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash -s -- --skip-config
```

If the binary is not on PATH, set:
```bash
export CODEBASE_MEMORY_MCP_BIN="/absolute/path/to/codebase-memory-mcp"
```

## 3a. Install Serena (LSP-backed symbolic navigation and edits)

`serena` covers a distinct role from `codebase-memory-mcp`: symbol-level LSP navigation and atomic refactors. It is not a duplicate. See [INSTALL.md](INSTALL.md) §4.5 for full details.

```bash
uv tool install -p 3.13 serena-agent@1.1.2 --prerelease=allow
claude mcp add --scope user serena -- \
  serena start-mcp-server \
    --context claude-code \
    --mode no-memories \
    --project-from-cwd
```

The `--mode no-memories` flag is mandatory: Graphiti is the canonical long-term memory layer, and running Serena without `no-memories` would expose a second memory backend.

## 4. Prepare the Graphiti env

```bash
cp ops/env/graphiti.neo4j.env.example ~/.claude/graphiti.neo4j.env
chmod 600 ~/.claude/graphiti.neo4j.env
```

In `~/.claude/graphiti.neo4j.env`, fill in at minimum:
- `OPENAI_API_KEY` or `GOOGLE_API_KEY`
- `NEO4J_PASSWORD`, if you do not want the demo default `demodemo`

## 5. Bring up Graphiti MCP + Neo4j

```bash
cd ops
docker compose -f docker-compose.graphiti-neo4j.yml up -d
cd ..
```

## 6. Add shell env for the host runtime

```bash
export OPENAI_API_KEY="..."
export GRAPHITI_MCP_ENDPOINT="http://127.0.0.1:8000/mcp/"
export GRAPHITI_HEALTH_URL="http://127.0.0.1:8000/health"
export NEO4J_URI="bolt://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="demodemo"
```

## 7. Bootstrap the repo

```bash
./tools/install-graphiti-stack.sh /absolute/path/to/repo \
  --backend neo4j \
  --provider openai \
  --logical-group-id verbalium/mobile-app
```

What happens automatically:
- repo surfaces are bootstrapped;
- runtime install;
- the repo-declared plugin layer lands in `.claude/settings.json`;
- `graphiti-memory` + `codebase-memory-mcp` land in `.mcp.json`;
- `codebase-memory-mcp config set auto_index true`;
- an initial `codebase-memory-mcp cli index_repository` for this repo.

## 8. Check state

For a consolidated verification sequence with expected output per command and common failure remedies, see [POST-INSTALL-CHECKLIST.md](POST-INSTALL-CHECKLIST.md).

Quick smoke test:

```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
./tools/graphiti_admin.py status /absolute/path/to/repo
./tools/graphiti_admin.py doctor /absolute/path/to/repo
```

Expected:
- `.claude/settings.json` contains `extraKnownMarketplaces` + `enabledPlugins` for the retained baseline;
- `.mcp.json` contains `graphiti-memory` and `codebase-memory-mcp`;
- `CLAUDE.md` contains working principles and memory ids;
- `.claude/settings.json` contains the Graphiti hook events;
- the runtime stamp exists;
- `doctor.direct_ingest.ready` equals `true`.

## 9. Open the repo in Claude Code

In Claude Code you need to:
1. open the repo root;
2. make sure Claude sees the repo `.claude/settings.json` and `.mcp.json`;
3. accept marketplace/plugin prompts if Claude shows them;
4. approve project MCP servers if approvals are enabled;
5. run `/reload-plugins` if you just installed plugins in a live session.

After that:
- ECC provides the baseline harness;
- context-mode cuts down noise from MCP output;
- `SessionStart` provides a local memory checkpoint;
- `Stop` and `PreCompact` capture summaries into the queue;
- `codebase-memory-mcp` already has `auto_index=true` and an initial index;
- `serena` is available for symbol-level LSP navigation and atomic refactors alongside `codebase-memory-mcp`;
- Graphiti MCP tools are available for manual recall/search.

Note: the first plugin install and the first `npx` run may require the network if local caches are still empty.


## 10. What to tell Claude Code after the first open of the repo

Once the repo is open in Claude Code, the most convenient thing is to give one of these instructions.

### Gather context and start working

```text
Check baseline-doctor, status and doctor for this repo.
Explain the result to me briefly, then start working, using codebase-memory-mcp for code structure, Graphiti for continuity and Context7 for up-to-date documentation.
```

### Continue previous work

```text
First pick up the memory checkpoint of this repo, check Graphiti continuity and the structural state of the code, then continue the task.
```

### Explain what is already installed

```text
Explain to me in plain terms what the baseline does in this repo, what the overlay adds, which hooks are active and what is automated without my involvement.
```
