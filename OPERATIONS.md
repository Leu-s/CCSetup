# Operations

## 1. Baseline checks

```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
./tools/graphiti_admin.py status /absolute/path/to/repo
./tools/graphiti_admin.py doctor /absolute/path/to/repo
```

## 2. Queue operations

```bash
./tools/graphiti_admin.py flush /absolute/path/to/repo --limit 20
./tools/graphiti_admin.py requeue /absolute/path/to/repo --source dead-letter --limit 20
```

## 3. What this repo runtime does not manage

Global/plugin lifecycle for:
- ECC
- context-mode
- ui-ux-pro-max-skill

These are managed by the Claude Code plugin system or upstream installers.

## 4. What this repo runtime now manages

- Graphiti repo overlay
- queue / ledger / archive / dead-letter
- repo-declared plugin baseline
- `codebase-memory-mcp` first-run bootstrap

## 5. Scheduler boundary

The package does not mandate a specific scheduler, but it describes two recommended paths: systemd on Linux/WSL and cron on any Unix-like system (macOS, Linux, WSL).

### 5.1 Linux / WSL via systemd

Unit templates live under `ops/systemd/`:
- `graphiti-flush@.service` invokes `./.claude/hooks/run_python.sh graphiti_flush.py --limit 50` in the given repo;
- `graphiti-flush@.timer` fires every 2 minutes (`OnUnitActiveSec=2m`) after the initial start via `OnBootSec=1m`.

Install as user units (instance name is the escaped absolute path to the repo, see `systemd-escape`).

### 5.2 Cross-platform via cron

If systemd is unavailable (macOS, minimal Linux images without user-systemd), a cron wrapper provides the same shape across all supported platforms.

Shape of the wrapper script `~/.claude/hooks/graphiti-flush-cron.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# 1. Where the ccsetup clone itself lives — the admin CLI runs from here.
CCSETUP_DIR="${CCSETUP_DIR:-$HOME/src/ccsetup}"

# 2. Secrets and env for graphiti_core: chmod 600, contains OPENAI_API_KEY,
#    NEO4J_PASSWORD, NEO4J_URI, GOOGLE_API_KEY, etc.
ENV_FILE="${GRAPHITI_CRON_ENV_FILE:-$HOME/.claude/graphiti.neo4j.env}"

# 3. Repo list, one absolute path per line; # comments and blank lines are ignored.
REPOS_LIST="${GRAPHITI_CRON_REPOS_LIST:-$HOME/.claude/hooks/graphiti-flush-repos.list}"

# 4. Cron-specific log in a stable state directory.
LOG_DIR="${GRAPHITI_CRON_LOG_DIR:-$HOME/.claude/state}"
LOG_FILE="$LOG_DIR/cron-flush.log"
mkdir -p "$LOG_DIR"

# Load env (chmod 600).
if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
fi

cd "$CCSETUP_DIR"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

while IFS= read -r repo || [ -n "$repo" ]; do
  case "$repo" in ""|\#*) continue ;; esac
  echo "[$(timestamp)] flush $repo" >> "$LOG_FILE"
  ./tools/graphiti_admin.py flush "$repo" --limit 50 >> "$LOG_FILE" 2>&1 || \
    echo "[$(timestamp)] flush failed for $repo (rc=$?)" >> "$LOG_FILE"
done < "$REPOS_LIST"
```

What it does:
- loads env from `~/.claude/graphiti.neo4j.env` (chmod 600, containing `OPENAI_API_KEY`, `NEO4J_PASSWORD`, `NEO4J_URI`, and optionally `GOOGLE_API_KEY`);
- iterates the repo list from `~/.claude/hooks/graphiti-flush-repos.list` (one absolute path per line, `#` comments and empty lines are skipped);
- runs `./tools/graphiti_admin.py flush <repo> --limit 50` for each repo;
- writes a per-run log to `~/.claude/state/cron-flush.log` (stdout+stderr per repo).

Example contents of `~/.claude/hooks/graphiti-flush-repos.list`:

```text
# One absolute repo path per line.
/Users/you/src/verbalium-mobile-app
/Users/you/src/ccsetup
```

Example crontab (every 15 minutes):

```cron
*/15 * * * * ~/.claude/hooks/graphiti-flush-cron.sh >> ~/.claude/state/cron-flush.log 2>&1
```

Permissions and order:
- `chmod +x ~/.claude/hooks/graphiti-flush-cron.sh`;
- `chmod 600 ~/.claude/graphiti.neo4j.env`;
- `crontab -e` to add the line above.

### 5.3 macOS Full Disk Access requirement

On modern macOS, `/usr/sbin/cron` itself does not have access to the user's private directories (including `~/.claude/**` and many repos under `~/Documents`, `~/Desktop`, and external volumes). Without Full Disk Access (FDA), a cron job silently fails when reading protected paths — `cron` itself runs, but the wrapper cannot see the env file, repos list, or `.claude/state/`, and delivery does not happen silently.

How to enable FDA for cron:

1. open `System Settings → Privacy & Security → Full Disk Access`;
2. press `+` and via Cmd+Shift+G add `/usr/sbin/cron`;
3. toggle `cron` on;
4. if you edit crontab via `crontab -e`, the terminal (Terminal.app / iTerm) must also be in FDA — otherwise the edit will save, but execution will not see protected paths.

Verification: after the first cron fire, the log `~/.claude/state/cron-flush.log` should contain a `flush <repo>` line and should not contain `Permission denied` / `Operation not permitted`.

### 5.4 Async flush via `Stop` hook

An alternative to cron/systemd for latency-sensitive setups is `queue.asyncFlushOnStop=true` in `.claude/graphiti.json`. With it, `Stop` spawns a detached flush subprocess itself after spooling (see `HOOKS.md` §6 and `CONFIG-REFERENCE.md` §5). This is suitable if you want to see session summaries in Neo4j almost immediately without an external scheduler. Cron still remains useful as a safety net for retries after network failures and for repos that have not had sessions in a while.

### 5.5 Scheduler boundary (EN)

The package does not mandate a specific scheduler. Two supported paths:

- **Linux / WSL via systemd** — templates in `ops/systemd/` (`graphiti-flush@.service` + `graphiti-flush@.timer`, 2-minute interval).
- **Cross-platform via cron** — wrapper at `~/.claude/hooks/graphiti-flush-cron.sh` (shape above) that loads `~/.claude/graphiti.neo4j.env`, iterates `~/.claude/hooks/graphiti-flush-repos.list`, runs `./tools/graphiti_admin.py flush <repo> --limit 50` per entry, and logs to `~/.claude/state/cron-flush.log`. Sample crontab: `*/15 * * * * ~/.claude/hooks/graphiti-flush-cron.sh >> ~/.claude/state/cron-flush.log 2>&1`.

On macOS, `/usr/sbin/cron` must be granted Full Disk Access via `System Settings → Privacy & Security → Full Disk Access`. Without FDA, the cron process runs but cannot read protected paths (env file, repos list, `.claude/state/**`), and flushes fail silently. The terminal app used to edit crontab should also have FDA.

As a latency-sensitive alternative, enable `queue.asyncFlushOnStop=true` in `.claude/graphiti.json` so the `Stop` hook spawns a detached flush off the session-end critical path — see `HOOKS.md` and `CONFIG-REFERENCE.md`. Cron still helps as a safety net for retries and cold repos.
