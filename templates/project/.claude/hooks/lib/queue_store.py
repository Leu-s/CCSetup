from __future__ import annotations

import pathlib
import shutil
from typing import Any

from .config import state_path
from .ledger import record_payload, update_status
from .util import atomic_write_json, now_utc_iso, parse_iso, read_json

def _queue_dirs(root: pathlib.Path, config: dict[str, Any]) -> dict[str, pathlib.Path]:
    queue = config["queue"]
    return {
        "spool": (root / queue["spoolDir"]).resolve(),
        "archive": (root / queue["archiveDir"]).resolve(),
        "dead": (root / queue["deadLetterDir"]).resolve(),
        "ledger": (root / queue["ledgerPath"]).resolve(),
    }

def make_spool_filename(payload: dict[str, Any]) -> str:
    ts = payload["created_at"].replace(":", "").replace("-", "").replace("+00:00", "z")
    return f"{ts}--{payload['payload_id']}.json"

def queue_payload(root: pathlib.Path, config: dict[str, Any], payload: dict[str, Any]) -> pathlib.Path:
    dirs = _queue_dirs(root, config)
    dirs["spool"].mkdir(parents=True, exist_ok=True)
    path = dirs["spool"] / make_spool_filename(payload)
    wrapped = {
        "payload": payload,
        "meta": {
            "status": "queued",
            "attempts": 0,
            "queued_at": now_utc_iso(),
            "next_retry_at": now_utc_iso(),
            "last_error": None,
        },
    }
    atomic_write_json(path, wrapped)
    record_payload(dirs["ledger"], payload, status="queued", attempts=0, next_retry_at=wrapped["meta"]["next_retry_at"])
    return path

def load_spool_file(path: pathlib.Path) -> dict[str, Any]:
    return read_json(path, default={}) or {}

def due_spool_files(root: pathlib.Path, config: dict[str, Any], *, limit: int) -> list[pathlib.Path]:
    dirs = _queue_dirs(root, config)
    dirs["spool"].mkdir(parents=True, exist_ok=True)
    now = now_utc_iso()
    candidates: list[pathlib.Path] = []
    for path in sorted(dirs["spool"].glob("*.json")):
        wrapped = load_spool_file(path)
        next_retry_at = (((wrapped or {}).get("meta") or {}).get("next_retry_at") or "")
        if not next_retry_at or next_retry_at <= now:
            candidates.append(path)
        if len(candidates) >= limit:
            break
    return candidates

def archive_spool_file(root: pathlib.Path, config: dict[str, Any], path: pathlib.Path) -> pathlib.Path:
    dirs = _queue_dirs(root, config)
    dirs["archive"].mkdir(parents=True, exist_ok=True)
    dest = dirs["archive"] / path.name
    shutil.move(str(path), str(dest))
    return dest

def dead_letter_spool_file(root: pathlib.Path, config: dict[str, Any], path: pathlib.Path) -> pathlib.Path:
    dirs = _queue_dirs(root, config)
    dirs["dead"].mkdir(parents=True, exist_ok=True)
    dest = dirs["dead"] / path.name
    shutil.move(str(path), str(dest))
    return dest

def set_retry(root: pathlib.Path, config: dict[str, Any], path: pathlib.Path, *, attempts: int, next_retry_at: str, error: str) -> None:
    wrapped = load_spool_file(path)
    payload = wrapped.get("payload") or {}
    wrapped.setdefault("meta", {})
    wrapped["meta"]["status"] = "retry"
    wrapped["meta"]["attempts"] = attempts
    wrapped["meta"]["next_retry_at"] = next_retry_at
    wrapped["meta"]["last_error"] = error
    atomic_write_json(path, wrapped)
    update_status(
        (root / config["queue"]["ledgerPath"]).resolve(),
        payload["payload_id"],
        status="retry",
        attempts=attempts,
        next_retry_at=next_retry_at,
        error=error,
        response=None,
    )

def mark_delivered(root: pathlib.Path, config: dict[str, Any], path: pathlib.Path, *, response: Any) -> pathlib.Path:
    wrapped = load_spool_file(path)
    payload = wrapped.get("payload") or {}
    update_status(
        (root / config["queue"]["ledgerPath"]).resolve(),
        payload["payload_id"],
        status="delivered",
        attempts=int((wrapped.get("meta") or {}).get("attempts", 0)),
        next_retry_at=None,
        error=None,
        response=response,
    )
    return archive_spool_file(root, config, path)

def mark_dead_letter(root: pathlib.Path, config: dict[str, Any], path: pathlib.Path, *, error: str) -> pathlib.Path:
    wrapped = load_spool_file(path)
    payload = wrapped.get("payload") or {}
    wrapped.setdefault("meta", {})
    wrapped["meta"]["status"] = "dead_letter"
    wrapped["meta"]["last_error"] = error
    atomic_write_json(path, wrapped)
    update_status(
        (root / config["queue"]["ledgerPath"]).resolve(),
        payload["payload_id"],
        status="dead_letter",
        attempts=int((wrapped.get("meta") or {}).get("attempts", 0)),
        next_retry_at=None,
        error=error,
        response=None,
    )
    return dead_letter_spool_file(root, config, path)
