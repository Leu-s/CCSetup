# Installation

## Supported operator environment

The expected operator environment is **Linux, macOS or WSL**.
The commands below are described for `bash`, `python3 -m venv`, Docker Compose and repo-local shell scripts.
Windows-native shell without WSL is not covered as a first-class path by this package.

## 0. How to read this install flow

The normal model is:
- **you** provide secrets, confirm prompts, and decide which repo to prepare;
- **Claude Code** reads this file and runs the install/bootstrap steps;
- **this package** automates repo surfaces, hooks, memory, and the `codebase-memory-mcp` bootstrap.

During install, only four kinds of manual involvement may be required from you:
- entering API keys or other env secrets;
- confirming plugin install prompts;
- confirming project MCP approvals;
- starting Docker/infrastructure if Claude Code cannot reach it directly.

## 1. Prerequisites

Required:
- Claude Code
- Python 3.10+
- `python3 -m venv`
- Git
- Docker + Docker Compose for the live Graphiti backend
- Node.js / `npx` for `repomix`, `ccusage` and the plugin ecosystem

## 2. Unpack the package

```bash
mkdir -p ~/data
unzip /path/to/downloaded-package.zip -d ~/data/
cd ~/data/claude-code-framework-v7-ecosystem-final
```

## 3. Prepare the retained baseline, and do not mix up its different parts

### 3.1 Repo-declared plugin portion — the canonical path for the plugin layer
The repo bootstrap will itself add into `.claude/settings.json`:
- `extraKnownMarketplaces`
- `enabledPlugins`

for ECC, context-mode and ui-ux-pro-max-skill.

This reproduces the **plugin portion** of the retained baseline on a fresh clone and in cloud sessions, provided there is trust and access to the marketplace source.

### 3.2 For local convenience — install plugins immediately
```text
/plugin marketplace add https://github.com/affaan-m/everything-claude-code
/plugin install everything-claude-code@everything-claude-code
/plugin marketplace add mksglu/context-mode
/plugin install context-mode@context-mode
/plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
/plugin install ui-ux-pro-max@ui-ux-pro-max-skill
/reload-plugins
```

### 3.2a Alternative via the CLI
The same plugin layer can be brought up via the non-interactive `claude` CLI — convenient for scripted bootstrap or a fresh container:
```bash
claude plugin marketplace add https://github.com/affaan-m/everything-claude-code
claude plugin install everything-claude-code@everything-claude-code
claude plugin marketplace add mksglu/context-mode
claude plugin install context-mode@context-mode
claude plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
claude plugin install ui-ux-pro-max@ui-ux-pro-max-skill
```
The slash-command path remains the default for an interactive session; the CLI is an alternative for automation.

### 3.3 ECC rules — a separate required step if you want the full ECC rules surface
The current ECC limitation is this: plugin install does not distribute `rules` automatically. For the full ECC rules surface, take one of the two paths.

The most reliable one:
```bash
git clone https://github.com/affaan-m/everything-claude-code.git ~/data/everything-claude-code
cd ~/data/everything-claude-code
npm install
./install.sh --profile full
```

The alternative is to copy `rules/common` and the language directories you need into `~/.claude/rules/` or into the project `.claude/rules/`.

### 3.4 Local operator utilities
```bash
npx repomix@latest
npx ccusage@latest
```

Important:
- Context7, GitHub MCP and Sequential Thinking arrive via ECC.
- They should not be duplicated with separate repo entries in this framework.
- If ECC is installed as a plugin, do not copy its hooks manually into the repo `settings.json`.
- `repomix` and `ccusage` are not declared in the repo settings; they are operator-local CLI utilities.
- The first plugin install and the first `npx` run may require the network if local caches are still empty.
- ECC bundle ships a `memory` MCP — **do not use it**. Graphiti is the canonical long-term memory layer for this framework. Rationale and the exclusion list are in [USER-MANUAL.md](USER-MANUAL.md).

