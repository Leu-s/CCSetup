from __future__ import annotations

import base64
import hashlib
import pathlib
import re
import unicodedata
from typing import Any

from .util import atomic_write_json, now_utc_iso, read_json, read_text

_MEMORY_RE = re.compile(r"(?m)^\s*MEMORY_GROUP_ID:\s*(.+?)\s*$")
_STORAGE_RE = re.compile(r"(?m)^\s*GRAPHITI_STORAGE_GROUP_ID:\s*(.+?)\s*$")

_WORKING_SECTION = [
    "## Working Principles",
    "- Think before coding. Read the relevant files, understand the flow, then change the minimum necessary surface.",
    "- Prefer simplicity. Choose the smallest solution that solves the actual problem without speculative abstractions.",
    "- Make surgical changes. Do not refactor unrelated areas unless the task explicitly requires it.",
    "- Stay goal-driven. Translate the request into clear success criteria and verify that the result actually satisfies them.",
]

_TOOL_SECTION = [
    "## Tool Priority",
    "- Use `codebase-memory-mcp` first for structural questions about symbols, call paths, module relationships, routes, and impact radius.",
    "- Use Graphiti for cross-session memory: decisions, constraints, user preferences, unresolved risks, and important outcomes.",
    "- Use Context7 for current library and framework documentation.",
    "- Use GitHub MCP for issues, pull requests, branches, and repository operations.",
    "- Use raw file reads only after the structural tools have narrowed the search space.",
]

_MEMORY_SECTION = [
    "## Graphiti Memory Contract",
    "- Graphiti is the canonical long-term memory for this repository.",
    "- Use `GRAPHITI_STORAGE_GROUP_ID` for Graphiti memory reads and writes.",
    "- `MEMORY_GROUP_ID` is the human-readable project identity.",
    "- Do not invent or rotate storage group ids during normal work.",
]


