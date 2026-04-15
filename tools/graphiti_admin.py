#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _repo_hook_wrapper(repo: pathlib.Path) -> pathlib.Path:
    return repo / ".claude" / "hooks" / "run_python.sh"


def _run(repo: pathlib.Path, script_name: str, args: list[str]) -> int:
    repo = repo.resolve()
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(repo)
    wrapper = _repo_hook_wrapper(repo)
    if wrapper.exists():
        cmd = [str(wrapper), script_name, *args]
    else:
        cmd = [sys.executable, str(repo / ".claude" / "hooks" / script_name), *args]
    proc = subprocess.run(cmd, env=env)
    return proc.returncode


def _bootstrap(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "graphiti_bootstrap.py"),
        str(pathlib.Path(args.repo).resolve()),
        "--backend",
        args.backend,
        "--provider",
        args.provider,
    ]
    if args.logical_group_id:
        cmd.extend(["--logical-group-id", args.logical_group_id])
    if args.keep_existing_storage_id:
        cmd.append("--keep-existing-storage-id")
    if args.force:
        cmd.append("--force")
    return subprocess.run(cmd).returncode


def _install_runtime(args: argparse.Namespace) -> int:
    cmd = [
        str(ROOT / "tools" / "install-hook-runtime.sh"),
        str(pathlib.Path(args.repo).resolve()),
        "--backend",
        args.backend,
        "--provider",
        args.provider,
    ]
    return subprocess.run(cmd).returncode


def _doctor(args: argparse.Namespace) -> int:
    return _run(pathlib.Path(args.repo).resolve(), "graphiti_doctor.py", [])


def _status(args: argparse.Namespace) -> int:
    return _run(pathlib.Path(args.repo).resolve(), "graphiti_status.py", [])


def _flush(args: argparse.Namespace) -> int:
    extra = ["--limit", str(args.limit)]
    if args.dry_run:
        extra.append("--dry-run")
    return _run(pathlib.Path(args.repo).resolve(), "graphiti_flush.py", extra)


def _requeue(args: argparse.Namespace) -> int:
    extra = ["--source", args.source, "--limit", str(args.limit)]
    if args.match:
        extra.extend(["--match", args.match])
    if args.dry_run:
        extra.append("--dry-run")
    return _run(pathlib.Path(args.repo).resolve(), "graphiti_requeue.py", extra)


def _migrate(args: argparse.Namespace) -> int:
    repo = pathlib.Path(args.repo).resolve()
    hooks_root = ROOT / "templates" / "project" / ".claude" / "hooks"
    sys.path.insert(0, str(hooks_root))
    from lib.config import ensure_state_dirs, load_config
    from lib.group_ids import (
        make_storage_group_id,
        normalize_logical_group_id,
        parse_claude_memory_ids,
        register_group_mapping,
        remove_registry_mapping,
        upsert_claude_memory_block,
    )

    logical = normalize_logical_group_id(args.new_logical_group_id)
    config = load_config(repo)
    ensure_state_dirs(repo, config)
    old_logical, old_storage = parse_claude_memory_ids(repo / "CLAUDE.md")
    if not old_logical:
        old_logical = repo.name

    expected = make_storage_group_id(
        logical,
        prefix=config["groupIds"]["prefix"],
        max_slug_chars=int(config["groupIds"]["maxSlugChars"]),
        hash_chars=int(config["groupIds"]["hashChars"]),
    )
    if args.mode == "keep-storage" and old_storage:
        new_storage = old_storage
    else:
        new_storage = expected

    upsert_claude_memory_block(repo / "CLAUDE.md", logical, new_storage)
    registry_path = repo / config["groupIds"]["registryPath"]
    register_group_mapping(
        registry_path,
        logical_group_id=logical,
        storage_group_id=new_storage,
        expected_storage_group_id=expected,
        project_root=repo,
        force=True,
        note=f"migration:{args.mode}",
    )
    if args.drop_old_logical and old_logical and old_logical != logical:
        remove_registry_mapping(registry_path, logical_group_id=old_logical)
    print(f"Migrated logical group id to: {logical}")
    print(f"Effective storage group id: {new_storage}")
    return 0


def _baseline_doctor(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        str(ROOT / "tools" / "baseline_doctor.py"),
        str(pathlib.Path(args.repo).resolve()),
    ]
    return subprocess.run(cmd).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Administrative CLI for the Claude Code Graphiti framework")
    sub = parser.add_subparsers(dest="command", required=True)

    p_bootstrap = sub.add_parser("bootstrap")
    p_bootstrap.add_argument("repo")
    p_bootstrap.add_argument("--backend", choices=["neo4j", "falkordb"], default="neo4j")
    p_bootstrap.add_argument("--provider", choices=["openai", "openai_generic", "gemini"], default="openai")
    p_bootstrap.add_argument("--logical-group-id", default="")
    p_bootstrap.add_argument("--keep-existing-storage-id", action="store_true")
    p_bootstrap.add_argument("--force", action="store_true")
    p_bootstrap.set_defaults(func=_bootstrap)

    p_runtime = sub.add_parser("install-runtime")
    p_runtime.add_argument("repo")
    p_runtime.add_argument("--backend", choices=["neo4j", "falkordb"], default="neo4j")
    p_runtime.add_argument("--provider", choices=["openai", "openai_generic", "gemini"], default="openai")
    p_runtime.set_defaults(func=_install_runtime)

    p_doctor = sub.add_parser("doctor")
    p_doctor.add_argument("repo")
    p_doctor.set_defaults(func=_doctor)

    p_status = sub.add_parser("status")
    p_status.add_argument("repo")
    p_status.set_defaults(func=_status)

    p_flush = sub.add_parser("flush")
    p_flush.add_argument("repo")
    p_flush.add_argument("--limit", default="50")
    p_flush.add_argument("--dry-run", action="store_true")
    p_flush.set_defaults(func=_flush)

    p_requeue = sub.add_parser("requeue")
    p_requeue.add_argument("repo")
    p_requeue.add_argument("--source", choices=["archive", "dead-letter"], required=True)
    p_requeue.add_argument("--match", default="")
    p_requeue.add_argument("--limit", default="50")
    p_requeue.add_argument("--dry-run", action="store_true")
    p_requeue.set_defaults(func=_requeue)

    p_migrate = sub.add_parser("migrate-logical-id")
    p_migrate.add_argument("repo")
    p_migrate.add_argument("--new-logical-group-id", required=True)
    p_migrate.add_argument("--mode", choices=["keep-storage", "new-storage"], default="keep-storage")
    p_migrate.add_argument("--drop-old-logical", action="store_true")
    p_migrate.set_defaults(func=_migrate)

    p_baseline = sub.add_parser("baseline-doctor")
    p_baseline.add_argument("repo")
    p_baseline.set_defaults(func=_baseline_doctor)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
