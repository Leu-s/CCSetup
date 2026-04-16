# Tutorial

This is the most human-friendly way to use this framework.

Its normal mode is:
- **the human** loads the package, provides secrets, and confirms prompts;
- **Claude Code** reads the docs, performs install/bootstrap, and then works inside the repo;
- **the framework itself** automates hooks, memory, repo settings, MCP wiring, and part of the first-run setup.

## 1. What this package is in practice

The package gives you two layers:
- **the base Claude Code baseline**: ECC, Context7/GitHub/Sequential Thinking via ECC, context-mode, ui-ux-pro-max-skill, repomix, ccusage;
- **the repo overlay**: Graphiti memory, `codebase-memory-mcp`, repo `CLAUDE.md`, `.claude/settings.json`, `.mcp.json`, hooks, and the state tree.

So it is not just "memory". It is a working environment for Claude Code around a specific repository.

## 2. Who does what

### What you do
- unpack the package;
- give Claude Code access to the repo;
- set the required env secrets;
- confirm plugin / MCP prompts;
- ask Claude Code to explain what is happening when needed.

### What Claude Code does
- reads `README.md`, `QUICKSTART.md`, `INSTALL.md`, `USER-MANUAL.md`;
- runs the install flow and bootstraps the repo;
- then works through the agreed tool order: `codebase-memory-mcp` → Graphiti → Context7 → GitHub MCP → raw files.

### What the framework does automatically
- seeds the repo `CLAUDE.md`, `.claude/settings.json`, `.mcp.json`;
- wires up Graphiti hooks;
- creates the queue/ledger/archive path for memory;
- disables built-in auto memory at the repo level;
- enables `codebase-memory-mcp auto_index` and runs the initial indexing of the repo;
- declares the retained **plugin** layer in the repo settings.

## 3. What bootstrap actually changes in the repo

After install/bootstrap the following appear or are updated in the repo:
- `CLAUDE.md`;
- `.claude/settings.json`;
- `.mcp.json`;
- `.claude/graphiti.json`;
- `.claude/hooks/*`;
- `.claude/rules/graphiti-memory.md`;
- `.claude/state/.gitignore`;
- `.claude/state/graphiti-runtime/` and the runtime stamp;
- local queue/ledger/archive files, once hooks start running.

What does **not** arrive in the repo automatically:
- `repomix` and `ccusage` as local CLIs;
- ECC `rules`, because the plugin layer does not deploy them automatically.

## 4. First path from scratch

1. Go through [QUICKSTART.md](QUICKSTART.md).
2. If you need a full install with explanations, open [INSTALL.md](INSTALL.md).
3. After bootstrap, run:
   - `./tools/graphiti_admin.py baseline-doctor /absolute/path/to/repo`
   - `./tools/graphiti_admin.py status /absolute/path/to/repo`
   - `./tools/graphiti_admin.py doctor /absolute/path/to/repo`
4. Open the repo in Claude Code.
5. Approve plugin / MCP prompts if they appear.

## 5. What to tell Claude Code

### Option 1. Set up the framework from scratch

```text
Read README.md, TUTORIAL.md, QUICKSTART.md, INSTALL.md, and USER-MANUAL.md from this package.
Then set up this repo under this framework.
First, tell me which manual steps and confirmations are needed from me, then run the install in order.
Do not duplicate ECC MCPs in the repo .mcp.json and do not copy plugin hooks by hand.
```

### Option 2. Check that everything is already installed correctly

```text
Check this repo for compliance with the framework.
Start with baseline-doctor, status, and doctor.
Explain in plain terms what is already fine and what still needs to be done.
```

### Option 3. Explain the framework in plain language

```text
Explain this framework to me as a user: what it automates, what Claude Code does, what I have to do myself, and how to work with it day to day.
Lean on TUTORIAL.md and USER-MANUAL.md.
```

## 6. What you will see in Claude Code on the first open of the repo

The normal sequence is:
- Claude Code sees the repo `.claude/settings.json`;
- it may ask you to confirm plugins from the retained baseline;
- it may ask you to confirm project MCP servers;
- after that the repo has a working plugin baseline, hooks, `graphiti-memory`, and `codebase-memory-mcp`.

Important boundary: repo settings reproduce the **plugin layer**, but they do not install `repomix`, `ccusage` for you, and they do not deploy ECC `rules`. For the full ECC rules surface, install the upstream ECC rules separately or copy `rules/common` plus the language directories you need.

If something here is unclear, do not try to guess by hand. Just ask Claude Code to explain which prompt appeared and why it is needed.

## 7. How to use the framework day to day

### When you need to understand a new repo
Tell Claude Code to start with `codebase-memory-mcp` instead of reading files at random.

### When you need to continue yesterday's work
Ask it to check Graphiti memory and the startup checkpoint first, then move to the specific task.

### When you need current library documentation
Tell it to use Context7.

### When you need GitHub operations
Tell it to use the GitHub MCP.

### When you need a full repo snapshot
Tell it to use `repomix`.

### When you want to look at usage/cost
Tell it to use `ccusage`.

### When the task is UI/UX
Say explicitly that it can lean on `ui-ux-pro-max-skill`.

## 8. What is automated and what is not

### Automated
- Graphiti capture via `Stop` and `PreCompact`;
- local checkpoint on `SessionStart`;
- reproducible plugin baseline in repo settings;
- `codebase-memory-mcp` first-run bootstrap;
- admin CLI for health/status/flush/requeue.

### Not fully automated
- entering secrets;
- live approvals in Claude Code;
- ECC rules install, if you want the full rules surface from ECC;
- external Docker/runtime bring-up, if the environment does not allow it;
- the decision of which task you want to work on next.

## 9. Typical user mistakes

Do not:
- manually duplicate Context7/GitHub/Sequential Thinking in the repo `.mcp.json`;
- manually copy ECC hooks into repo hooks;
- assume that the repo-declared plugin layer automatically installed `repomix`, `ccusage`, or ECC `rules`;
- change `GRAPHITI_STORAGE_GROUP_ID` by hand without the migration flow;
- edit `.claude/state/` like regular configuration;
- expect a new machine to automatically have the same local startup checkpoint.

## 10. If something is unclear

The best path is not to search for an answer blindly, but to ask Claude Code to explain the system via the docs.

Start with this:

```text
Explain to me the current state of this framework based on its documentation.
Tell me what is the base baseline here, what is added at the repo level, what is automated, what needs my confirmation, and how to properly use this stack.
```
