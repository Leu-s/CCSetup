#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib.capture import make_memory_payload
from lib.config import ensure_state_dirs, load_config
from lib.observability import log_event
from lib.queue_store import queue_payload
from lib.util import load_stdin_json, project_dir, trim_text


def main() -> int:
    root = project_dir()
    config = load_config(root)
    ensure_state_dirs(root, config)
    payload = load_stdin_json(default={})

    tool_name = payload.get("tool_name") or "unknown"
    error = trim_text(str(payload.get("tool_error") or "").strip(), int(config["capture"]["maxAssistantChars"]))
    body = "\n".join(
        [
            "Tool failure captured for boundary-signal memory.",
            f"Tool: {tool_name}",
            f"Error: {error or '(empty)'}",
            "Purpose: record failure as a boundary signal (timeout, permission denial, unreachable backend) so future sessions can reason about recurring friction.",
        ]
    )
    queued = queue_payload(
        root,
        config,
        make_memory_payload(
            root=root,
            config=config,
            hook_event_name="PostToolUseFailure",
            input_payload=payload,
            body=body,
            name=f"Tool failure: {tool_name}",
        ),
    )
    log_event(
        root,
        config,
        "post_tool_use_failure",
        {
            "hook_input": payload,
            "queued_file": str(queued),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
