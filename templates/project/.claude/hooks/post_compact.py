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
            "Post-compact memory checkpoint.",
            f"Compact source: {payload.get('source') or 'unknown'}",
            "Purpose: record a short anchor immediately after Claude compacted the conversation so continuity survives the shortened transcript.",
        ]
    )
    queued = queue_payload(
        root,
        config,
        make_memory_payload(
            root=root,
            config=config,
            hook_event_name="PostCompact",
            input_payload=payload,
            body=body,
            name="Claude Code post-compact checkpoint",
        ),
    )
    log_event(
        root,
        config,
        "post_compact",
        {
            "hook_input": payload,
            "queued_file": str(queued),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
