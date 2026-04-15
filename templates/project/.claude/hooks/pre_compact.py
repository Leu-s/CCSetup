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
from lib.util import load_stdin_json, project_dir

def main() -> int:
    root = project_dir()
    config = load_config(root)
    ensure_state_dirs(root, config)
    payload = load_stdin_json(default={})

    body = "\n".join(
        [
            "Pre-compact memory checkpoint.",
            f"Compact source: {payload.get('source') or 'unknown'}",
            "Purpose: preserve a short session checkpoint before Claude compacts context.",
        ]
    )
    queued = queue_payload(
        root,
        config,
        make_memory_payload(
            root=root,
            config=config,
            hook_event_name="PreCompact",
            input_payload=payload,
            body=body,
            name="Claude Code pre-compact checkpoint",
        ),
    )
    log_event(
        root,
        config,
        "pre_compact",
        {
            "hook_input": payload,
            "queued_file": str(queued),
        },
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
