# Graphiti memory contract

- Graphiti is the canonical long-term memory for this repository.
- Use `GRAPHITI_STORAGE_GROUP_ID` for Graphiti memory reads and writes.
- `MEMORY_GROUP_ID` is the human-readable project identifier. Do not pass it directly to Graphiti as a storage namespace.
- Do not invent a new storage group id during normal work.
- Use `codebase-memory-mcp` first for graph-scale structural code questions (reach, data-flow, IMPORTS, architecture, impact radius). Use `serena` for symbol-level navigation and atomic refactors (find/rename/replace a specific symbol via LSP). Use Graphiti for continuity across sessions.
- Never use `serena`'s memory tools — run `serena` with the `no-memories` mode. Graphiti is the canonical long-term memory; two memory backends produce split state.
- Store only high-signal project memory:
  - architectural decisions
  - important constraints
  - user preferences that matter across sessions
  - unresolved risks worth carrying forward
- Do not store:
  - large code blocks
  - raw logs
  - temporary exploratory noise
  - facts already obvious from git history
