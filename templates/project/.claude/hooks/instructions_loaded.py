#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib.adapters import check_mcp_health
from lib.config import ensure_state_dirs, load_config
from lib.group_ids import resolve_group_context
from lib.observability import log_event
from lib.util import load_stdin_json, project_dir


def main() -> int:
    root = project_dir()
    config = load_config(root)
    ensure_state_dirs(root, config)
    payload = load_stdin_json(default={})
    group = resolve_group_context(root, config)
    health = check_mcp_health(config["mcp"]["healthUrl"])
    log_event(
        root,
        config,
        "instructions_loaded",
        {
            "hook_input": payload,
            "logical_group_id": group["logical_group_id"],
            "storage_group_id": group["storage_group_id"],
            "mcp_health_ok": health.ok,
            "mcp_health_detail": health.detail,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
