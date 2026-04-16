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
- Python 3.10+ with the `venv` module available
  - Debian/Ubuntu: `sudo apt install python3-venv`
  - macOS (Homebrew or python.org Python): included by default
  - verify with `python3 -m venv --help` before continuing
- Git
- Docker + Docker Compose for the live Graphiti backend
- Node.js / `npx` for `repomix`, `ccusage` and the plugin ecosystem

## 1.5 Baseline user settings (required)

These are operator-level, not repo-level — they affect Claude Code across every project, not just the bootstrapped repo. Skipping this section means hitting a class of avoidable errors later (wrong timeouts, shell exec in skills, ECC `memory` MCP sneaking back in after a plugin update), so it is part of the baseline install.

Edit `~/.claude/settings.json`:

```json
{
  "model": "claude-opus-4-6",
  "effortLevel": "high",
  "showThinkingSummaries": true,
  "disableSkillShellExecution": true,
  "cleanupPeriodDays": 14,
  "permissions": {
    "deny": ["mcp__memory"]
  },
  "disabledMcpjsonServers": ["memory"],
  "env": {
    "API_TIMEOUT_MS": "600000",
    "BASH_DEFAULT_TIMEOUT_MS": "300000",
    "BASH_MAX_TIMEOUT_MS": "900000",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
  }
}
```

Keys used here:
- `model`, `effortLevel` (values: `low` / `medium` / `high`) — default reasoning profile.
- `showThinkingSummaries` — expose extended-thinking summaries in the UI.
- `disableSkillShellExecution` — must be a **boolean**, not a string; disables auto-run of shell snippets emitted by skills.
- `cleanupPeriodDays` — how long Claude Code keeps session logs before cleanup.
- `permissions.deny: ["mcp__memory"]` — blocks tool calls against any `memory` MCP server, including ECC's plugin-scope one which cannot be removed without uninstalling the ECC plugin.
- `disabledMcpjsonServers: ["memory"]` — a complementary barrier that rejects any `memory` server declared in `.mcp.json`, catching project-scope or future re-registration.
- `API_TIMEOUT_MS` / `BASH_DEFAULT_TIMEOUT_MS` / `BASH_MAX_TIMEOUT_MS` — raise default timeouts for long-running MCP calls and bash tasks.
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1` — opt out of optional telemetry.

Restart Claude Code after editing for the new keys to take effect. Existing sessions use the config snapshot from when they started.

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

Each entry in `extraKnownMarketplaces` has a `source` object whose `ref` field pins the marketplace to a specific upstream tag, branch, or commit. Example shape:

```json
{
  "extraKnownMarketplaces": {
    "everything-claude-code": {
      "source": { "source": "github", "repo": "affaan-m/everything-claude-code", "ref": "vX.Y.Z" }
    }
  }
}
```

Pinning is the difference between a reproducible bootstrap and "it worked on my machine last Tuesday" — unpinned marketplaces silently move when the upstream repo pushes a new commit, and a seeded repo can drift between operators without any local change.

The seeded baseline ships with known-good `ref` values; re-run `baseline-doctor` after the bootstrap to confirm the marketplace/plugin layer matches expectations. When you want a newer tag, update the `ref` inside the matching `source` block deliberately and re-run `/reload-plugins` (or re-bootstrap).

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

**After §3.2 or §3.2a: jump to §3.5 to disable the ECC `memory` MCP before continuing.** ECC registers it during plugin install; if you move on through §3.3–§3.4 without disabling it, you bootstrap a repo with two live memory backends.

### 3.3 ECC rules (required)
ECC's plugin install does not auto-distribute `rules` — that surface lives separately in the ECC repo and must be installed with ECC's own installer. Run it once per machine:

```bash
git clone https://github.com/affaan-m/everything-claude-code.git ~/data/everything-claude-code
cd ~/data/everything-claude-code
npm install
./install.sh --profile full
```

After this, `baseline-doctor` (step §10) treats the rules surface as present. If you deliberately want a narrower rules set, copy `rules/common` plus the language directories you need into `~/.claude/rules/` or into the project `.claude/rules/` instead of running `--profile full`; skipping rules entirely is not a supported configuration for this framework.

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

### 3.5 Disable the ECC `memory` MCP

The ECC bundle registers a `memory` MCP during its install. It duplicates Graphiti's role in this framework and must be off before you bootstrap any repo. Run this immediately after §3.2 or §3.2a:

```bash
claude mcp remove memory
claude mcp list | grep -i memory   # should now show no `memory` server
```

ECC registers its `memory` server at **plugin scope**, which cannot be removed via `claude mcp remove` without uninstalling the ECC plugin entirely. Three barriers catch the condition at different layers:

1. `permissions.deny: ["mcp__memory"]` in `~/.claude/settings.json` (§1.5) blocks every tool call against the `memory` server by tool-name prefix, including ECC's plugin-scope one. This is the only barrier that applies while ECC is installed. The server connection may still appear in `/mcp` output, but its tools will refuse to run.
2. `disabledMcpjsonServers: ["memory"]` in `~/.claude/settings.json` (§1.5) rejects any `memory` server declared in a `.mcp.json` — project or user — so a plugin update, an ECC reinstall, or a future bootstrap cannot sneak it in through that path.
3. `claude mcp remove memory` cleans up user-scope or project-scope `memory` entries if they exist (it does not affect plugin-scope). Run it once to catch any leftover entry from before the baseline was established:
   ```bash
   claude mcp remove memory --scope user 2>/dev/null || true
   claude mcp remove memory --scope project 2>/dev/null || true
   claude mcp list | grep -i 'memory'
   # Expected: only `plugin:everything-claude-code:memory` remains, and it is
   # neutralized by step 1 above.
   ```

Running two long-term memory backends at once produces split state and drifting recall across sessions — `baseline-doctor` flags this condition as `graphiti_overlap_mcps_in_repo` (error) or `graphiti_overlap_mcps_in_user_scope` / `graphiti_overlap_mcps_from_plugins` (warnings).

### 3.6 Adding user-scope MCPs

Once §3.2 is done, ECC already provides these MCPs at plugin scope: `github`, `context7`, `sequential-thinking`, `exa`, `playwright`. You do not need to re-add them.

This section is for the case where you want to add a different MCP at user scope (available in every project) or override an ECC-provided one with your own credentials. Example shape for an HTTP MCP with header auth:

```bash
read -rs -p "API_KEY: " MCP_API_KEY && export MCP_API_KEY
claude mcp add --scope user --transport http <name> \
  https://example.invalid/mcp \
  --header "x-api-key: ${MCP_API_KEY}"
