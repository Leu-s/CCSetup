from __future__ import annotations

import datetime as _dt
import json
import os
import pathlib
import shutil
import tempfile
import traceback
import uuid
from typing import Any

UTC = _dt.timezone.utc


def project_dir() -> pathlib.Path:
    value = os.environ.get("CLAUDE_PROJECT_DIR")
    if value:
        return pathlib.Path(value).expanduser().resolve()
    return pathlib.Path.cwd().resolve()


def now_utc() -> _dt.datetime:
    return _dt.datetime.now(tz=UTC)


def now_utc_iso() -> str:
    return now_utc().isoformat()


def parse_iso(value: str | None) -> _dt.datetime | None:
    if not value:
        return None
    try:
        return _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def read_text(path: pathlib.Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return default


def read_json(path: pathlib.Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def atomic_write_text(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def atomic_write_json(path: pathlib.Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def append_jsonl(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def load_stdin_json(default: dict[str, Any] | None = None) -> dict[str, Any]:
    import sys

    raw = sys.stdin.read()
    if not raw.strip():
        return default or {}
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return default or {}


def trim_text(value: str, limit: int) -> str:
    value = (value or "").strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def new_payload_id() -> str:
    return str(uuid.uuid4())


def safe_traceback(exc: BaseException) -> str:
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).strip()


def shell_export_line(key: str, value: str) -> str:
    safe = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'export {key}="{safe}"\n'


def write_session_exports(exports: dict[str, str]) -> None:
    env_file_value = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file_value:
        return
    env_file = pathlib.Path(env_file_value)
    env_file.parent.mkdir(parents=True, exist_ok=True)
    with env_file.open("a", encoding="utf-8") as handle:
        for key, value in exports.items():
            handle.write(shell_export_line(key, value))


def hook_json_output(*, hook_event_name: str, additional_context: str | None = None, watch_paths: list[str] | None = None, decision: str | None = None, reason: str | None = None, updated_mcp_tool_output: Any | None = None) -> str:
    payload: dict[str, Any] = {}
    if decision:
        payload["decision"] = decision
    if reason:
        payload["reason"] = reason
    hook_specific: dict[str, Any] = {"hookEventName": hook_event_name}
    if additional_context is not None:
        hook_specific["additionalContext"] = additional_context
    if watch_paths is not None:
        hook_specific["watchPaths"] = watch_paths
    if updated_mcp_tool_output is not None:
        hook_specific["updatedMCPToolOutput"] = updated_mcp_tool_output
    if len(hook_specific) > 1:
        payload["hookSpecificOutput"] = hook_specific
    return json.dumps(payload, ensure_ascii=False)


def backup_file(path: pathlib.Path, backup_root: pathlib.Path) -> pathlib.Path | None:
    if not path.exists():
        return None
    backup_root.mkdir(parents=True, exist_ok=True)
    target = backup_root / path.name
    if path.is_dir():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(path, target)
    else:
        shutil.copy2(path, target)
    return target
