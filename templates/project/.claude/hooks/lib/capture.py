from __future__ import annotations

import pathlib
import subprocess
from typing import Any

from .group_ids import resolve_group_context
from .util import new_payload_id, now_utc_iso, trim_text

def git_changed_files(root: pathlib.Path, *, max_lines: int) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return []
    lines = []
    for raw_line in proc.stdout.splitlines()[:max_lines]:
        if not raw_line.strip():
            continue
        path = raw_line[3:] if len(raw_line) > 3 else raw_line
        lines.append(path.strip())
    # preserve order but deduplicate
    seen: set[str] = set()
    result: list[str] = []
    for item in lines:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result

def make_memory_payload(
    *,
    root: pathlib.Path,
    config: dict[str, Any],
    hook_event_name: str,
    input_payload: dict[str, Any],
    body: str,
    name: str,
) -> dict[str, Any]:
    group = resolve_group_context(root, config)
    capture_cfg = config["capture"]
    changed_files = git_changed_files(root, max_lines=int(capture_cfg.get("maxGitStatusLines", 100)))
    changed_files = changed_files[: int(capture_cfg.get("maxChangedFiles", 50))]
    return {
        "payload_id": new_payload_id(),
        "created_at": now_utc_iso(),
        "logical_group_id": group["logical_group_id"],
        "storage_group_id": group["storage_group_id"],
        "hook_event_name": hook_event_name,
        "session_id": input_payload.get("session_id"),
        "cwd": str(root),
        "model": input_payload.get("model"),
        "name": name,
        "episode_body": trim_text(body, int(capture_cfg.get("maxAssistantChars", 6000)) * 2),
        "source": "text",
        "source_description": capture_cfg.get("sourceDescription", "Claude Code memory checkpoint"),
        "changed_files": changed_files,
        "trace": {
            "hook_event_name": hook_event_name,
            "hook_source": input_payload.get("source"),
            "transcript_path": input_payload.get("transcript_path"),
        },
    }
