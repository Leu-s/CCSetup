from __future__ import annotations

import copy
import os
import pathlib
import re
from typing import Any

from .util import atomic_write_json, project_dir, read_json

_ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)(?::-([^}]*))?\}")

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 2,
    "groupIds": {
        "prefix": "g",
        "maxSlugChars": 40,
        "hashChars": 16,
        "registryPath": ".claude/state/graphiti-group-registry.json",
    },
    "capture": {
        "sourceDescription": "Claude Code memory checkpoint",
        "maxAssistantChars": 6000,
        "maxChangedFiles": 50,
        "maxGitStatusLines": 100,
    },
    "recall": {
        "maxEpisodes": 5,
        "maxCharsPerEpisode": 1000,
        "maxTotalChars": 5000,
    },
    "queue": {
        "ledgerPath": ".claude/state/graphiti-ledger.sqlite3",
        "spoolDir": ".claude/state/graphiti-spool",
        "archiveDir": ".claude/state/graphiti-archive",
        "deadLetterDir": ".claude/state/graphiti-dead-letter",
        "logsDir": ".claude/state/logs",
        "locksDir": ".claude/state/locks",
        "lastFlushPath": ".claude/state/graphiti-last-flush.json",
        "engineStatePath": ".claude/state/graphiti-engine-state.json",
        "bootstrapReceiptsDir": ".claude/state/bootstrap-receipts",
        "bootstrapBackupsDir": ".claude/state/bootstrap-backups",
        "maxAttempts": 6,
        "baseRetrySeconds": 30,
        "maxRetrySeconds": 3600,
        "flushLockMaxAgeSeconds": 900,
    },
    "runtime": {
        "preferredPythonEnvVar": "GRAPHITI_HOOK_PYTHON",
        "localRuntimeDir": ".claude/state/graphiti-runtime",
        "runtimeStampPath": ".claude/state/graphiti-runtime-stamp.json",
    },
    "hooks": {
        "watchRelativePaths": [
            "CLAUDE.md",
            ".mcp.json",
            ".claude/settings.json",
            ".claude/settings.local.json",
            ".claude/graphiti.json",
        ],
        "watchMatcher": "CLAUDE.md|.mcp.json|settings.json|settings.local.json|graphiti.json",
    },
    "drift": {
        "blockProjectConfigChanges": True,
        "failDoctorOnWarnings": True,
        "warnOnStorageMismatch": True,
    },
    "mcp": {
        "endpoint": "${GRAPHITI_MCP_ENDPOINT:-http://127.0.0.1:8000/mcp/}",
        "healthUrl": "${GRAPHITI_HEALTH_URL:-http://127.0.0.1:8000/health}",
        "toolName": "add_episode",
        "timeoutSeconds": 30,
    },
    "engine": {
        "mode": "queue",
        "backend": "neo4j",
        "provider": "openai",
        "graphitiCoreVersion": "0.28.2",
        "graphitiMcpRef": "mcp-v1.0.2",
        "neo4j": {
            "uri": "${NEO4J_URI:-bolt://127.0.0.1:7687}",
            "user": "${NEO4J_USER:-neo4j}",
            "password": "${NEO4J_PASSWORD:-demodemo}",
            "database": "${NEO4J_DATABASE:-neo4j}",
        },
        "falkordb": {
            "uri": "${FALKORDB_URI:-redis://127.0.0.1:6379}",
            "database": "${FALKORDB_DATABASE:-default_db}",
        },
        "openai": {
            "model": "${GRAPHITI_OPENAI_MODEL:-gpt-4.1}",
            "smallModel": "${GRAPHITI_OPENAI_SMALL_MODEL:-gpt-4.1-mini}",
            "embeddingModel": "${GRAPHITI_OPENAI_EMBEDDING_MODEL:-text-embedding-3-small}",
        },
        "openai_generic": {
            "baseUrl": "${OPENAI_BASE_URL:-http://127.0.0.1:11434/v1}",
            "apiKey": "${OPENAI_API_KEY:-ollama}",
            "model": "${GRAPHITI_OPENAI_GENERIC_MODEL:-deepseek-r1:7b}",
            "smallModel": "${GRAPHITI_OPENAI_GENERIC_SMALL_MODEL:-deepseek-r1:7b}",
            "embeddingModel": "${GRAPHITI_OPENAI_GENERIC_EMBEDDING_MODEL:-nomic-embed-text}",
            "embeddingDim": 768,
        },
        "gemini": {
            "apiKey": "${GOOGLE_API_KEY:-}",
            "model": "${GRAPHITI_GEMINI_MODEL:-gemini-2.5-flash}",
            "embeddingModel": "${GRAPHITI_GEMINI_EMBEDDING_MODEL:-embedding-001}",
            "rerankerModel": "${GRAPHITI_GEMINI_RERANKER_MODEL:-gemini-2.5-flash-lite}",
        },
    },
    "doctor": {
        "requiredHookEvents": [
            "InstructionsLoaded",
            "SessionStart",
            "CwdChanged",
            "FileChanged",
            "PreCompact",
            "Stop",
            "ConfigChange",
        ],
    },
}


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def expand_env_string(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        default = match.group(2)
        if name in os.environ:
            return os.environ[name]
        if default is not None:
            return default
        raise ValueError(f"Missing required environment variable: {name}")

    return _ENV_PATTERN.sub(repl, value)


def _expand_env(value: Any) -> Any:
    if isinstance(value, str):
        return expand_env_string(value)
    if isinstance(value, list):
        return [_expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: _expand_env(item) for key, item in value.items()}
    return value


def load_config(root: pathlib.Path | None = None) -> dict[str, Any]:
    root = root or project_dir()
    raw = read_json(root / ".claude" / "graphiti.json", default={}) or {}
    merged = _merge_dicts(DEFAULT_CONFIG, raw)
    return _expand_env(merged)


def ensure_state_dirs(root: pathlib.Path, config: dict[str, Any]) -> None:
    queue = config["queue"]
    for rel in [
        queue["spoolDir"],
        queue["archiveDir"],
        queue["deadLetterDir"],
        queue["logsDir"],
        queue["locksDir"],
        queue["bootstrapReceiptsDir"],
        queue["bootstrapBackupsDir"],
    ]:
        (root / rel).mkdir(parents=True, exist_ok=True)
    runtime_dir = root / config["runtime"]["localRuntimeDir"]
    runtime_dir.mkdir(parents=True, exist_ok=True)
    registry_path = root / config["groupIds"]["registryPath"]
    if not registry_path.exists():
        atomic_write_json(registry_path, {"version": 1, "groups": {}})


def state_path(rel_path: str, *, root: pathlib.Path | None = None) -> pathlib.Path:
    root = root or project_dir()
    return (root / rel_path).resolve()


def important_watch_paths(root: pathlib.Path, config: dict[str, Any]) -> list[str]:
    results = []
    for rel in config.get("hooks", {}).get("watchRelativePaths", []):
        results.append(str((root / rel).resolve()))
    return results
