#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import shutil
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
HOOKS_ROOT = ROOT / "templates" / "project" / ".claude" / "hooks"
RULES_ROOT = ROOT / "templates" / "project" / ".claude" / "rules"
CLAUDE_TEMPLATE = ROOT / "templates" / "project" / "CLAUDE.md"

sys.path.insert(0, str(HOOKS_ROOT))
from lib.config import DEFAULT_CONFIG, ensure_state_dirs, load_config
from lib.group_ids import (
    make_storage_group_id,
    normalize_logical_group_id,
    parse_claude_memory_ids,
    register_group_mapping,
    upsert_claude_memory_block,
)
from lib.util import backup_file, now_utc_iso, read_json

MANAGED_HOOK_SCRIPTS = {
    "instructions_loaded.py",
    "session_start.py",
    "cwd_changed.py",
    "file_changed.py",
    "pre_compact.py",
    "graphiti_stop.py",
    "config_drift_guard.py",
}


def _is_managed_graphiti_handler(handler: dict[str, Any]) -> bool:
    command = str((handler or {}).get("command") or "")
    return any(script in command for script in MANAGED_HOOK_SCRIPTS)


def _strip_managed_graphiti_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for group in groups or []:
        hooks = list((group or {}).get("hooks") or [])
        kept_hooks = [hook for hook in hooks if not _is_managed_graphiti_handler(hook)]
        if not kept_hooks:
            continue
        kept_group = copy.deepcopy(group)
        kept_group["hooks"] = kept_hooks
        cleaned.append(kept_group)
    return cleaned


