#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib.config import ensure_state_dirs, load_config
from lib.group_ids import registry_collisions, resolve_group_context, load_registry
from lib.observability import log_event
from lib.util import hook_json_output, load_stdin_json, project_dir, read_json


def main() -> int:
    root = project_dir()
    config = load_config(root)
    ensure_state_dirs(root, config)
    payload = load_stdin_json(default={})
    group = resolve_group_context(root, config)

    settings_json = read_json(root / ".claude" / "settings.json", default={}) or {}
    hook_events = sorted((settings_json.get("hooks") or {}).keys())
    mcp_json = read_json(root / ".mcp.json", default={}) or {}
    registry = load_registry(root / config["groupIds"]["registryPath"])
    collisions = registry_collisions(registry)

    errors: list[str] = []
    warnings: list[str] = []
    if settings_json.get("autoMemoryEnabled") is not False:
        errors.append("autoMemoryEnabled must remain false in project settings")
    required = set(config["doctor"]["requiredHookEvents"])
    if not required.issubset(set(hook_events)):
        errors.append("required Graphiti hook events are missing from .claude/settings.json")
    if "graphiti-memory" not in (mcp_json.get("mcpServers") or {}):
        warnings.append(".mcp.json is missing graphiti-memory")
    if collisions:
        errors.append("group registry contains storage collisions")
    if group["storage_mismatch"]:
        warnings.append("logical group id and effective storage id are out of canonical sync")

    log_event(
        root,
        config,
        "config_drift_guard",
        {
            "hook_input": payload,
            "logical_group_id": group["logical_group_id"],
            "storage_group_id": group["storage_group_id"],
            "expected_storage_group_id": group["expected_storage_group_id"],
            "errors": errors,
            "warnings": warnings,
            "registry_collisions": collisions,
        },
    )

    if errors and config.get("drift", {}).get("blockProjectConfigChanges", True):
        reason = "Graphiti infrastructure contract would become inconsistent: " + "; ".join(errors)
        print(hook_json_output(hook_event_name="ConfigChange", decision="block", reason=reason))
        return 0

    if warnings:
        print(hook_json_output(hook_event_name="ConfigChange", additional_context="Graphiti configuration changed. Review doctor output if memory behavior looks inconsistent."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