## 4. Install the `codebase-memory-mcp` binary without auto-configuration

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash -s -- --skip-config
```

If the binary is not on PATH:
```bash
export CODEBASE_MEMORY_MCP_BIN="/absolute/path/to/codebase-memory-mcp"
```

The package will then itself run:
- `codebase-memory-mcp config set auto_index true`
- `codebase-memory-mcp cli index_repository '{"repo_path":"..."}'`

That is, the hidden first-run step no longer stays undocumented.

## 5. Choose a backend for Graphiti

### Canonical baseline
- backend: `neo4j`
- provider: `openai`
- MCP config file: `/graphiti-config/config-docker-neo4j.openai.yaml`

### Lightweight local path
- backend: `falkordb`
- provider: `openai`
- MCP config file: `/graphiti-config/config-docker-falkordb.openai.yaml`
- `SEMAPHORE_LIMIT=1`

### Gemini path
Replace `GRAPHITI_MCP_CONFIG_PATH` with one of:
- `/graphiti-config/config-docker-neo4j.gemini.yaml`
- `/graphiti-config/config-docker-falkordb.gemini.yaml`

### OpenAI-compatible path (`openai_generic`)
`openai_generic` in this package is supported for the **host direct-ingest runtime**.
Packaged MCP Docker configs here are only for `openai` and `gemini`, so for `openai_generic` use:
- a custom remote Graphiti MCP endpoint;
- or your own Graphiti MCP config outside the shipped compose files.

## 6. Prepare the Docker env

### Neo4j
```bash
cp ops/env/graphiti.neo4j.env.example ~/.claude/graphiti.neo4j.env
chmod 600 ~/.claude/graphiti.neo4j.env
```

Fill in at minimum:
- `OPENAI_API_KEY` or `GOOGLE_API_KEY`
- `NEO4J_PASSWORD`
- `GRAPHITI_MCP_CONFIG_PATH` if needed

By default:
- the host bind is `127.0.0.1`
- the demo password is `demodemo`

### FalkorDB
```bash
cp ops/env/graphiti.falkordb.env.example ~/.claude/graphiti.falkordb.env
chmod 600 ~/.claude/graphiti.falkordb.env
```

Fill in at minimum:
- `OPENAI_API_KEY` or `GOOGLE_API_KEY`
- leave `SEMAPHORE_LIMIT=1`
- change `GRAPHITI_MCP_CONFIG_PATH` if needed

## 7. Bring up the Graphiti stack

### Neo4j
```bash
cd ops
docker compose -f docker-compose.graphiti-neo4j.yml up -d
cd ..
```

### FalkorDB
```bash
cd ops
docker compose -f docker-compose.graphiti-falkordb.yml up -d
cd ..
```

## 8. Add shell env for the host direct-ingest runtime

### Neo4j + OpenAI
```bash
export OPENAI_API_KEY="..."
export GRAPHITI_MCP_ENDPOINT="http://127.0.0.1:8000/mcp/"
export GRAPHITI_HEALTH_URL="http://127.0.0.1:8000/health"
export NEO4J_URI="bolt://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="demodemo"
export GRAPHITI_OPENAI_MODEL="gpt-4.1"
export GRAPHITI_OPENAI_SMALL_MODEL="gpt-4.1-mini"
export GRAPHITI_OPENAI_EMBEDDING_MODEL="text-embedding-3-small"
```

### Neo4j + Gemini
```bash
export GOOGLE_API_KEY="..."
export GRAPHITI_MCP_ENDPOINT="http://127.0.0.1:8000/mcp/"
export GRAPHITI_HEALTH_URL="http://127.0.0.1:8000/health"
export NEO4J_URI="bolt://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="demodemo"
```

### FalkorDB + OpenAI
```bash
export OPENAI_API_KEY="..."
export GRAPHITI_MCP_ENDPOINT="http://127.0.0.1:8000/mcp/"
export GRAPHITI_HEALTH_URL="http://127.0.0.1:8000/health"
export FALKORDB_URI="redis://127.0.0.1:6379"
export SEMAPHORE_LIMIT="1"
```

### OpenAI-compatible (`openai_generic`) direct-ingest runtime
```bash
export OPENAI_API_KEY="..."
export GRAPHITI_MCP_ENDPOINT="http://127.0.0.1:8000/mcp/"
export GRAPHITI_HEALTH_URL="http://127.0.0.1:8000/health"
export NEO4J_URI="bolt://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="demodemo"
export GRAPHITI_OPENAI_GENERIC_BASE_URL="https://your-openai-compatible-endpoint.example/v1"
export GRAPHITI_OPENAI_GENERIC_MODEL="your-model-name"
```

### Offline / wheelhouse runtime install
```bash
export GRAPHITI_SKIP_PIP_BOOTSTRAP=1
export GRAPHITI_RUNTIME_PIP_EXTRA_ARGS="--no-index --find-links /absolute/path/to/wheelhouse"
```

## 9. Bootstrap the repo

```bash
./tools/install-graphiti-stack.sh /absolute/path/to/repo \
  --backend neo4j \
  --provider openai \
  --logical-group-id verbalium/mobile-app