```

Prefer header-based auth when the server supports it, so the key does not end up in URLs, process listings (`ps`), or `claude mcp list` output. If the server only accepts URL-embedded auth (`?apiKey=...`), redact the key before sharing any output or screenshots — the URL form is visible to anyone who inspects the user-scope MCP state.

Using `read -rs` instead of pasting `export KEY="..."` keeps the key out of your shell history (`~/.bash_history`, `~/.zsh_history`) even if `HISTCONTROL` is not configured.

Scope precedence in Claude Code is **local > project > user > plugin**. Keep each MCP at exactly one scope — multiple scopes cause conflicting approvals and split state. If you override an ECC-provided MCP at user scope, the user-scope entry wins; the plugin-scope entry is not disabled, but also not used.

Do not add `graphiti-memory` or `codebase-memory-mcp` at user scope: they are intentionally project-scoped and live in the bootstrapped repo's `.mcp.json`, so that project approval is distinct per repo.

## 4. Install the `codebase-memory-mcp` binary without auto-configuration

```bash
curl -fsSL https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh | bash -s -- --skip-config
```

**Supply-chain note:** this pipes a remote script directly into `bash` from an unpinned `main` branch. Inspect the script before running it (`curl -fsSL ... | less`) and consider pinning to a released tag once the upstream project publishes them. The same applies to any `curl | bash` pattern in the rest of this guide.

If the binary is not on PATH:
```bash
export CODEBASE_MEMORY_MCP_BIN="/absolute/path/to/codebase-memory-mcp"
```

Make sure the resolved path is not world-writable — a writable binary location lets a local attacker swap the executable.

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

**Secret hygiene:** this file lives at `~/.claude/` by design — outside the repo tree. Do not commit it, symlink it back into the repo, or sync it via git. Shipped Compose stacks load it via `${HOME}/.claude/graphiti.neo4j.env` with `required: false`, so a missing file does not break `docker compose config` (env defaults take over).

### FalkorDB
```bash
cp ops/env/graphiti.falkordb.env.example ~/.claude/graphiti.falkordb.env
chmod 600 ~/.claude/graphiti.falkordb.env
```

Fill in at minimum:
- `OPENAI_API_KEY` or `GOOGLE_API_KEY`
- leave `SEMAPHORE_LIMIT=1`
- change `GRAPHITI_MCP_CONFIG_PATH` if needed

**Secret hygiene:** same rule as Neo4j — the file lives at `~/.claude/`, never symlinked or committed.

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

These exports must be live in the same shell used to run §9 (bootstrap) and §10 (verification). If you open a new terminal later, repeat this step — `graphiti_admin.py` reads from the process environment, not from the repo.

**Prefer sourcing the env file from §6 to avoid leaking keys into shell history:**

```bash
set -a
. ~/.claude/graphiti.neo4j.env      # or graphiti.falkordb.env
set +a
```

`set -a` / `set +a` exports every variable defined in the file for the duration of the shell. The file already contains `OPENAI_API_KEY` / `GOOGLE_API_KEY`, `NEO4J_PASSWORD`, and the defaults from §6. Then export the host-side runtime values below that are not in the env file.

The literal `export KEY="..."` blocks below are reference templates for the variables the host runtime expects. If you paste them directly, your shell will record the key in `~/.bash_history` / `~/.zsh_history` unless you have `HISTCONTROL=ignorespace` and prefix each export with a space.

### Neo4j + OpenAI
```bash
export OPENAI_API_KEY="..."
export GRAPHITI_MCP_ENDPOINT="http://127.0.0.1:8000/mcp/"
export GRAPHITI_HEALTH_URL="http://127.0.0.1:8000/health"
export NEO4J_URI="bolt://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-demodemo}"  # override the demo default in production
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

