# User manual

## 0. How to use this framework as a human

The most common mode is:
- you hand Claude Code the repo and this package;
- Claude Code reads the docs and performs install/bootstrap;
- from then on you assign tasks, and Claude Code uses the agreed baseline automatically.

So this manual is not meant to make you run every tool by hand every day.
It is here so you understand **what the system does, what Claude Code does, and what you have to do yourself**.

Starting route for a human:
1. [TUTORIAL.md](TUTORIAL.md)
2. [QUICKSTART.md](QUICKSTART.md)
3. [INSTALL.md](INSTALL.md)
4. then this manual

## 1. Mental model of the whole stack

The system has clear roles.

### Retained Claude Code layer
- **`everything-claude-code@everything-claude-code` (ECC bundle)** — the base harness: skills, agents, hooks, and bundled MCP surface.
- **ECC rules surface** — a separate upstream-owned layer; plugin install does not deploy it automatically.
- **Context7 / GitHub MCP / Sequential Thinking** — arrive via the ECC bundle.
- **context-mode** — reduces noise from large tool outputs in context.
- **ui-ux-pro-max-skill** — design intelligence for UI/UX tasks.
- **repomix** — operator-local CLI for an AI-friendly snapshot of the whole repo.
- **ccusage** — operator-local CLI for usage/cost on Claude Code logs.

### Repo layer
- **Graphiti** — the canonical long-term memory of the project.
- **codebase-memory-mcp** — relationship graph of the code (callers, reach, data-flow, IMPORTS, architecture).
- **serena** — LSP-backed symbolic navigation and atomic refactors (file outline, symbol lookup, rename, replace body).
- **repo hooks** — automatic capture and delivery of memory summaries.
- **`CLAUDE.md`** — working principles, tool priority, and project identity.
- **repo `.claude/settings.json`** — hooks plus the reproducible plugin baseline.

## 2. Tool order

1. **`codebase-memory-mcp`** — graph-scale structural questions: callers, transitive reach, data-flow, IMPORTS, architecture, impact radius.
2. **`serena`** — single-symbol LSP operations and atomic refactors: file outline, symbol lookup, exact references, rename, replace body, insert-before/after-symbol, safe-delete. Pair with (1) — `serena` answers "where is this one symbol and how do I change it safely", `codebase-memory-mcp` answers "what else depends on it".
3. **Graphiti** — continuity, decisions, constraints, unresolved risks.
4. **Context7** — current library/framework docs.
5. **GitHub MCP** — issues, PRs, branches, repo actions.
6. **raw file reads** — only after narrowing the search.

## 3. How automatic memory works in the repo

### At session start
`SessionStart`:
- determines logical/storage ids;
- exports env for the rest of the session;
- reads the local delivered ledger;
- prints a short checkpoint into context.

### During the session
`InstructionsLoaded`, `CwdChanged`, and `FileChanged`:
- keep runtime exports current;
- update `watchPaths`;
- log lifecycle events.

### Before compaction and at the end of a reply
`PreCompact` and `Stop`:
- collect a short summary from the session;
- write the payload to spool and ledger;
- do not wait on a live network write.

### Outside the Claude reply
`graphiti_flush.py`:
- reads due payloads from spool;
- delivers them via `graphiti_core`;
- moves successes to archive;
- retries or dead-letters on failures.

## 4. How the plugin baseline works now

The retained plugin baseline no longer lives only in user scope.

After bootstrap, the repo `.claude/settings.json` already declares:
- marketplace source for `everything-claude-code@everything-claude-code` (ECC bundle), `context-mode@context-mode`, and `ui-ux-pro-max@ui-ux-pro-max-skill`;
- `enabledPlugins` for those three plugins.

Consequence:
- a fresh clone gets the same **plugin contract**;
- a cloud session can reproduce the **plugin portion** of the baseline from the repo;
- user preinstall remains a convenience, not the only way to configure.

