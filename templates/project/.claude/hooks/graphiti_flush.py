#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from lib.adapters import ingest_payload
from lib.config import ensure_state_dirs, load_config
from lib.observability import log_event
from lib.queue_store import due_spool_files, load_spool_file, mark_dead_letter, mark_delivered, set_retry
from lib.util import atomic_write_json, now_utc, now_utc_iso, parse_iso, project_dir, safe_traceback


def _lock_path(root: pathlib.Path, config: dict) -> pathlib.Path:
    return (root / config["queue"]["locksDir"] / "graphiti-flush.lock").resolve()


def _stale_lock(path: pathlib.Path, *, max_age_seconds: int) -> bool:
    if not path.exists():
        return False
    try:
        created = parse_iso(path.read_text(encoding="utf-8").strip())
    except Exception:
        created = None
    if created is not None:
        age = (now_utc() - created).total_seconds()
        return age >= max_age_seconds
    age = time.time() - path.stat().st_mtime
    return age >= max_age_seconds


def _acquire_lock(root: pathlib.Path, config: dict) -> pathlib.Path | None:
    path = _lock_path(root, config)
    path.parent.mkdir(parents=True, exist_ok=True)
    max_age_seconds = int(config["queue"].get("flushLockMaxAgeSeconds") or 900)
    if _stale_lock(path, max_age_seconds=max_age_seconds):
        path.unlink(missing_ok=True)
        log_event(root, config, "flush_lock_recovered", {"lock_path": str(path), "max_age_seconds": max_age_seconds})
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(now_utc_iso())
        return path
    except FileExistsError:
        return None


def _release_lock(path: pathlib.Path | None) -> None:
    if path and path.exists():
        path.unlink(missing_ok=True)


def _next_retry_iso(config: dict, attempts: int) -> str:
    queue = config["queue"]
    base = int(queue["baseRetrySeconds"])
    max_seconds = int(queue["maxRetrySeconds"])
    delay = min(base * max(1, 2 ** max(0, attempts - 1)), max_seconds)
    return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(time.time() + delay))


def run_flush(*, limit: int, dry_run: bool) -> int:
    root = project_dir()
    config = load_config(root)
    ensure_state_dirs(root, config)

    lock_path = _acquire_lock(root, config)
    if lock_path is None:
        return 0

    processed = 0
    delivered = 0
    retried = 0
    dead_lettered = 0
    try:
        for path in due_spool_files(root, config, limit=limit):
            wrapped = load_spool_file(path)
            payload = wrapped.get("payload") or {}
            meta = wrapped.get("meta") or {}
            attempts = int(meta.get("attempts", 0))
            if dry_run:
                log_event(root, config, "flush_dry_run", {"spool_file": str(path), "payload_id": payload.get("payload_id")})
                processed += 1
                continue
            try:
                response = ingest_payload(root, config, payload)
                mark_delivered(root, config, path, response=response)
                log_event(root, config, "flush_delivered", {"spool_file": str(path), "payload_id": payload.get("payload_id"), "response": response})
                delivered += 1
            except Exception as exc:
                attempts += 1
                error = safe_traceback(exc)
                if attempts >= int(config["queue"]["maxAttempts"]):
                    mark_dead_letter(root, config, path, error=error)
                    log_event(root, config, "flush_dead_letter", {"spool_file": str(path), "payload_id": payload.get("payload_id"), "error": error})
                    dead_lettered += 1
                else:
                    next_retry_at = _next_retry_iso(config, attempts)
                    set_retry(root, config, path, attempts=attempts, next_retry_at=next_retry_at, error=error)
                    log_event(root, config, "flush_retry", {"spool_file": str(path), "payload_id": payload.get("payload_id"), "attempts": attempts, "next_retry_at": next_retry_at, "error": error})
                    retried += 1
            processed += 1
        atomic_write_json(
            (root / config["queue"]["lastFlushPath"]).resolve(),
            {
                "finished_at": now_utc_iso(),
                "limit": limit,
                "dry_run": dry_run,
                "processed": processed,
                "delivered": delivered,
                "retried": retried,
                "dead_lettered": dead_lettered,
            },
        )
        return 0
    finally:
        _release_lock(lock_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Flush queued Graphiti payloads into Graphiti.")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return run_flush(limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
