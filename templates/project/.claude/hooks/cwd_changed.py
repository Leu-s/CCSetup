#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib.config import ensure_state_dirs, important_watch_paths, load_config
from lib.group_ids import resolve_group_context
from lib.observability import log_event
from lib.runtime import selected_runtime_python
from lib.util import hook_json_output, load_stdin_json, project_dir, write_session_exports


def main() -> int:
    root = project_dir()
    config = load_config(root)
    ensure_state_dirs(root, config)
    payload = load_stdin_json(default={})
    group = resolve_group_context(root, config)

    exports = {
        "GRAPHITI_LOGICAL_GROUP_ID": group["logical_group_id"],
        "GRAPHITI_STORAGE_GROUP_ID": group["storage_group_id"],
        "GRAPHITI_BACKEND": config["engine"]["backend"],
        "GRAPHITI_PROVIDER": config["engine"]["provider"],
    }
    selected_python = selected_runtime_python(root, config)
    if selected_python:
        exports["GRAPHITI_HOOK_PYTHON"] = selected_python
        exports["GRAPHITI_HOOK_RUNTIME_PYTHON"] = selected_python
    write_session_exports(exports)

    watch_paths = important_watch_paths(root, config)
    log_event(
        root,
        config,
        "cwd_changed",
        {
            "hook_input": payload,
            "logical_group_id": group["logical_group_id"],
            "storage_group_id": group["storage_group_id"],
            "watch_paths": watch_paths,
            "selected_python": selected_python,
        },
    )
    print(hook_json_output(hook_event_name="CwdChanged", watch_paths=watch_paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