Important boundary:
- `repomix` and `ccusage` are not installed via repo settings;
- ECC `rules` are also not deployed by the plugin layer automatically.

## 5. `codebase-memory-mcp`: what is now automated

The previous weak spot was that after manual binary install you still had to remember to:
- restart the agent;
- say "Index this project";
- or enable `auto_index`.

In this package the install flow now does two things itself:
- `codebase-memory-mcp config set auto_index true`
- `codebase-memory-mcp cli index_repository '{"repo_path":"..."}'`

So by the time you first open the repo in Claude Code, the structural layer is no longer left "half-activated".

## 6. When to rely on automatic memory vs. MCP tools

### Rely on automatic memory when
- you need important decisions to not get lost between sessions;
- you want a short local checkpoint at start;
- summary-level continuity is enough.

### Use Graphiti MCP tools when
- you need to find specific facts or entities;
- you need to pull older history from the remote graph;
- you are on a new machine and the local ledger is still empty.

### Use `codebase-memory-mcp` when
- you need to find the entry point in an unfamiliar repo;
- you need to understand who calls what across the whole repo (transitive callers);
- you need to trace data-flow or cross-service paths;
- you need to assess impact before a code change (`detect_changes`);
- you need an architectural overview or cross-module dependency slice;
- you need to reduce the number of raw file reads.

### Use `serena` when
- you need the outline of a specific file (classes/methods/variables via LSP);
- you need exact references to a symbol (LSP-accurate, not text matches);
- you are performing a refactor: cross-file rename, atomic body replace, safe-delete, insert-before/after-symbol;
- you need to read a single symbol's body by its qualified name;
- you know the symbol you want to touch and `codebase-memory-mcp` already narrowed the scope.

`serena` and `codebase-memory-mcp` compose: start with `codebase-memory-mcp` to find the candidates and the transitive reach, then use `serena` to execute the precise change. Never use `serena`'s memory tools — Graphiti owns that role, and `serena` runs with `no-memories` mode so its memory surface is disabled.

### Disambiguating overlaps between `serena` and `codebase-memory-mcp`

Two pairs of capabilities can look similar on the surface. Pick the correct one by the axis of the question:

- **"Find references to this symbol"** → `serena` when you need LSP-accurate per-symbol references (follows type-aware bindings, ignores unrelated textual matches). Use `codebase-memory-mcp` when you need transitive reach across the whole repo ("what eventually calls this", "what's the impact radius"), not just direct LSP references.
- **"Show me a function's body"** → `serena.find_symbol` when you want the body of one specific symbol by qualified name. Use `codebase-memory-mcp.get_code_snippet` when you want a snippet cited alongside graph-scale context the graph query already returned.

## 7. How ECC hooks, context-mode, and repo Graphiti hooks interact

They should not replace each other.

- ECC provides its own global harness and global hooks.
- context-mode provides routing/sandbox hooks via the plugin.
- The repo `.claude/settings.json` from this package adds Graphiti lifecycle hooks.

Important rule:
- **do not copy ECC plugin hooks by hand into the repo `settings.json`**;
- **do not try to port context-mode hook config into the repo hooks of this package**.

The repo hooks of this package are an **additional project layer**, not a replacement for ECC or context-mode.

## 8. Fresh machine / fresh clone semantics

`SessionStart` does **not** do a remote search in Graphiti. It reads only the local delivered ledger at `.claude/state/graphiti-ledger.sqlite3`.

Consequence:
- on a new machine, the memory checkpoint at start may be empty;
- that does not mean remote Graphiti is empty;
- if you need shared history right away, use Graphiti MCP search tools manually.

The plugin baseline behaves differently here:
- if the repo is trusted and marketplace access is available, Claude Code may install the repo-declared plugins at session start;
- if a plugin is already preinstalled locally, prompts will either not appear or will be minimal.

## 9. Best practices

