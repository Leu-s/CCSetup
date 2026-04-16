# Project Instructions

## Memory
MEMORY_GROUP_ID: your-project-name
GRAPHITI_STORAGE_GROUP_ID: g_your_project_storage_id

## Working Principles
- Think before coding. Read the relevant files, understand the flow, then change the minimum necessary surface.
- Prefer simplicity. Choose the smallest solution that solves the actual problem without speculative abstractions.
- Make surgical changes. Do not refactor unrelated areas unless the task explicitly requires it.
- Stay goal-driven. Translate the request into clear success criteria and verify that the result actually satisfies them.

## Tool Priority
- Use `codebase-memory-mcp` first for structural questions about symbols, call paths, module relationships, routes, and impact radius.
- Use Graphiti for cross-session memory: decisions, constraints, user preferences, unresolved risks, and important outcomes.
- Use Context7 for current library and framework documentation.
- Use GitHub MCP for issues, pull requests, branches, and repository operations.
- Use raw file reads only after the structural tools have narrowed the search space.

## Plugin Surfaces
The following retained plugins are active in this workspace. Invoke their skills, agents, and commands for the use cases below; do not reimplement what they already provide.

- `everything-claude-code@everything-claude-code` — ECC bundle (agents, skills, slash commands). Use ECC commands for repo audits, scaffolding, automation recommendations, PR and code review, security review, and cross-cutting analysis. The bundled MCPs available through ECC are `github`, `context7`, `sequential-thinking`, `exa`, and `playwright`. The bundled `memory` MCP is excluded — see Excluded Surfaces.
- `context-mode@context-mode` — invoke when session context approaches its budget or after long tool-heavy turns, to reset focus without losing load-bearing state.
- `ui-ux-pro-max@ui-ux-pro-max-skill` — invoke for UI/UX critique, design-system questions, component composition, and accessibility audits.

## Excluded Surfaces
- Do not use the `memory` MCP shipped by `everything-claude-code`. Graphiti is the canonical long-term memory layer for this repository, and writing to two memory backends produces split state, conflicting recall, and drift between sessions.
- Do not introduce a second code-graph or symbol-index tool alongside `codebase-memory-mcp`.
- Do not re-enable `autoMemoryEnabled` in `.claude/settings.json`; the Graphiti hook pipeline owns memory capture.

## Memory Write Triggers
Memory capture is hook-driven. Claude does not write to Graphiti directly during normal turns.

- `Stop` hook (`.claude/hooks/graphiti_stop.py`) spools a session-end episode into the local queue and ledger automatically. If `queue.asyncFlushOnStop` is true in `.claude/graphiti.json`, a detached flush is fired.
- `PreCompact` hook (`.claude/hooks/pre_compact.py`) spools pre-compaction context so long-running sessions retain continuity across compaction boundaries.
- `PostCompact` hook (`.claude/hooks/post_compact.py`) spools a short anchor right after Claude compacts the transcript, so continuity survives the shortened context rather than being anchored only to the pre-compact snapshot.
- `PostToolUseFailure` hook (`.claude/hooks/post_tool_use_failure.py`) captures tool-level failures (timeouts, permission denials, unreachable backends) as boundary signals — useful for reasoning about recurring friction across sessions.
- Delivery into Neo4j runs via `graphiti_core` (not the MCP) and is triggered by the cron wrapper at `~/.claude/hooks/graphiti-flush-cron.sh` or manually via `./tools/graphiti_admin.py flush <repo>`.

Write only high-signal content: architectural decisions, load-bearing constraints, user preferences that must carry across sessions, and unresolved risks worth revisiting. Do not write: large code blocks, raw logs, exploratory noise, or anything already obvious from git history.

## Graphiti Memory Contract
- Graphiti is the canonical long-term memory for this repository.
- Use `GRAPHITI_STORAGE_GROUP_ID` for Graphiti memory reads and writes.
- `MEMORY_GROUP_ID` is the human-readable project identity.
- Do not invent or rotate storage group ids during normal work.
