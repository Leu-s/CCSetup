#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent

REQUIRED_MARKETPLACES: dict[str, str] = {
    "everything-claude-code": "affaan-m/everything-claude-code",
    "context-mode": "mksglu/context-mode",
    "ui-ux-pro-max-skill": "nextlevelbuilder/ui-ux-pro-max-skill",
}

REQUIRED_ENABLED_PLUGINS: tuple[str, ...] = (
    "everything-claude-code@everything-claude-code",
    "context-mode@context-mode",
    "ui-ux-pro-max@ui-ux-pro-max-skill",
)

FORBIDDEN_REPO_MCP_DUPLICATES: tuple[str, ...] = (
    "context7",
    "github",
    "sequential-thinking",
)

FORBIDDEN_GRAPHITI_OVERLAP_MCPS: tuple[str, ...] = (
    "memory",
)



_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")


def _expand_shell_style_env(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        default = match.group(2)
        current = os.environ.get(name)
        if current not in (None, ""):
            return current
        return default or ""

    return _ENV_PATTERN.sub(repl, value)

def _read_json(path: pathlib.Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _resolve_command(command: str | None) -> dict[str, Any]:
    if not command:
        return {"present": False, "command": None, "expanded": None, "resolvable": False}
    expanded = _expand_shell_style_env(os.path.expandvars(command))
    candidate = pathlib.Path(expanded).expanduser()
    if candidate.is_absolute() or "/" in expanded or "\\" in expanded:
        resolvable = candidate.exists()
    else:
        resolvable = shutil.which(expanded) is not None
    return {
        "present": True,
        "command": command,
        "expanded": expanded,
        "resolvable": resolvable,
    }


def _claude_config_dir() -> pathlib.Path:
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        return pathlib.Path(os.environ["CLAUDE_CONFIG_DIR"]).expanduser().resolve()
    return pathlib.Path.home() / ".claude"


def _plugin_cache_hits(plugins_dir: pathlib.Path) -> dict[str, bool]:
    if not plugins_dir.exists():
        return {plugin_id: False for plugin_id in REQUIRED_ENABLED_PLUGINS}
    results: dict[str, bool] = {}
    haystack = "\n".join(str(path).lower() for path in plugins_dir.rglob("*"))
    for plugin_id in REQUIRED_ENABLED_PLUGINS:
        plugin_name = plugin_id.split("@", 1)[0].lower()
        results[plugin_id] = plugin_name in haystack
    return results


def _repo_plugin_baseline(settings: dict[str, Any]) -> dict[str, Any]:
    enabled = dict(settings.get("enabledPlugins") or {})
    marketplaces = dict(settings.get("extraKnownMarketplaces") or {})

    enabled_status = {plugin_id: enabled.get(plugin_id) is True for plugin_id in REQUIRED_ENABLED_PLUGINS}
    marketplace_status: dict[str, dict[str, Any]] = {}
    for market_name, expected_repo in REQUIRED_MARKETPLACES.items():
        spec = marketplaces.get(market_name) or {}
        source = spec.get("source") if isinstance(spec, dict) else {}
        if isinstance(source, dict):
            actual_repo = source.get("repo")
            actual_source_type = source.get("source")
        else:
            actual_repo = spec.get("repo") if isinstance(spec, dict) else None
            actual_source_type = spec.get("source") if isinstance(spec, dict) else None
        marketplace_status[market_name] = {
            "present": market_name in marketplaces,
            "expected_repo": expected_repo,
            "actual_repo": actual_repo,
            "expected_source_type": "github",
            "actual_source_type": actual_source_type,
            "matches": actual_repo == expected_repo and actual_source_type == "github",
        }

    ok = all(enabled_status.values()) and all(item["matches"] for item in marketplace_status.values())
    return {
        "enabled_plugins": enabled_status,
        "marketplaces": marketplace_status,
        "ok": ok,
    }


def _command_or_npx_available(name: str) -> dict[str, Any]:
    direct = shutil.which(name)
    npx = shutil.which("npx")
    return {
        "direct": direct,
        "via_npx": bool(npx),
        "available": bool(direct or npx),
    }


def _user_plugin_preferences(user_settings: dict[str, Any]) -> dict[str, Any]:
    enabled = dict(user_settings.get("enabledPlugins") or {})
    return {plugin_id: enabled.get(plugin_id) for plugin_id in REQUIRED_ENABLED_PLUGINS}


def _ecc_rules_state(repo: pathlib.Path, claude_dir: pathlib.Path) -> dict[str, Any]:
    def collect(base: pathlib.Path) -> dict[str, Any]:
        common_dir = base / "common"
        language_dirs = sorted(
            child.name
            for child in base.iterdir()
            if child.is_dir() and child.name != "common"
        ) if base.exists() else []
        return {
            "rules_dir": str(base),
            "rules_dir_present": base.exists(),
            "common_rules_present": common_dir.is_dir(),
            "language_rule_dirs": language_dirs,
        }

    user_rules = collect(claude_dir / "rules")
    project_rules = collect(repo / ".claude" / "rules")
    any_common = user_rules["common_rules_present"] or project_rules["common_rules_present"]
    any_language = bool(user_rules["language_rule_dirs"] or project_rules["language_rule_dirs"])
    return {
        "user": user_rules,
        "project": project_rules,
        "any_common_rules_present": any_common,
        "any_language_rules_present": any_language,
        "full_ecc_rules_surface_ready": any_common,
    }


def _graphiti_overlap_in_servers(servers: dict[str, Any]) -> list[str]:
    return sorted(name for name in FORBIDDEN_GRAPHITI_OVERLAP_MCPS if name in servers)


def _graphiti_overlap_in_user_scope(claude_dir: pathlib.Path) -> list[str]:
    user_mcp = _read_json(claude_dir / ".mcp.json", {}) or {}
    servers = user_mcp.get("mcpServers") if isinstance(user_mcp, dict) else None
    if not isinstance(servers, dict):
        return []
    return _graphiti_overlap_in_servers(servers)


def _graphiti_overlap_from_plugins(claude_dir: pathlib.Path) -> list[dict[str, str]]:
    # Plugin manifest shapes vary across cache layouts, so this scan is best-effort:
    # we read installed_plugins.json for the authoritative install path, then inspect
    # any .mcp.json / plugin.json / mcp-*.json files inside it for an mcpServers entry.
    installed = _read_json(claude_dir / "plugins" / "installed_plugins.json", {}) or {}
    plugins = installed.get("plugins") if isinstance(installed, dict) else None
    if not isinstance(plugins, dict):
        return []

    manifest_names = {"plugin.json", ".mcp.json", "mcp.json", "mcp-servers.json"}
    results: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for plugin_id, entries in plugins.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            install_path_raw = entry.get("installPath")
            if not isinstance(install_path_raw, str) or not install_path_raw:
                continue
            install_path = pathlib.Path(install_path_raw).expanduser()
            if not install_path.exists():
                continue
            for manifest_path in install_path.rglob("*"):
                if not manifest_path.is_file():
                    continue
                if manifest_path.name not in manifest_names:
                    continue
                data = _read_json(manifest_path, None)
                if not isinstance(data, dict):
                    continue
                servers = data.get("mcpServers")
                if not isinstance(servers, dict):
                    continue
                for name in _graphiti_overlap_in_servers(servers):
                    key = (plugin_id, name)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append({"plugin_id": plugin_id, "mcp_name": name})

    results.sort(key=lambda item: (item["plugin_id"], item["mcp_name"]))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the retained Claude Code ecosystem baseline")
    parser.add_argument("repo", nargs="?", default=".", help="Bootstrapped repository path")
    args = parser.parse_args()

    repo = pathlib.Path(args.repo).resolve()
    settings_path = repo / ".claude" / "settings.json"
    mcp_path = repo / ".mcp.json"
    if not settings_path.exists():
        print(json.dumps({"ok": False, "errors": [f"Missing project settings: {settings_path}"]}, ensure_ascii=False, indent=2))
        return 1

    project_settings = _read_json(settings_path, {}) or {}
    project_mcp = _read_json(mcp_path, {}) or {}
    mcp_servers = dict(project_mcp.get("mcpServers") or {})
    claude_dir = _claude_config_dir()
    user_settings = _read_json(claude_dir / "settings.json", {}) or {}
    plugins_dir = claude_dir / "plugins"

    repo_plugin_baseline = _repo_plugin_baseline(project_settings)
    graphiti_present = "graphiti-memory" in mcp_servers
    codebase_memory_status = _resolve_command((mcp_servers.get("codebase-memory-mcp") or {}).get("command") if isinstance(mcp_servers.get("codebase-memory-mcp"), dict) else None)
    duplicate_repo_mcps = sorted(name for name in FORBIDDEN_REPO_MCP_DUPLICATES if name in mcp_servers)
    graphiti_overlap_in_repo = _graphiti_overlap_in_servers(mcp_servers)
    graphiti_overlap_in_user_scope = _graphiti_overlap_in_user_scope(claude_dir)
    graphiti_overlap_from_plugins = _graphiti_overlap_from_plugins(claude_dir)
    ecc_rules = _ecc_rules_state(repo, claude_dir)

    local_machine = {
        "claude_cli_present": shutil.which("claude") is not None,
        "repomix": _command_or_npx_available("repomix"),
        "ccusage": _command_or_npx_available("ccusage"),
        "codebase_memory": codebase_memory_status,
        "claude_config_dir": str(claude_dir),
        "user_settings_present": (claude_dir / "settings.json").exists(),
        "plugins_dir_present": plugins_dir.exists(),
        "user_plugin_preferences": _user_plugin_preferences(user_settings),
        "plugin_cache_hits": _plugin_cache_hits(plugins_dir),
        "ecc_rules": ecc_rules,
        "graphiti_overlap_mcps_in_user_scope": graphiti_overlap_in_user_scope,
        "graphiti_overlap_mcps_from_plugins": graphiti_overlap_from_plugins,
    }

    errors: list[str] = []
    warnings: list[str] = []

    if not repo_plugin_baseline["ok"]:
        errors.append("Project settings do not declare the required plugin baseline reproducibly")
    if not graphiti_present:
        errors.append("Project .mcp.json is missing graphiti-memory")
    if not codebase_memory_status["present"]:
        errors.append("Project .mcp.json is missing codebase-memory-mcp")
    elif not codebase_memory_status["resolvable"]:
        errors.append("codebase-memory-mcp command is not resolvable")
    if duplicate_repo_mcps:
        errors.append("Project .mcp.json duplicates ECC-provided MCPs")
    if graphiti_overlap_in_repo:
        errors.append(
            "Project .mcp.json declares "
            + ", ".join(graphiti_overlap_in_repo)
            + " which overlaps with Graphiti (the canonical long-term memory layer)"
        )
    if not local_machine["repomix"]["available"]:
        errors.append("repomix is not invocable directly or via npx")
    if not local_machine["ccusage"]["available"]:
        errors.append("ccusage is not invocable directly or via npx")
    if not local_machine["claude_cli_present"]:
        warnings.append("claude CLI is not installed on this machine; plugin install state cannot be exercised here")
    if not local_machine["plugins_dir_present"]:
        warnings.append("~/.claude/plugins is absent; plugin caches are not installed locally yet")
    if not any(local_machine["plugin_cache_hits"].values()):
        warnings.append("No retained plugins are present in the local plugin cache yet; Claude Code will install repo-declared plugins on first trusted open")
    if local_machine["repomix"]["direct"] is None and local_machine["repomix"]["via_npx"]:
        warnings.append("repomix is currently available only via npx; the first invocation may require network access unless npm cache is already warm")
    if local_machine["ccusage"]["direct"] is None and local_machine["ccusage"]["via_npx"]:
        warnings.append("ccusage is currently available only via npx; the first invocation may require network access unless npm cache is already warm")
    if not ecc_rules["any_common_rules_present"]:
        warnings.append("ECC plugin surfaces are declared, but ECC rules are not present locally or in the repo yet. Claude Code plugins cannot distribute ECC rules automatically; install them via the ECC upstream installer or copy rules/common and the language directories you need.")
    if graphiti_overlap_in_user_scope:
        warnings.append(
            "User-scope .mcp.json declares "
            + ", ".join(graphiti_overlap_in_user_scope)
            + " which overlaps with Graphiti; disable it in user settings so Graphiti remains the canonical memory layer"
        )
    if graphiti_overlap_from_plugins:
        pairs = ", ".join(
            f"{item['plugin_id']}:{item['mcp_name']}"
            for item in graphiti_overlap_from_plugins
        )
        warnings.append(
            "Retained plugin bundles ship MCPs that overlap with Graphiti ("
            + pairs
            + "); the framework forbids using these — disable them in plugin settings so Graphiti remains the canonical memory layer"
        )

    report = {
        "repo_dir": str(repo),
        "repo_plugin_baseline": repo_plugin_baseline,
        "repo_services": {
            "graphiti_memory_present": graphiti_present,
            "codebase_memory": codebase_memory_status,
            "forbidden_ecc_mcp_duplicates": duplicate_repo_mcps,
            "graphiti_overlap_mcps_in_repo": graphiti_overlap_in_repo,
        },
        "local_machine": local_machine,
        "notes": [
            "Project .claude/settings.json is the canonical reproducibility surface for ECC, context-mode, and ui-ux-pro-max-skill.",
            "Claude Code installs repo-declared plugins at session start in cloud sessions and prompts locally when the repo is trusted.",
            "Local plugin cache presence is informative; repo declarations are the authoritative baseline contract for the plugin layer only.",
            "repomix and ccusage remain operator-local CLI utilities; repo settings do not install them for you.",
            "ECC rules are an upstream-owned surface. The plugin layer does not distribute them automatically, so install rules via ECC or copy the needed rule directories into .claude/rules when you want the full ECC rules surface.",
        ],
        "warnings": warnings,
        "errors": errors,
        "ok": not errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