def normalize_logical_group_id(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").strip()
    value = re.sub(r"\s+", " ", value)
    if not value:
        raise ValueError("logical group id must not be empty")
    return value


def _slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "group"


def make_storage_group_id(
    logical_group_id: str,
    *,
    prefix: str = "g",
    max_slug_chars: int = 40,
    hash_chars: int = 16,
) -> str:
    logical_group_id = normalize_logical_group_id(logical_group_id)
    slug = _slugify(logical_group_id)[:max_slug_chars].rstrip("_") or "group"
    digest = base64.b32encode(hashlib.sha256(logical_group_id.encode("utf-8")).digest()).decode("ascii").lower().rstrip("=")
    return f"{prefix}_{slug}_{digest[:hash_chars]}"


def parse_claude_memory_ids(claude_path: pathlib.Path) -> tuple[str | None, str | None]:
    text = read_text(claude_path, default="")
    memory = None
    storage = None
    match = _MEMORY_RE.search(text)
    if match:
        memory = match.group(1).strip()
    match = _STORAGE_RE.search(text)
    if match:
        storage = match.group(1).strip()
    return memory, storage


def upsert_claude_memory_block(claude_path: pathlib.Path, logical_group_id: str, storage_group_id: str) -> None:
    text = read_text(claude_path, default="# Project Instructions\n\n")
    lines = text.splitlines()

    def replace_or_append(key: str, value: str) -> None:
        pattern = re.compile(rf"^\s*{re.escape(key)}:\s*.+?$")
        for index, line in enumerate(lines):
            if pattern.match(line):
                lines[index] = f"{key}: {value}"
                return
        if lines and lines[-1].strip():
            lines.append("")
        lines.append(f"{key}: {value}")

    def ensure_section(section: list[str]) -> None:
        title = section[0]
        if title in text:
            return
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend(section)

    replace_or_append("MEMORY_GROUP_ID", logical_group_id)
    replace_or_append("GRAPHITI_STORAGE_GROUP_ID", storage_group_id)

    ensure_section(_WORKING_SECTION)
    ensure_section(_TOOL_SECTION)
    ensure_section(_MEMORY_SECTION)
    claude_path.parent.mkdir(parents=True, exist_ok=True)
    claude_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def load_registry(path: pathlib.Path) -> dict[str, Any]:
    value = read_json(path, default={"version": 1, "groups": {}}) or {"version": 1, "groups": {}}
    value.setdefault("version", 1)
    value.setdefault("groups", {})
    return value


def save_registry(path: pathlib.Path, registry: dict[str, Any]) -> None:
    atomic_write_json(path, registry)


def register_group_mapping(
    registry_path: pathlib.Path,
    *,
    logical_group_id: str,
    storage_group_id: str,
    expected_storage_group_id: str,
    project_root: pathlib.Path,
    force: bool = False,
    note: str | None = None,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    groups = registry.setdefault("groups", {})
    existing = dict(groups.get(logical_group_id) or {})
    existing_storage = existing.get("storage_group_id")
    final_storage = storage_group_id if force or not existing_storage else existing_storage
    roots = sorted(set((existing.get("project_roots") or []) + [str(project_root)]))
    groups[logical_group_id] = {
        "storage_group_id": final_storage,
        "expected_storage_group_id": expected_storage_group_id,
        "updated_at": now_utc_iso(),
        "project_roots": roots,
        "note": note or existing.get("note"),
    }
    save_registry(registry_path, registry)
    return groups[logical_group_id]


def remove_registry_mapping(registry_path: pathlib.Path, *, logical_group_id: str) -> None:
    registry = load_registry(registry_path)
    groups = registry.setdefault("groups", {})
    groups.pop(logical_group_id, None)
    save_registry(registry_path, registry)


def registry_collisions(registry: dict[str, Any]) -> dict[str, list[str]]:
    reverse: dict[str, list[str]] = {}
    for logical, payload in (registry.get("groups") or {}).items():
        storage = (payload or {}).get("storage_group_id")
        if not storage:
            continue
        reverse.setdefault(storage, []).append(logical)
    return {storage: sorted(values) for storage, values in reverse.items() if len(values) > 1}


def resolve_group_context(root: pathlib.Path, config: dict[str, Any]) -> dict[str, Any]:
    claude_path = root / "CLAUDE.md"
    registry_path = root / config["groupIds"]["registryPath"]
    registry = load_registry(registry_path)

    raw_logical, raw_storage = parse_claude_memory_ids(claude_path)
    logical = normalize_logical_group_id(raw_logical or root.name)
    expected = make_storage_group_id(
        logical,
        prefix=config["groupIds"]["prefix"],
        max_slug_chars=int(config["groupIds"]["maxSlugChars"]),
        hash_chars=int(config["groupIds"]["hashChars"]),
    )

    entry = (registry.get("groups") or {}).get(logical) or {}
    storage_source = "expected"
    storage = expected
    if entry.get("storage_group_id"):
        storage = entry["storage_group_id"]
        storage_source = "registry"
    elif raw_storage:
        storage = raw_storage
        storage_source = "claude_md"

    mismatch_sources: dict[str, str] = {}
    if raw_storage and raw_storage != expected:
        mismatch_sources["claude_md"] = raw_storage
    if entry.get("storage_group_id") and entry.get("storage_group_id") != expected:
        mismatch_sources["registry"] = entry["storage_group_id"]

    register_group_mapping(
        registry_path,
        logical_group_id=logical,
        storage_group_id=storage,
        expected_storage_group_id=expected,
        project_root=root,
        force=False,
    )

    return {
        "logical_group_id": logical,
        "storage_group_id": storage,
        "expected_storage_group_id": expected,
        "storage_source": storage_source,
        "storage_mismatch": bool(mismatch_sources),
        "mismatch_sources": mismatch_sources,
        "registry_path": str(registry_path),
    }
