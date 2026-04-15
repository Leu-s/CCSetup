#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib.config import ensure_state_dirs, load_config
from lib.group_ids import resolve_group_context
from lib.ledger import recent_delivered_summaries
from lib.observability import log_event
from lib.runtime import selected_runtime_python
from lib.util import load_stdin_json, project_dir, write_session_exports


def main() -> int:
    root = project_dir()
    config = load_config(root)
    ensure_state_dirs(root, config)
    payload = load_stdin_json(default={})
    group = resolve_group_context(root, config)

    ledger_path = (root / config["queue"]["ledgerPath"]).resolve()
    recall_cfg = config["recall"]
    summaries = recent_delivered_summaries(
        ledger_path,
        storage_group_id=group["storage_group_id"],
        limit=int(recall_cfg["maxEpisodes"]),
        max_chars_per_episode=int(recall_cfg["maxCharsPerEpisode"]),
        max_total_chars=int(recall_cfg["maxTotalChars"]),
    )

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

    log_event(
        root,
        config,
        "session_start",
        {
            "hook_input": payload,
            "logical_group_id": group["logical_group_id"],
            "storage_group_id": group["storage_group_id"],
            "summary_count": len(summaries),
            "selected_python": selected_python,
        },
    )

    if not summaries:
        print(
            "\n".join(
                [
                    "Graphiti memory checkpoint for this repository:",
                    f"- Logical memory group: {group['logical_group_id']}",
                    f"- Storage namespace: {group['storage_group_id']}",
                    f"- Backend / provider: {config['engine']['backend']} / {config['engine']['provider']}",
                    "- No delivered memory checkpoints exist in this local ledger yet.",
                    "- On a fresh machine or fresh clone this is expected until this workspace records and flushes its own checkpoints.",
                    "- If you need older shared history immediately, query the Graphiti MCP tools directly for this storage namespace.",
                ]
            )
        )
        return 0

    body = [
        "Memory checkpoint from previous sessions:",
        f"- Logical memory group: {group['logical_group_id']}",
        f"- Storage namespace: {group['storage_group_id']}",
        f"- Backend / provider: {config['engine']['backend']} / {config['engine']['provider']}",
        "- Use GRAPHITI_STORAGE_GROUP_ID for Graphiti tool calls.",
        "",
    ]
    for index, summary in enumerate(summaries, start=1):
        body.append(f"{index}. {summary}")
        body.append("")
    print("\n".join(body).rstrip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
