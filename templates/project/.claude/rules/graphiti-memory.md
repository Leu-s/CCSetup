# Graphiti memory contract

- Graphiti is the canonical long-term memory for this repository.
- Use `GRAPHITI_STORAGE_GROUP_ID` for Graphiti memory reads and writes.
- `MEMORY_GROUP_ID` is the human-readable project identifier. Do not pass it directly to Graphiti as a storage namespace.
- Do not invent a new storage group id during normal work.
- Use `codebase-memory-mcp` first for structural code questions. Use Graphiti for continuity across sessions.
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
