#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib.adapters import check_mcp_health, mock_ingest_enabled
from lib.config import ensure_state_dirs, expand_env_string, important_watch_paths, load_config
from lib.group_ids import load_registry, registry_collisions, resolve_group_context
from lib.ledger import ledger_metrics
from lib.runtime import load_runtime_stamp, selected_runtime_python
from lib.util import project_dir, read_json


def _mcp_command_status(spec: dict[str, object] | None) -> dict[str, object]:
    if not isinstance(spec, dict):
        return {"present": False, "command": None, "expanded_command": None, "resolvable": False}
    raw_command = spec.get("command")
    if not raw_command:
        return {"present": True, "command": None, "expanded_command": None, "resolvable": False}
    command = str(raw_command)
    try:
        expanded = expand_env_string(command)
    except Exception:
        expanded = command
    path_candidate = pathlib.Path(expanded).expanduser()
    resolvable = path_candidate.exists() if (path_candidate.is_absolute() or '/' in expanded) else shutil.which(expanded) is not None
    return {"present": True, "command": command, "expanded_command": expanded, "resolvable": resolvable}


def _count_json_files(path: pathlib.Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.glob("*.json"))


def main() -> int:
    root = project_dir()
    config = load_config(root)
    ensure_state_dirs(root, config)
    group = resolve_group_context(root, config)
    queue = config["queue"]
    health = check_mcp_health(config["mcp"]["healthUrl"])
    runtime_python = selected_runtime_python(root, config)
    graphiti_core_available = importlib.util.find_spec("graphiti_core") is not None
    mcp_json = read_json(root / ".mcp.json", default={}) or {}
    mcp_servers = mcp_json.get("mcpServers") or {}
    codebase_memory = _mcp_command_status(mcp_servers.get("codebase-memory-mcp"))

    state = {
        "project_dir": str(root),
        "backend": config["engine"]["backend"],
        "provider": config["engine"]["provider"],
        "group": group,
        "mcp_http_health": {
            "ok": health.ok,
            "detail": health.detail,
        },
        "mcp_health": {
            "ok": health.ok,
            "detail": health.detail,
        },
        "mcp": {
            "graphiti_memory_present": "graphiti-memory" in mcp_servers,
            "codebase_memory_mcp_present": codebase_memory["present"],
            "project_mcp_approval_required": True,
            "project_mcp_approval_verifiable_here": False,
        },
        "codebase_memory": codebase_memory,
        "direct_ingest": {
            "mock_ingest": mock_ingest_enabled(),
            "runtime_python_present": bool(runtime_python),
            "graphiti_core_available": graphiti_core_available,
            "note": "Direct ingest uses the repo runtime and graphiti_core, not the MCP HTTP endpoint.",
        },
        "ledger": ledger_metrics((root / queue["ledgerPath"]).resolve()),
        "queue": {
            "spool": _count_json_files((root / queue["spoolDir"]).resolve()),
            "archive": _count_json_files((root / queue["archiveDir"]).resolve()),
            "dead_letter": _count_json_files((root / queue["deadLetterDir"]).resolve()),
            "last_flush": read_json((root / queue["lastFlushPath"]).resolve(), default={}) or {},
        },
        "runtime": {
            "selected_python": runtime_python,
            "stamp": load_runtime_stamp(root, config),
        },
        "watch_paths": important_watch_paths(root, config),
        "registry_collisions": registry_collisions(load_registry(root / config["groupIds"]["registryPath"])),
    }
    print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
