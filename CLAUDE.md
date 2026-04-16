# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

This is **the framework package itself**, not a project that consumes it. It ships the retained Claude Code ecosystem baseline declaration plus the repo-owned Graphiti memory overlay, and bootstraps them into *other* target repos via `./tools/install-graphiti-stack.sh <target-repo>`. When working here, you are editing the distribution — templates, installers, hooks, docs, and tests — not the output of a bootstrap.

Docs are a mix of Ukrainian and English. The canonical entry is `README.md`; `ARCHITECTURE.md` and `STACK-DECISIONS.md` describe intent and scope boundaries that matter when making changes.

## Commands

Run from repo root.

- **Full test suite** (syntax + JSON/markdown link audit + validator + unit tests, and optionally `systemd-analyze verify` and `docker compose config` if available): `bash tests/run-tests.sh`
- **Package validator only**: `python3 tools/validate-package.py`
- **Syntax/compile pass**:
  - `python3 -m compileall templates/project/.claude/hooks tools tests`
  - `bash -n tools/install-graphiti-stack.sh tools/install-hook-runtime.sh tools/configure-codebase-memory.sh templates/project/.claude/hooks/run_python.sh`
- **Single test**: `python3 tests/test_<name>.py -v` (e.g. `test_group_ids`, `test_bootstrap_hygiene`, `test_baseline_doctor`, `test_admin_wrapper`, `test_e2e_mock`, `test_hook_contracts`, `test_install_flow_offline`)
- **Bootstrap a target repo end-to-end**: `./tools/install-graphiti-stack.sh /absolute/path/to/target-repo --backend neo4j --provider openai --logical-group-id verbalium/mobile-app`
- **Admin CLI against a bootstrapped repo**: `./tools/graphiti_admin.py {baseline-doctor|status|doctor|flush|requeue|migrate-logical-id} /absolute/path/to/target-repo [...]` (see `CLI-REFERENCE.md`)

Supported operator environment is Linux, macOS, or WSL. Windows-native shell without WSL is not a first-class target.

## Architecture: two planes, deliberate boundaries

The package is deliberately split, and the split is enforced by tests (`test_baseline_doctor.py`, `test_bootstrap_hygiene.py`) — do not collapse it:

1. **Retained Claude Code baseline** (ECC, Context7/GitHub/Sequential Thinking via ECC, context-mode, ui-ux-pro-max-skill, repomix, ccusage) — the package only *declares* the plugin portion reproducibly via `extraKnownMarketplaces` + `enabledPlugins` in the seeded repo `.claude/settings.json`. It does **not** install ECC rules, `repomix`, `ccusage`, or the `codebase-memory-mcp` binary. Those are upstream flows, and docs must keep saying so.
2. **Repo-owned overlay** (Graphiti + `codebase-memory-mcp` project entry) — the package *does* automate this, end-to-end: templates, hooks, queue/ledger/archive path, `codebase-memory-mcp` first-run `auto_index=true` + initial `index_repository`, and admin CLI.

Never introduce a second long-term memory engine, a second code-graph layer, or a second behavior plugin; `CLAUDE.md` is where behavior principles live. See `STACK-DECISIONS.md` for the exclusion list.

### Data flow in a bootstrapped repo

`SessionStart` reads the local delivered ledger only (no remote search); in-session `InstructionsLoaded`/`CwdChanged`/`FileChanged` keep env exports current; `Stop`/`PreCompact` enqueue summaries to the local spool + ledger without waiting on network; `graphiti_flush.py` (manual or scheduled) delivers via `graphiti_core`, archives success, retries or dead-letters failures. Mirror this ordering when modifying hooks in `templates/project/.claude/hooks/`.

### Source layout, at the level that requires reading multiple files

- `templates/project/` — what gets seeded into target repos. `CLAUDE.md` (working principles + tool priority + memory IDs), `.claude/settings.graphiti.fragment.json` (hooks + plugin baseline), `.mcp.graphiti.fragment.json` (graphiti-memory + codebase-memory-mcp entries), `.claude/graphiti.json` (runtime config), `.claude/hooks/*` (lifecycle + admin hooks), `.claude/hooks/lib/*` (config, queue_store, ledger, runtime, group_ids, capture, observability, adapters).
- `tools/` — installers and admin. `graphiti_bootstrap.py` seeds/merges repo surfaces; `install-hook-runtime.sh` stands up the dedicated Python runtime under `.claude/state/graphiti-runtime/`; `configure-codebase-memory.sh` does the `codebase-memory-mcp` first-run; `install-graphiti-stack.sh` orchestrates all three; `graphiti_admin.py` shells into the target repo's hook wrapper for `status`/`doctor`/`flush`/`requeue`; `baseline_doctor.py` checks the retained-baseline contract; `validate-package.py` checks package-internal consistency.
- `ops/` — Docker Compose for Graphiti (Neo4j and FalkorDB), env examples, packaged MCP config YAMLs (OpenAI + Gemini; `openai_generic` is host-runtime-only, not shipped as a Compose config), `systemd/` user timer/service for Linux/WSL, Caddy example (local, no auth), remote-MCP auth examples.
- `tests/` — Python `unittest` discovered by `run-tests.sh`. Keep new tests in this style.

## Invariants you must preserve when editing

These are enforced by tests, by `baseline-doctor`, and by `doctor`. Breaking them silently is the failure mode this package exists to prevent.

- **Do not duplicate ECC-provided MCPs** (`context7`, `github`, `sequential-thinking`) in the seeded repo `.mcp.json`. They arrive via ECC.
- **Do not copy ECC or context-mode plugin hooks** into the seeded repo `.claude/settings.json`. Repo hooks here cover Graphiti lifecycle only.
- **`autoMemoryEnabled` must be `false`** in seeded project settings — Graphiti is the canonical memory layer.
- **Bootstrap must not drop custom fields**: user-owned hooks in `settings.json` and custom MCP auth fields (`headers`, `headersHelper`) in `.mcp.json` must survive a re-bootstrap. `test_bootstrap_hygiene.py` covers this.
- **Group IDs**: `MEMORY_GROUP_ID` is the human-readable logical identity; `GRAPHITI_STORAGE_GROUP_ID` is deterministic `g_<slug>_<hash>`, NFKC-normalized, never hand-edited. Rename flows go through `graphiti_admin.py migrate-logical-id --mode {keep-storage|new-storage}`. See `GROUP-ID-POLICY.md`.
- **Docs-to-code fidelity**: if docs describe something as automated, there must be code for it. If a surface is upstream-owned, docs must say so explicitly. Do not regress this contract.
- **Localhost-first defaults**: Compose files bind to `127.0.0.1`. Remote exposure is an explicit opt-in, and shipped Caddy/remote examples are examples, not production configs.
- **Do not commit secrets**. `.claude/state/**`, `.env*`, and `secrets/**` are sensitive; the security-deny snippet in `SECURITY.md` section 7 is the recommended shape.
