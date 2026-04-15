#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib.config import ensure_state_dirs, load_config
from lib.ledger import update_status
from lib.queue_store import load_spool_file
from lib.util import atomic_write_json, now_utc_iso, project_dir

def _source_dir(root: pathlib.Path, config: dict, source: str) -> pathlib.Path:
    queue = config["queue"]
    if source == "archive":
        return (root / queue["archiveDir"]).resolve()
    if source == "dead-letter":
        return (root / queue["deadLetterDir"]).resolve()
    raise RuntimeError(f"Unsupported source: {source}")

def main() -> int:
    parser = argparse.ArgumentParser(description="Move archived or dead-letter Graphiti payloads back into the spool queue.")
    parser.add_argument("--source", choices=["archive", "dead-letter"], required=True)
    parser.add_argument("--match", default="")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = project_dir()
    config = load_config(root)
    ensure_state_dirs(root, config)

    src_dir = _source_dir(root, config, args.source)
    spool_dir = (root / config["queue"]["spoolDir"]).resolve()
    spool_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = (root / config["queue"]["ledgerPath"]).resolve()

    moved = 0
    for path in sorted(src_dir.glob("*.json")):
        if args.match and args.match not in path.name:
            continue
        wrapped = load_spool_file(path)
        if not wrapped:
            continue
        wrapped.setdefault("meta", {})
        wrapped["meta"]["status"] = "queued"
        wrapped["meta"]["attempts"] = 0
        wrapped["meta"]["next_retry_at"] = now_utc_iso()
        wrapped["meta"]["last_error"] = None
        wrapped["meta"]["requeued_from"] = args.source
        if args.dry_run:
            print(f"would requeue: {path.name}")
        else:
            dest = spool_dir / path.name
            atomic_write_json(dest, wrapped)
            path.unlink(missing_ok=True)
            payload = wrapped["payload"]
            update_status(
                ledger_path,
                payload["payload_id"],
                status="queued",
                attempts=0,
                next_retry_at=wrapped["meta"]["next_retry_at"],
                error=None,
                response=None,
            )
            print(f"requeued: {path.name}")
        moved += 1
        if moved >= args.limit:
            break
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