def _merge_dicts_fragment_priority(existing: dict[str, Any], fragment: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(existing or {})
    for key, value in (fragment or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dicts_fragment_priority(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def merge_settings(existing: dict[str, Any], fragment: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(existing or {})
    for key, value in (fragment or {}).items():
        if key == "hooks":
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dicts_fragment_priority(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    result["autoMemoryEnabled"] = fragment.get("autoMemoryEnabled", False)
    hooks = dict(result.get("hooks") or {})
    for event_name, groups in (fragment.get("hooks") or {}).items():
        existing_groups = _strip_managed_graphiti_groups(list(hooks.get(event_name) or []))
        for group in groups:
            existing_groups.append(copy.deepcopy(group))
        hooks[event_name] = existing_groups
    result["hooks"] = hooks
    return result


def _merge_dicts_preserve_existing(base: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base or {})
    for key, value in (existing or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dicts_preserve_existing(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def merge_mcp(existing: dict[str, Any], fragment: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(existing or {})
    servers = dict(result.get("mcpServers") or {})
    for name, spec in (fragment.get("mcpServers") or {}).items():
        current = servers.get(name)
        if isinstance(current, dict) and isinstance(spec, dict):
            servers[name] = _merge_dicts_preserve_existing(spec, current)
        else:
            servers[name] = copy.deepcopy(spec)
    result["mcpServers"] = servers
    return result


def _write_json(path: pathlib.Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _copytree_filtered(src: pathlib.Path, dest: pathlib.Path) -> None:
    shutil.copytree(
        src,
        dest,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )


def _managed_runtime_files(repo: pathlib.Path) -> list[pathlib.Path]:
    managed: list[pathlib.Path] = []
    for source_root, relative_base in [
        (HOOKS_ROOT, pathlib.Path('.claude/hooks')),
        (RULES_ROOT, pathlib.Path('.claude/rules')),
    ]:
        for path in source_root.rglob('*'):
            if path.is_dir():
                continue
            if '__pycache__' in path.parts or path.suffix.lower() in {'.pyc', '.pyo'}:
                continue
            managed.append(repo / relative_base / path.relative_to(source_root))
    managed.append(repo / '.claude/state/.gitignore')
    return managed


def _managed_manifest_path(repo: pathlib.Path, config: dict[str, Any]) -> pathlib.Path:
    return (repo / config['queue']['bootstrapReceiptsDir'] / 'managed-files.json').resolve()


def _load_managed_manifest(path: pathlib.Path) -> list[str]:
    data = read_json(path, default={}) or {}
    return list(data.get('files') or [])


def _save_managed_manifest(path: pathlib.Path, files: list[pathlib.Path], *, repo: pathlib.Path) -> None:
    rel_files = sorted({str(file_path.resolve().relative_to(repo.resolve())) for file_path in files if file_path.exists()})
    _write_json(path, {'files': rel_files, 'updated_at': now_utc_iso()})


def _prune_stale_managed_files(repo: pathlib.Path, *, config: dict[str, Any], current_files: list[pathlib.Path]) -> None:
    manifest_path = _managed_manifest_path(repo, config)
    previous = [repo / rel for rel in _load_managed_manifest(manifest_path)]
    current_set = {path.resolve() for path in current_files}
    for old_path in previous:
        resolved = old_path.resolve()
        if resolved in current_set:
            continue
        if old_path.exists() and old_path.is_file():
            old_path.unlink()


def _copy_runtime(repo: pathlib.Path, *, config: dict[str, Any]) -> None:
    _copytree_filtered(HOOKS_ROOT, repo / '.claude' / 'hooks')
    _copytree_filtered(RULES_ROOT, repo / '.claude' / 'rules')
    state_ignore_src = ROOT / 'templates' / 'project' / '.claude' / 'state' / '.gitignore'
    state_ignore_dst = repo / '.claude' / 'state' / '.gitignore'
    state_ignore_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(state_ignore_src, state_ignore_dst)
    run_hook = repo / '.claude' / 'hooks' / 'run_python.sh'
    if run_hook.exists():
        run_hook.chmod(0o755)
    current_files = _managed_runtime_files(repo)
    _prune_stale_managed_files(repo, config=config, current_files=current_files)
    _save_managed_manifest(_managed_manifest_path(repo, config), current_files, repo=repo)


def _maybe_backup(repo: pathlib.Path, *, config: dict[str, Any], paths: list[pathlib.Path]) -> list[str]:
    backup_root = (repo / config["queue"]["bootstrapBackupsDir"] / now_utc_iso().replace(":", "").replace("+00:00", "z")).resolve()
    saved: list[str] = []
    for path in paths:
        backup = backup_file(path, backup_root)
        if backup:
            saved.append(str(backup))
    return saved


def bootstrap_repo(
    repo: pathlib.Path,
    *,
    backend: str,
    provider: str,
    logical_group_id: str,
    keep_existing_storage_id: bool,
    force: bool,
) -> dict[str, Any]:
    repo.mkdir(parents=True, exist_ok=True)

    config = load_config(repo)
    ensure_state_dirs(repo, config)

    graphiti_cfg_path = repo / ".claude" / "graphiti.json"
    settings_path = repo / ".claude" / "settings.json"
    mcp_path = repo / ".mcp.json"
    claude_path = repo / "CLAUDE.md"
    hooks_path = repo / ".claude" / "hooks"
    rule_path = repo / ".claude" / "rules" / "graphiti-memory.md"
    state_ignore_path = repo / ".claude" / "state" / ".gitignore"

    backups = _maybe_backup(
        repo,
        config=config,
        paths=[claude_path, mcp_path, settings_path, graphiti_cfg_path, hooks_path, rule_path, state_ignore_path],
    )

    if not claude_path.exists() and CLAUDE_TEMPLATE.exists():
        claude_path.write_text(CLAUDE_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")

    _copy_runtime(repo, config=config)

    template_cfg = read_json(ROOT / "templates" / "project" / ".claude" / "graphiti.json", default=DEFAULT_CONFIG) or DEFAULT_CONFIG
    existing_cfg = read_json(graphiti_cfg_path, default={}) or {}
    graphiti_cfg = copy.deepcopy(template_cfg)
    if existing_cfg and not force:
        graphiti_cfg = _merge_dicts_preserve_existing(graphiti_cfg, existing_cfg)
    graphiti_cfg.setdefault("engine", {})
    graphiti_cfg["engine"]["backend"] = backend
    graphiti_cfg["engine"]["provider"] = provider
    _write_json(graphiti_cfg_path, graphiti_cfg)

    template_settings = read_json(ROOT / "templates" / "project" / ".claude" / "settings.graphiti.fragment.json", default={}) or {}
    existing_settings = read_json(settings_path, default={}) or {}
    merged_settings = merge_settings(existing_settings, template_settings)
    _write_json(settings_path, merged_settings)

    template_mcp = read_json(ROOT / "templates" / "project" / ".mcp.graphiti.fragment.json", default={}) or {}
    existing_mcp = read_json(mcp_path, default={}) or {}
    merged_mcp = merge_mcp(existing_mcp, template_mcp)
    _write_json(mcp_path, merged_mcp)

    _, existing_storage = parse_claude_memory_ids(claude_path)
    canonical_storage = make_storage_group_id(
        logical_group_id,
        prefix=config["groupIds"]["prefix"],
        max_slug_chars=int(config["groupIds"]["maxSlugChars"]),
        hash_chars=int(config["groupIds"]["hashChars"]),
    )
    final_storage = existing_storage if keep_existing_storage_id and existing_storage else canonical_storage
    upsert_claude_memory_block(claude_path, logical_group_id, final_storage)

    registry_entry = register_group_mapping(
        repo / config["groupIds"]["registryPath"],
        logical_group_id=logical_group_id,
        storage_group_id=final_storage,
        expected_storage_group_id=canonical_storage,
        project_root=repo,
        force=True,
        note="bootstrap",
    )

    receipt = {
        "bootstrapped_at": now_utc_iso(),
        "repo": str(repo),
        "logical_group_id": logical_group_id,
        "storage_group_id": final_storage,
        "canonical_storage_group_id": canonical_storage,
        "backend": backend,
        "provider": provider,
        "keep_existing_storage_id": keep_existing_storage_id,
        "force": force,
        "registry_entry": registry_entry,
        "backups": backups,
    }
    receipt_name = f"bootstrap-{now_utc_iso().replace(':', '').replace('+00:00', 'z')}.json"
    _write_json((repo / config["queue"]["bootstrapReceiptsDir"] / receipt_name).resolve(), receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Graphiti infrastructure into a repository.")
    parser.add_argument("repo", help="Target repository root")
    parser.add_argument("--backend", choices=["neo4j", "falkordb"], default="neo4j")
    parser.add_argument("--provider", choices=["openai", "openai_generic", "gemini"], default="openai")
    parser.add_argument("--logical-group-id", default="", help="Human-readable memory group id")
    parser.add_argument("--keep-existing-storage-id", action="store_true", help="Adopt the storage id that already exists in CLAUDE.md instead of regenerating a canonical one")
    parser.add_argument("--force", action="store_true", help="Refresh Graphiti project files from the package templates while preserving timestamped backups")
    args = parser.parse_args()

    repo = pathlib.Path(args.repo).expanduser().resolve()
    logical_group_id = normalize_logical_group_id(args.logical_group_id or repo.name)
    receipt = bootstrap_repo(
        repo,
        backend=args.backend,
        provider=args.provider,
        logical_group_id=logical_group_id,
        keep_existing_storage_id=args.keep_existing_storage_id,
        force=args.force,
    )

    print(
        "\n".join(
            [
                f"Installed Graphiti infrastructure into: {repo}",
                f"Logical group id:           {receipt['logical_group_id']}",
                f"Storage group id:           {receipt['storage_group_id']}",
                f"Canonical storage group id: {receipt['canonical_storage_group_id']}",
                f"Backend:                    {receipt['backend']}",
                f"Provider:                   {receipt['provider']}",
                "",
                "Use tools/graphiti_admin.py for repo-scoped operations.",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
