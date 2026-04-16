# Post-install checklist

This is the consolidated verification sequence to run after [INSTALL.md](INSTALL.md) §9 (bootstrap). It is designed so that a Claude Code session can walk through it top-to-bottom without intermediate reminders and know after each step whether the install is healthy.

If anything below fails, see the remedy line under that step, or jump to [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for details.

Throughout this file, `<repo>` stands for the absolute path to the bootstrapped repo (the one passed to `install-graphiti-stack.sh`). Keep using absolute paths — the admin CLI does not resolve relative paths reliably across hooks and schedulers.

## 1. Retained baseline contract — `baseline-doctor`

```bash
./tools/graphiti_admin.py baseline-doctor <repo>
```

Expected:
- `ok: true`
- `errors: []`
- `repo_services.graphiti_overlap_mcps_in_repo` is empty (no `memory` MCP leaked into the repo `.mcp.json`)
- `local_machine.graphiti_overlap_mcps_in_user_scope` is empty
- `local_machine.graphiti_overlap_mcps_from_plugins` is empty

Common failures:
- `graphiti_overlap_mcps_in_repo: ["memory"]` — ECC `memory` MCP is registered in the repo. To remove it, edit the repo `.mcp.json` and delete the `memory` entry, or run `claude mcp remove memory --scope project` from inside the repo.
- `graphiti_overlap_mcps_in_user_scope: ["memory"]` — same at user scope. Run `claude mcp remove memory --scope user`, or check `~/.claude/settings.json` for a leftover entry.

See [INSTALL.md](INSTALL.md) §3.5 for the removal procedure.

## 2. Repo runtime — `status`

```bash
./tools/graphiti_admin.py status <repo>
```

Expected fields in the returned JSON:
- `group.logical_group_id` matches the `--logical-group-id` passed to `install-graphiti-stack.sh`
- `group.storage_group_id` matches the deterministic `g_<slug>_<hash>` shape
- `group.storage_mismatch: false` and `group.expected_storage_group_id == storage_group_id`
- `queue.spool` / `queue.archive` / `queue.dead_letter` counters present (may all be `0` on a freshly bootstrapped repo)
- `ledger.exists: true`
- `mcp.project_mcp_approval_verifiable_here: false` — correct for CLI context; approval state is only verifiable inside Claude Code
- `.claude/state/graphiti-runtime-stamp.json` exists on disk

Common failures:
- `group.storage_mismatch: true` — `./tools/graphiti_admin.py migrate-logical-id <repo> --mode keep-storage` (or `--mode new-storage` for a fresh namespace). See [GROUP-ID-POLICY.md](GROUP-ID-POLICY.md).
- runtime stamp absent — re-run `./tools/install-hook-runtime.sh <repo>`.

## 3. Memory pipeline — `doctor`

```bash
./tools/graphiti_admin.py doctor <repo>
```

Expected fields in the returned JSON:
- `ok: true` with empty `errors` array
- `direct_ingest.ready: true` and `direct_ingest.missing_env: []` — `graphiti_core` can write to Neo4j directly from the host runtime
- `mcp_http_health.ok: true` — the Graphiti MCP HTTP server answers on `http://127.0.0.1:8000/health`
- `codebase_memory.present: true` and `codebase_memory.resolvable: true` — the `.mcp.json` entry exists and the binary resolves on PATH or via `CODEBASE_MEMORY_MCP_BIN`
- `runtime` block shows the dedicated Python venv is present

Common failures:
- `direct_ingest.ready: false` with `direct_ingest.missing_env: ["OPENAI_API_KEY", ...]` — check `~/.claude/graphiti.neo4j.env`, then re-run the `set -a; . ~/.claude/graphiti.neo4j.env; set +a` block from [INSTALL.md](INSTALL.md) §8 in the terminal where you invoke the admin CLI. The host runtime reads from the process environment, not from the repo.
- `mcp_http_health.ok: false` — the Graphiti MCP container is not up. `cd ops && docker compose -f docker-compose.graphiti-neo4j.yml ps` to check; `docker compose ... up -d` to bring it up; tail `docker compose ... logs graphiti-mcp` for root cause.
- `codebase_memory.present: false` — the `.mcp.json` entry is missing. Re-run `./tools/install-graphiti-stack.sh <repo>` (idempotent) or add the entry manually from the fragment template.
- `codebase_memory.resolvable: false` — the binary is not on `PATH` and `CODEBASE_MEMORY_MCP_BIN` is unset. `export CODEBASE_MEMORY_MCP_BIN="/absolute/path/to/codebase-memory-mcp"` and retry.

## 4. Smoke-test delivery — `flush --limit 1`

```bash
./tools/graphiti_admin.py flush <repo> --limit 1
cat <repo>/.claude/state/graphiti-last-flush.json
```

`graphiti_flush.py` writes results to `.claude/state/graphiti-last-flush.json` rather than stdout. The wrapper exits 0 whether the queue was empty or a payload was delivered. Inspect the JSON for counters.

Expected fields in `graphiti-last-flush.json`:
- `processed`, `delivered`, `retried`, `dead_lettered` — counters for this flush run
- `limit`, `dry_run`, `finished_at` — invocation metadata

On a fresh repo with no queued items: `processed=0, delivered=0`, and the wrapper itself prints nothing (no Python tracebacks). On a repo where `Stop` has already fired at least once: `delivered=1` (or higher), and a new episode node appears in Neo4j for that session.

Common failures (read the relevant traceback in `.claude/state/logs/` if the JSON shows `delivered=0` with a queue that should have had items):
- `ConnectionRefusedError` or `AuthError` on bolt — check `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` in the shell env; confirm the Neo4j container is running (`docker compose -f ops/docker-compose.graphiti-neo4j.yml ps`).
- `openai.AuthenticationError` — `OPENAI_API_KEY` is invalid or expired; check `~/.claude/graphiti.neo4j.env` and the exported shell env. Redact the key prefix before sharing any traceback — `graphiti_core` may include request context in stack traces.

## 5. MCP registration — `claude mcp list` inside the repo

```bash
cd <repo> && claude mcp list
```

Expected:
- `graphiti-memory` (project scope, `http://127.0.0.1:8000/mcp/`)
- `codebase-memory-mcp` (project scope, stdio command)
- **no** `memory` server
- any user-scope MCPs from [INSTALL.md](INSTALL.md) §3.6 (e.g. `exa`) appear under user scope

If any URL-embedded secret was used for a user-scope MCP, `claude mcp list` prints it literally — redact before sharing output.

Common failures:
- `memory` present — see step 1 remedy and [INSTALL.md](INSTALL.md) §3.5.
- `graphiti-memory` missing — `.mcp.json` was not seeded. Re-run the bootstrap.

## 6. Plugin layer

Steps 6–7 require actions outside the CLI. Open the repo in Claude Code first (see [INSTALL.md](INSTALL.md) §11).

Inside an open Claude Code session on the repo:

- `/plugin` shows the three retained plugins as installed and enabled
- `/status` shows `.claude/settings.json` is being loaded from the repo
- `/hooks` lists Graphiti hook events: `SessionStart`, `Stop`, `PreCompact`, `PostCompact`, `PostToolUseFailure`, plus the in-session `InstructionsLoaded` / `CwdChanged` / `FileChanged` triggers

Common failures:
- a plugin is missing — re-run `/plugin install <slug>` from [INSTALL.md](INSTALL.md) §3.2 and `/reload-plugins`.
- hooks not listed — confirm `.claude/settings.json` contains the Graphiti fragment. `baseline-doctor` reports missing hook events as part of the repo contract check.
- `/hooks` is empty immediately after editing settings — restart Claude Code. Settings load once per session start.

## 7. Scheduled flush

Scheduled flush is a required component of the install (see [INSTALL.md](INSTALL.md) §9.5). Verify it landed correctly:


If you enabled systemd, verify:
```bash
systemctl --user status "graphiti-flush@$(systemd-escape --path <repo>).timer"
```
Expected: `active (waiting)`.

If you enabled cron, verify after one schedule window:
```bash
tail -n 20 ~/.claude/logs/graphiti-flush-cron.log
```
Expected: at least one `flush <repo>` line from the scheduled run, no `Permission denied` / `Operation not permitted`.

On macOS, a cron log that stops at "flush" and never produces a line after means `/usr/sbin/cron` does not have Full Disk Access — revisit [INSTALL.md](INSTALL.md) §9.5.

## 8. Summary

If steps 1–5 are green, the install is healthy and you can open the repo in Claude Code. Steps 6–7 are operator-facing checks that live outside what the CLI can self-verify.

When you come back to this repo after a long gap, run only steps 1 and 3 — they are the fastest signal that the Graphiti stack and the baseline contract are still intact.
