# Project Instructions

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

## Memory
MEMORY_GROUP_ID: your-project-name
GRAPHITI_STORAGE_GROUP_ID: g_your_project_storage_id

## Graphiti Memory Contract
- Graphiti is the canonical long-term memory for this repository.
- Use `GRAPHITI_STORAGE_GROUP_ID` for Graphiti memory reads and writes.
- `MEMORY_GROUP_ID` is the human-readable project identity.
- Do not invent or rotate storage group ids during normal work.
