from __future__ import annotations

import json
import pathlib
import sqlite3
from typing import Any

from .util import now_utc_iso, trim_text

_SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
  payload_id TEXT PRIMARY KEY,
  logical_group_id TEXT NOT NULL,
  storage_group_id TEXT NOT NULL,
  hook_event_name TEXT NOT NULL,
  created_at TEXT NOT NULL,
  session_id TEXT,
  cwd TEXT,
  model TEXT,
  name TEXT NOT NULL,
  episode_body TEXT NOT NULL,
  source TEXT NOT NULL,
  source_description TEXT NOT NULL,
  changed_files_json TEXT,
  trace_json TEXT,
  status TEXT NOT NULL,
  attempts INTEGER NOT NULL DEFAULT 0,
  next_retry_at TEXT,
  delivered_at TEXT,
  last_error TEXT,
  response_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_episodes_status_next_retry ON episodes(status, next_retry_at);
CREATE INDEX IF NOT EXISTS idx_episodes_group_delivered ON episodes(storage_group_id, delivered_at DESC);
"""

def _connect(db_path: pathlib.Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(_SCHEMA)
    return conn

def record_payload(db_path: pathlib.Path, payload: dict[str, Any], *, status: str = "queued", attempts: int = 0, next_retry_at: str | None = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO episodes (
              payload_id, logical_group_id, storage_group_id, hook_event_name, created_at,
              session_id, cwd, model, name, episode_body, source, source_description,
              changed_files_json, trace_json, status, attempts, next_retry_at, delivered_at,
              last_error, response_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["payload_id"],
                payload["logical_group_id"],
                payload["storage_group_id"],
                payload["hook_event_name"],
                payload["created_at"],
                payload.get("session_id"),
                payload.get("cwd"),
                payload.get("model"),
                payload["name"],
                payload["episode_body"],
                payload.get("source", "text"),
                payload.get("source_description", "Claude Code memory checkpoint"),
                json.dumps(payload.get("changed_files") or [], ensure_ascii=False),
                json.dumps(payload.get("trace") or {}, ensure_ascii=False),
                status,
                attempts,
                next_retry_at,
                None,
                None,
                None,
            ),
        )
        conn.commit()

def update_status(
    db_path: pathlib.Path,
    payload_id: str,
    *,
    status: str,
    attempts: int,
    next_retry_at: str | None,
    error: str | None,
    response: Any | None,
) -> None:
    delivered_at = now_utc_iso() if status == "delivered" else None
    with _connect(db_path) as conn:
        conn.execute(
            """
            UPDATE episodes
            SET status = ?, attempts = ?, next_retry_at = ?, delivered_at = ?,
                last_error = ?, response_json = ?
            WHERE payload_id = ?
            """,
            (
                status,
                attempts,
                next_retry_at,
                delivered_at,
                error,
                json.dumps(response, ensure_ascii=False) if response is not None else None,
                payload_id,
            ),
        )
        conn.commit()

def recent_delivered_summaries(
    db_path: pathlib.Path,
    *,
    storage_group_id: str,
    limit: int,
    max_chars_per_episode: int,
    max_total_chars: int,
) -> list[str]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT created_at, hook_event_name, name, episode_body
            FROM episodes
            WHERE storage_group_id = ? AND status = 'delivered'
            ORDER BY delivered_at DESC, created_at DESC
            LIMIT ?
            """,
            (storage_group_id, limit),
        ).fetchall()
    results: list[str] = []
    used = 0
    for created_at, hook_event_name, name, episode_body in rows:
        summary = f"[{created_at}] {hook_event_name} — {name}\n{trim_text(episode_body, max_chars_per_episode)}"
        if used + len(summary) > max_total_chars and results:
            break
        used += len(summary)
        results.append(summary)
    return results

def ledger_metrics(db_path: pathlib.Path) -> dict[str, Any]:
    if not db_path.exists():
        return {
            "exists": False,
            "counts": {},
            "latest_created_at": None,
        }
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT status, COUNT(*) FROM episodes GROUP BY status").fetchall()
        latest = conn.execute("SELECT MAX(created_at) FROM episodes").fetchone()[0]
    return {
        "exists": True,
        "counts": {status: count for status, count in rows},
        "latest_created_at": latest,
    }
