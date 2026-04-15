from __future__ import annotations

import pathlib
from typing import Any

from .util import append_jsonl, now_utc_iso

def log_event(root: pathlib.Path, config: dict[str, Any], name: str, payload: dict[str, Any]) -> None:
    path = (root / config["queue"]["logsDir"] / "graphiti-hooks.jsonl").resolve()
    append_jsonl(
        path,
        {
            "ts": now_utc_iso(),
            "event": name,
            "payload": payload,
        },
    )
