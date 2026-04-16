# Troubleshooting

## 1. `baseline-doctor` says the repo plugin baseline is not declared

Check:
- whether bootstrap actually created `.claude/settings.json`;
- whether the file contains `extraKnownMarketplaces` and `enabledPlugins`;
- whether the repo was overwritten by an old manual config copy.

## 2. `baseline-doctor` says `.mcp.json` duplicates ECC MCPs

Remove from the repo `.mcp.json`:
- `context7`
- `github`
- `sequential-thinking`

They must come via ECC.

## 3. `doctor` says `codebase-memory-mcp` is missing or does not resolve

Check:
- whether the binary is installed;
- whether `.mcp.json` contains `codebase-memory-mcp`;
- whether `CODEBASE_MEMORY_MCP_BIN` is set if the binary is not on PATH.

## 4. `codebase-memory-mcp` is not ready on the first session

Check that the install flow ran to completion.

The package should have executed:
```bash
codebase-memory-mcp config set auto_index true
codebase-memory-mcp cli index_repository '{"repo_path":"/absolute/path/to/repo"}'
```

Repeat manually if needed:
```bash
./tools/configure-codebase-memory.sh /absolute/path/to/repo
```

## 5. Context7 / GitHub MCP / Sequential Thinking are not visible

Check:
- whether ECC is installed;
- whether the `everything-claude-code@everything-claude-code` plugin is active;
- whether the repo is trusted and Claude Code picked up the repo-declared plugins;
- whether you disabled ECC in user settings or managed settings.

## 6. Context-mode is not working

In Claude Code:
```text
/context-mode:ctx-doctor
```

Also check:
- whether `context-mode@context-mode` is enabled;
- whether you ran `/reload-plugins` after install.

## 7. The UI/UX skill does not appear

Check:
- whether `ui-ux-pro-max@ui-ux-pro-max-skill` is enabled;
- whether you ran `/reload-plugins` after install.

## 8. There are duplicate hooks or strange double firings

Do not copy ECC plugin hooks by hand into the repo `settings.json`.

The repo hooks of this package must cover only the Graphiti lifecycle.

## 9. `doctor` says Graphiti health is ok but ingest is not ready

This is normally possible because:
- MCP HTTP health and direct ingest are different layers;
- the Graphiti HTTP server can be reachable while the host runtime/env is not yet ready.


## 10. You need a remote MCP with short-lived auth

Use `.mcp.json` with `headersHelper` instead of a hardcoded bearer header.
A ready-made shape is in `ops/examples/mcp.graphiti.remote-headers-helper.example.json`.

## 11. Cron flush on macOS does not deliver episodes

Symptom:
- `~/.claude/state/cron-flush.log` shows access errors or is completely empty, even though `crontab -l` contains the schedule;
- `./tools/graphiti_admin.py status <repo>` reports that pending episodes do not decrease between ticks;
- manual `./tools/graphiti_admin.py flush <repo>` from the shell works correctly.

Root cause:
- on macOS the cron daemon (`/usr/sbin/cron`) by default does not have access to user data directories, bind-mounts, and even `~/.claude/state`. Without Full Disk Access (FDA), scheduled flushes silently fail — hook wrapper files or the ledger are simply inaccessible to the cron process.

Fix:
1. System Settings → Privacy & Security → Full Disk Access.
2. Click `+` and add `/usr/sbin/cron` (Cmd+Shift+G in Finder, enter the path if the binary is not visible).
3. Make sure the toggle next to `/usr/sbin/cron` is on.
4. After the FDA change, macOS will restart cron automatically; no additional reload command is required.

Verification:
- `crontab -l` shows the expected schedule pointing to `~/.claude/hooks/graphiti-flush-cron.sh`;
- `tail -f ~/.claude/state/cron-flush.log` on the next tick shows successful flush summaries (one entry per run, no `Permission denied`);
- `./tools/graphiti_admin.py status <repo>` starts showing a decreasing pending count and a fresh `lastFlush`.

## 12. Stop hook does not trigger async flush

Symptom:
- the queue / spool gradually accumulates payloads after sessions;
- the expected async flush after the `Stop` hook did not run (no fresh entry in `~/.claude/state/cron-flush.log` or in `graphiti-hooks.jsonl`);
- manual `graphiti_admin.py flush <repo>` successfully delivers what accumulated.

Check:
1. In `.claude/graphiti.json`, the `queue` section has `"asyncFlushOnStop": true`. The flag defaults to `false`, so without explicit enablement the `Stop` hook only enqueues and returns control — delivery is left to cron or manual flush (see `CONFIG-REFERENCE.md` §5.1).
2. The hook runtime is installed. `./tools/graphiti_admin.py doctor <repo>` should pass; `.claude/state/graphiti-runtime/` should exist with a working Python.
3. `runtime.pythonExecutable` (or the `GRAPHITI_HOOK_PYTHON` env var) resolves to an executable Python available from the shell that launches Claude Code. If it points at a broken venv, the detached subprocess exits immediately and leaves no logs.
4. The sandbox / shell environment of Claude Code allows detached child processes. In strictly sandboxed shells (for example, corporate wrappers, some IDE integrations) `subprocess.Popen(..., start_new_session=True)` is silently blocked — in that case rely on the cron wrapper `~/.claude/hooks/graphiti-flush-cron.sh` instead of async-on-stop.