```

What bootstrap does:
- creates or updates the repo `CLAUDE.md`;
- adds working principles and tool priority;
- adds `MEMORY_GROUP_ID` and `GRAPHITI_STORAGE_GROUP_ID`;
- adds `graphiti-memory` and `codebase-memory-mcp` to `.mcp.json`;
- adds the Graphiti hook groups to `.claude/settings.json`;
- adds `extraKnownMarketplaces` + `enabledPlugins` for the retained plugin layer;
- installs the repo-owned hook runtime;
- configures `codebase-memory-mcp auto_index=true`;
- runs the initial `index_repository`.

## 10. Check install state

```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
./tools/graphiti_admin.py status /absolute/path/to/repo
./tools/graphiti_admin.py doctor /absolute/path/to/repo
```

How to read the result:
- `baseline-doctor` shows the reproducible plugin layer, repo MCP contract, local invokers, and the state of the ECC rules surface;
- `mcp_http_health` shows the reachability of the Graphiti MCP HTTP server;
- `direct_ingest.ready` shows whether the repo runtime is ready for `graphiti_flush.py`;
- `codebase_memory` shows whether the `codebase-memory-mcp` entry is present and whether its command resolves;
- `project_mcp_approval_verifiable_here: false` means that interactive approval state is verified inside Claude Code itself.

## 11. Open the repo in Claude Code

The order is:
1. open the repo;
2. make sure Claude sees `.claude/settings.json` and `.mcp.json`;
3. accept plugin/marketplace prompts if Claude shows them;
4. approve project MCP servers if Claude Code asks;
5. run `/reload-plugins` if plugins were installed during the current session.

Useful actions in Claude Code:
- `/status` — see which settings layers are actually active;
- `/hooks` — see active hook configurations;
- `/mcp` — see servers and auth state;
- `/skills` — see skills from project, user and plugin sources;
- `claude mcp reset-project-choices` — reset project approvals if a previous choice is in the way.

## 12. What is verified by the package and what is not

Verified locally by the package:
- repo bootstrap;
- runtime install;
- the queue/ledger/archive path;
- the admin CLI path;
- mock ingest and local recall;
- the `codebase-memory-mcp` entry in project `.mcp.json`;
- the repo-declared plugin baseline in `.claude/settings.json`;
- the `codebase-memory-mcp auto_index` + initial `index_repository` install step.

Not presented as already verified in every environment:
- live Docker bring-up here and now, if Docker is unavailable;
- interactive Claude Code marketplace/plugin prompt state;
- interactive Claude Code project approval state;
- a specific provider's remote auth flow without a real login.

## 13. What the human does in the install flow and what Claude Code does

### Human
- unpacks the package or gives Claude Code the path to it;
- provides env secrets;
- confirms plugin / MCP prompts;
- decides which repo to bootstrap.

### Claude Code
- reads the package docs;
- runs the installer;
- checks `baseline-doctor`, `status`, `doctor`;
- then works inside the already-prepared repo, relying on `CLAUDE.md`, `.claude/settings.json` and `.mcp.json`.

### Framework
- creates repo surfaces;
- sets up hooks and the memory pipeline;
- enables the plugin baseline at the repo level;
- brings `codebase-memory-mcp` to ready state on the first repo.
