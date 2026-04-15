#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib.adapters import check_mcp_health, mock_ingest_enabled
from lib.config import ensure_state_dirs, expand_env_string, load_config
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


def _provider_backend_readiness(config: dict[str, object]) -> tuple[list[str], list[str]]:
    provider = str(config["engine"]["provider"])
    backend = str(config["engine"]["backend"])
    missing_env: list[str] = []
    warnings: list[str] = []

    if provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        missing_env.append("OPENAI_API_KEY")
    if provider == "openai_generic":
        ocfg = config["engine"]["openai_generic"]
        if not ocfg.get("baseUrl"):
            missing_env.append("OPENAI_BASE_URL or openai_generic.baseUrl")
        if not ocfg.get("apiKey"):
            missing_env.append("OPENAI_API_KEY or openai_generic.apiKey")
    if provider == "gemini" and not config["engine"]["gemini"].get("apiKey"):
        missing_env.append("GOOGLE_API_KEY")

    if backend == "neo4j":
        neo = config["engine"]["neo4j"]
        for key in ["uri", "user", "password"]:
            if not neo.get(key):
                missing_env.append(f"neo4j.{key}")
    if backend == "falkordb":
        if not config["engine"]["falkordb"].get("uri"):
            missing_env.append("falkordb.uri")
        if os.environ.get("SEMAPHORE_LIMIT", "1") != "1":
            warnings.append("Set SEMAPHORE_LIMIT=1 for FalkorDB profile")

    return sorted(set(missing_env)), warnings


def main() -> int:
    root = project_dir()
    config = load_config(root)
    ensure_state_dirs(root, config)
    group = resolve_group_context(root, config)

    settings_json = read_json(root / ".claude" / "settings.json", default={}) or {}
    hook_events = sorted((settings_json.get("hooks") or {}).keys())
    required = set(config["doctor"]["requiredHookEvents"])
    missing_hook_events = sorted(required - set(hook_events))
    mcp_json = read_json(root / ".mcp.json", default={}) or {}
    mcp_servers = mcp_json.get("mcpServers") or {}
    codebase_memory = _mcp_command_status(mcp_servers.get("codebase-memory-mcp"))

    registry = load_registry(root / config["groupIds"]["registryPath"])
    collisions = registry_collisions(registry)
    mock_mode = mock_ingest_enabled()
    mcp_health = check_mcp_health(config["mcp"]["healthUrl"])

    backend = config["engine"]["backend"]
    provider = config["engine"]["provider"]
    missing_env: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    if settings_json.get("autoMemoryEnabled") is not False:
        errors.append("Project autoMemoryEnabled is not false")
    if missing_hook_events:
        errors.append("Missing required Graphiti hook events")
    if "graphiti-memory" not in mcp_servers:
        errors.append(".mcp.json is missing graphiti-memory")
    if not codebase_memory["present"]:
        errors.append(".mcp.json is missing codebase-memory-mcp")
    if collisions:
        errors.append("Registry contains storage collisions")
    if not mcp_health.ok and not mock_mode:
        warnings.append("Graphiti MCP health endpoint is not reachable")
    if group["storage_mismatch"]:
        warnings.append("GRAPHITI_STORAGE_GROUP_ID differs from deterministic expected value")
    if codebase_memory["present"] and not codebase_memory["resolvable"]:
        warnings.append("codebase-memory-mcp command is not resolvable on PATH; set CODEBASE_MEMORY_MCP_BIN if needed")

    runtime_python = selected_runtime_python(root, config)
    runtime_stamp = load_runtime_stamp(root, config)
    if not runtime_python and not mock_mode:
        warnings.append("No dedicated hook runtime found; hooks will fall back to system python")

    graphiti_core_available = importlib.util.find_spec("graphiti_core") is not None
    provider_missing_env, provider_warnings = _provider_backend_readiness(config)
    missing_env.extend(provider_missing_env)
    warnings.extend(provider_warnings)
    if not graphiti_core_available and not mock_mode:
        missing_env.append("graphiti_core package")

    direct_ingest_ready = bool(runtime_python) and graphiti_core_available and not provider_missing_env
    ok = not errors and not missing_env and (not warnings or not config.get("drift", {}).get("failDoctorOnWarnings", True))

    report = {
        "project_dir": str(root),
        "backend": backend,
        "provider": provider,
        "mock_ingest": mock_mode,
        "graphiti_core_available": graphiti_core_available,
        "group": {
            "logical_group_id": group["logical_group_id"],
            "storage_group_id": group["storage_group_id"],
            "expected_storage_group_id": group["expected_storage_group_id"],
            "storage_source": group["storage_source"],
            "storage_matches_expected": not group["storage_mismatch"],
            "mismatch_sources": group["mismatch_sources"],
        },
        "mcp_http_health": {"ok": mcp_health.ok, "detail": mcp_health.detail},
        "mcp_health": {"ok": mcp_health.ok, "detail": mcp_health.detail},
        "config": {
            "required_hook_events_present": not missing_hook_events,
            "missing_hook_events": missing_hook_events,
            "auto_memory_disabled": settings_json.get("autoMemoryEnabled") is False,
            "graphiti_mcp_present": "graphiti-memory" in mcp_servers,
            "codebase_memory_mcp_present": codebase_memory["present"],
        },
        "codebase_memory": codebase_memory,
        "claude_code": {
            "project_mcp_scope": True,
            "project_mcp_approval_required": True,
            "project_mcp_approval_verifiable_here": False,
            "project_mcp_approval_note": "Claude Code approval state is interactive client state; doctor verifies repo config and HTTP reachability, not user approval decisions.",
        },
        "runtime": {
            "selected_python": runtime_python,
            "stamp": runtime_stamp,
        },
        "direct_ingest": {
            "ready": direct_ingest_ready or mock_mode,
            "runtime_python_present": bool(runtime_python),
            "graphiti_core_available": graphiti_core_available,
            "provider_and_backend_env_ready": not provider_missing_env,
            "missing_env": provider_missing_env,
            "note": "Direct ingest uses graphiti_core in the dedicated repo runtime. It is separate from MCP HTTP health.",
        },
        "ledger": ledger_metrics((root / config["queue"]["ledgerPath"]).resolve()),
        "registry_collisions": collisions,
        "notes": [
            "MCP HTTP health and direct-ingest readiness are separate checks.",
            "Project-scoped MCP approval must still be granted inside Claude Code when approval prompts are enabled.",
        ],
        "errors": errors,
        "warnings": warnings,
        "missing_env": sorted(set(missing_env)),
        "ok": ok,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
