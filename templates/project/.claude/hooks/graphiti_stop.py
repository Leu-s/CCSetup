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

    if payload.get("stop_hook_active"):
        return 0

    assistant_text = trim_text((payload.get("last_assistant_message") or "").strip(), int(config["capture"]["maxAssistantChars"]))
    body_lines = [
        "Claude Code turn summary.",
        f"Assistant summary: {assistant_text or '(empty)'}",
    ]
    queued = queue_payload(
        root,
        config,
        make_memory_payload(
            root=root,
            config=config,
            hook_event_name="Stop",
            input_payload=payload,
            body="\n".join(body_lines),
            name="Claude Code stop checkpoint",
        ),
    )
    log_event(
        root,
        config,
        "stop",
        {
            "hook_input": payload,
            "queued_file": str(queued),
        },
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