1. **One canonical long-term memory:** Graphiti.
2. **Do not duplicate ECC MCPs in the repo `.mcp.json`:** Context7, GitHub MCP, and Sequential Thinking are already covered globally.
3. **Do not duplicate ECC hooks in repo settings.**
4. **For code questions, structural tools first, then files.**
5. **Do not change `GRAPHITI_STORAGE_GROUP_ID` by hand without reason.** Work through `MEMORY_GROUP_ID` and admin migration commands.
6. **Keep secrets in env, not in git.**
7. **Do not conflate MCP health with ingest health.** The Graphiti HTTP path and host-side direct ingest are different checks.

## 9a. Excluded surfaces

Do not use the `memory` MCP shipped by the `everything-claude-code` bundle. Graphiti is the canonical long-term memory layer for this framework. Writing to two memory backends produces split state and conflicts with the queue/ledger/archive contract.

In practice this means:
- do not add the bundled `memory` MCP to the repo `.mcp.json`;
- do not call its tools in parallel with Graphiti in the same session;
- if the ECC bundle exposes it anyway, rely on `graphiti-memory` as the single write path.

## 10. Most useful daily commands

### Ecosystem baseline check
```bash
./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo
```

### Repo memory layer status
```bash
./tools/graphiti_admin.py status /absolute/path/to/repo
```

### Doctor
```bash
./tools/graphiti_admin.py doctor /absolute/path/to/repo
```

### Manual flush
```bash
./tools/graphiti_admin.py flush /absolute/path/to/repo --limit 20
```

### Requeue
```bash
./tools/graphiti_admin.py requeue /absolute/path/to/repo --source dead-letter --limit 20
```

### Repomix snapshot
```bash
npx repomix@latest
```

### Claude usage report
```bash
npx ccusage@latest
```

Note: the `npx` path for `repomix` and `ccusage` may require network on first run if the npm cache is still empty.

## 11. Daily user scenarios

### Scenario A. I just opened a new repo
Ask Claude Code to:
- run `baseline-doctor`, `status`, `doctor`;
- explain what is already ready;
- then work through the agreed tool order.

### Scenario B. I came back to the task the next day
Ask Claude Code to:
- pick up the startup checkpoint first;
- read remote Graphiti history if needed;
- then continue the task.

### Scenario C. I do not understand what is happening in the framework
Ask Claude Code to:
- explain the repo baseline;
- say which hooks are active;
- say what is automated and what still needs your involvement.

### Scenario D. I need to quickly understand an unfamiliar codebase
Ask Claude Code to start with `codebase-memory-mcp` instead of reading files at random.

### Scenario E. I have a UI/UX task
Say explicitly that it can lean on `ui-ux-pro-max-skill`.

## 12. Ready-made requests for Claude Code

### Explain the current state of the repo

```text
Explain to me the current state of this repo under the framework: what is already installed, which hooks and MCPs are working, what is automated, and what still needs my involvement.
```

### Set up the repo from scratch

```text
Read README.md, TUTORIAL.md, QUICKSTART.md, INSTALL.md, and USER-MANUAL.md from this package.
Then set up this repo under the framework.
Before any manual steps, briefly tell me what I need to confirm or enter myself.
```

### Continue previous work

```text
Start with the memory checkpoint and structural overview of this repo, then continue the task.
```

### Explain the framework in plain language

```text
Explain this framework to me in plain language: what the baseline does, what the repo overlay adds, how memory, hooks, and plugins work, and when I need to confirm something myself.
```

## 13. What the human still does themselves

The human is still responsible for:
- correct secrets and env values;
- trusting the repo;
- plugin approvals;
- MCP approvals;
- choosing the actual task to work on.

The framework and Claude Code remove a lot of manual work from the human, but they should not hide these control points.

## 14. The most important usage rule

Do not try to bypass the framework with manual duplicates.

Do not:
- add the same MCPs a second time in the repo `.mcp.json`;
- copy plugin hooks by hand into repo settings;
- twiddle storage ids by hand;
- patch `.claude/state/` by hand before you understand what actually broke.

First ask Claude Code to explain and check state via the docs and the admin commands.