## 9.5 Schedule flush (required)

Async delivery on session `Stop` covers the happy path, but scheduled flush is the safety net that catches retries after network failures, flushes repos with no recent sessions, and ensures that a single Claude Code quit does not leave a spool undrained. Pick one path and wire it up:

### Linux / WSL via systemd
Install user units from `ops/systemd/`. See [OPERATIONS.md](OPERATIONS.md) §5.1 for the `systemd-escape` / `systemctl --user enable` sequence.

### Cross-platform via cron
Install the wrapper at `~/.claude/hooks/graphiti-flush-cron.sh` and add a crontab entry. See [OPERATIONS.md](OPERATIONS.md) §5.2 for the full wrapper script and a sample crontab.

### macOS-specific requirement
`/usr/sbin/cron` does not have access to `~/.claude/**` by default on modern macOS. Without **Full Disk Access** (FDA), cron runs but silently cannot read the env file, repos list, or state directories — delivery fails without producing visible errors.

Grant FDA:
1. open `System Settings → Privacy & Security → Full Disk Access`;
2. press `+`, use Cmd+Shift+G, add `/usr/sbin/cron`;
3. toggle it on;
4. also add the terminal app used to edit crontab (Terminal.app / iTerm), otherwise the edit saves but execution still cannot see protected paths.

Verify: after the first scheduled fire, `~/.claude/logs/graphiti-flush-cron.log` should contain a `flush <repo>` line and no `Permission denied` / `Operation not permitted` messages.

## 10. Check install state

For a consolidated verification sequence with expected output per command, see [POST-INSTALL-CHECKLIST.md](POST-INSTALL-CHECKLIST.md).

The short version:

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
