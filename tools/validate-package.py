#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
import sys

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

ROOT = pathlib.Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "README.md",
    "TUTORIAL.md",
    "GLOBAL-BASELINE.md",
    "STACK-DECISIONS.md",
    "QUICKSTART.md",
    "INSTALL.md",
    "POST-INSTALL-CHECKLIST.md",
    "USER-MANUAL.md",
    "HOOKS.md",
    "OPERATIONS.md",
    "TROUBLESHOOTING.md",
    "ARCHITECTURE.md",
    "GROUP-ID-POLICY.md",
    "SECURITY.md",
    "CONFIG-REFERENCE.md",
    "CLI-REFERENCE.md",
    "FILE-TREE.md",
    "SUPPORT-MATRIX.md",
    "ops/docker-compose.graphiti-neo4j.yml",
    "ops/docker-compose.graphiti-falkordb.yml",
    "ops/env/graphiti.neo4j.env.example",
    "ops/env/graphiti.falkordb.env.example",
    "ops/config/config-docker-neo4j.openai.yaml",
    "ops/config/config-docker-falkordb.openai.yaml",
    "ops/config/config-docker-neo4j.gemini.yaml",
    "ops/config/config-docker-falkordb.gemini.yaml",
    "ops/examples/mcp.graphiti.remote-bearer.example.json",
    "ops/examples/mcp.graphiti.remote-headers-helper.example.json",
    "ops/systemd/graphiti-flush@.service",
    "ops/systemd/graphiti-flush@.timer",
    "ops/caddy/graphiti.Caddyfile",
    "ops/graphiti-mcp.Dockerfile",
    "templates/project/CLAUDE.md",
    "templates/project/.claude/graphiti.json",
    "templates/project/.claude/settings.graphiti.fragment.json",
    "templates/project/.mcp.graphiti.fragment.json",
    "templates/project/.claude/rules/graphiti-memory.md",
    "templates/project/.claude/state/.gitignore",
    "templates/project/.claude/hooks/run_python.sh",
    "templates/project/.claude/hooks/instructions_loaded.py",
    "templates/project/.claude/hooks/session_start.py",
    "templates/project/.claude/hooks/cwd_changed.py",
    "templates/project/.claude/hooks/file_changed.py",
    "templates/project/.claude/hooks/pre_compact.py",
    "templates/project/.claude/hooks/post_compact.py",
    "templates/project/.claude/hooks/post_tool_use_failure.py",
    "templates/project/.claude/hooks/graphiti_stop.py",
    "templates/project/.claude/hooks/graphiti_flush.py",
    "templates/project/.claude/hooks/graphiti_doctor.py",
    "templates/project/.claude/hooks/graphiti_status.py",
    "templates/project/.claude/hooks/graphiti_requeue.py",
    "templates/project/.claude/hooks/config_drift_guard.py",
    "templates/project/.claude/hooks/lib/__init__.py",
    "templates/project/.claude/hooks/lib/adapters.py",
    "templates/project/.claude/hooks/lib/capture.py",
    "templates/project/.claude/hooks/lib/config.py",
    "templates/project/.claude/hooks/lib/group_ids.py",
    "templates/project/.claude/hooks/lib/ledger.py",
    "templates/project/.claude/hooks/lib/observability.py",
    "templates/project/.claude/hooks/lib/queue_store.py",
    "templates/project/.claude/hooks/lib/runtime.py",
    "templates/project/.claude/hooks/lib/util.py",
    "tools/baseline_doctor.py",
    "tools/configure-codebase-memory.sh",
    "tools/graphiti_bootstrap.py",
    "tools/install-hook-runtime.sh",
    "tools/install-graphiti-stack.sh",
    "tools/graphiti_admin.py",
    "tools/validate-package.py",
    "tests/test_baseline_doctor.py",
    "tests/test_e2e_mock.py",
    "tests/test_group_ids.py",
    "tests/test_admin_wrapper.py",
    "tests/test_bootstrap_hygiene.py",
    "tests/test_install_flow_offline.py",
    "tests/run-tests.sh",
]

FORBIDDEN_PATTERNS = [
    re.compile(r"\bTODO\b"),
    re.compile(r"\bTBD\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"coming soon", re.IGNORECASE),
    re.compile(r"not implemented", re.IGNORECASE),
    re.compile(r"\{\{.+?\}\}"),
]

BINARY_FILE_SUFFIXES = {".pyc", ".pyo"}


def _is_text_file(path: pathlib.Path) -> bool:
    return path.suffix.lower() not in BINARY_FILE_SUFFIXES




def _broken_markdown_links(root: pathlib.Path) -> list[dict[str, str]]:
    broken: list[dict[str, str]] = []
    for path in root.rglob('*.md'):
        try:
            text = path.read_text(encoding='utf-8')
        except Exception:
            continue
        for raw_target in MARKDOWN_LINK_RE.findall(text):
            if '://' in raw_target or raw_target.startswith('#'):
                continue
            target = raw_target.split('#', 1)[0]
            candidate = path.parent / target
            if candidate.exists() or (root / target).exists():
                continue
            broken.append({'file': str(path.relative_to(root)), 'target': target})
    return broken



def _tutorial_entry_points_are_linked(root: pathlib.Path) -> bool:
    readme = (root / 'README.md').read_text(encoding='utf-8')
    tutorial = (root / 'TUTORIAL.md').read_text(encoding='utf-8')
    quickstart = (root / 'QUICKSTART.md').read_text(encoding='utf-8')
    user_manual = (root / 'USER-MANUAL.md').read_text(encoding='utf-8')
    return all(probe in readme for probe in ['[TUTORIAL.md](TUTORIAL.md)', '[QUICKSTART.md](QUICKSTART.md)', '[USER-MANUAL.md](USER-MANUAL.md)']) and 'Claude Code' in tutorial and 'TUTORIAL.md' in user_manual and 'TUTORIAL.md' in quickstart

def _compose_defaults_are_loopback_and_configured(root: pathlib.Path) -> bool:
    required_fragments = [
        '${GRAPHITI_BIND_HOST:-127.0.0.1}:8000:8000',
        'GRAPHITI_MCP_CONFIG_PATH',
        './config:/graphiti-config:ro',
    ]
    for rel in ['ops/docker-compose.graphiti-neo4j.yml', 'ops/docker-compose.graphiti-falkordb.yml']:
        text = (root / rel).read_text(encoding='utf-8')
        if not all(fragment in text for fragment in required_fragments):
            return False
    falkor_text = (root / 'ops/docker-compose.graphiti-falkordb.yml').read_text(encoding='utf-8')
    if ':3000:3000' in falkor_text:
        return False
    return True


def _env_examples_reference_supported_defaults(root: pathlib.Path) -> bool:
    checks = {
        'ops/env/graphiti.neo4j.env.example': ['GRAPHITI_BIND_HOST=127.0.0.1', 'GRAPHITI_MCP_CONFIG_PATH=/graphiti-config/config-docker-neo4j.openai.yaml', 'NEO4J_PASSWORD=demodemo'],
        'ops/env/graphiti.falkordb.env.example': ['GRAPHITI_BIND_HOST=127.0.0.1', 'GRAPHITI_MCP_CONFIG_PATH=/graphiti-config/config-docker-falkordb.openai.yaml', 'SEMAPHORE_LIMIT=1'],
    }
    for rel, probes in checks.items():
        text = (root / rel).read_text(encoding='utf-8')
        if not all(probe in text for probe in probes):
            return False
    return True


def _project_templates_include_codebase_memory_and_claude_sections(root: pathlib.Path) -> bool:
    mcp_text = (root / 'templates/project/.mcp.graphiti.fragment.json').read_text(encoding='utf-8')
    claude_text = (root / 'templates/project/CLAUDE.md').read_text(encoding='utf-8')
    return 'codebase-memory-mcp' in mcp_text and '## Working Principles' in claude_text and '## Tool Priority' in claude_text


def _project_settings_declare_reproducible_plugins(root: pathlib.Path) -> bool:
    settings_text = (root / 'templates/project/.claude/settings.graphiti.fragment.json').read_text(encoding='utf-8')
    return all(
        probe in settings_text
        for probe in [
            '"everything-claude-code@everything-claude-code": true',
            '"context-mode@context-mode": true',
            '"ui-ux-pro-max@ui-ux-pro-max-skill": true',
            'affaan-m/everything-claude-code',
            'mksglu/context-mode',
            'nextlevelbuilder/ui-ux-pro-max-skill',
        ]
    )


def _docs_capture_codebase_memory_bootstrap(root: pathlib.Path) -> bool:
    docs = [
        (root / 'INSTALL.md').read_text(encoding='utf-8'),
        (root / 'QUICKSTART.md').read_text(encoding='utf-8'),
        (root / 'USER-MANUAL.md').read_text(encoding='utf-8'),
    ]
    joined = '\n'.join(docs)
    return 'auto_index' in joined and 'index_repository' in joined





def _docs_capture_baseline_boundaries(root: pathlib.Path) -> bool:
    docs = [
        (root / 'README.md').read_text(encoding='utf-8'),
        (root / 'GLOBAL-BASELINE.md').read_text(encoding='utf-8'),
        (root / 'INSTALL.md').read_text(encoding='utf-8'),
        (root / 'USER-MANUAL.md').read_text(encoding='utf-8'),
    ]
    joined = "\n".join(docs)
    probes = [
        'ECC rules',
        'repomix',
        'ccusage',
        'plugin layer',
    ]
    return all(probe in joined for probe in probes)


def _docs_capture_openai_generic_boundary(root: pathlib.Path) -> bool:
    docs = [
        (root / 'INSTALL.md').read_text(encoding='utf-8'),
        (root / 'SUPPORT-MATRIX.md').read_text(encoding='utf-8'),
    ]
    joined = "\n".join(docs)
    return 'openai_generic' in joined and 'host direct-ingest' in joined

def _docs_capture_supported_platforms(root: pathlib.Path) -> bool:
    docs = [
        (root / 'README.md').read_text(encoding='utf-8'),
        (root / 'INSTALL.md').read_text(encoding='utf-8'),
        (root / 'SUPPORT-MATRIX.md').read_text(encoding='utf-8'),
    ]
    joined = '\n'.join(docs)
    return all(probe in joined for probe in ['Linux', 'macOS', 'WSL']) and 'Windows-native' in joined

def _stale_report_removed(root: pathlib.Path) -> bool:
    return not (root / 'RE-AUDIT-POST-FIX.md').exists()


def _readme_has_claude_code_path_notice(root: pathlib.Path) -> bool:
    readme = (root / 'README.md').read_text(encoding='utf-8')
    readme_lower = readme.lower()
    probes = [
        'recommended install and configuration path',
        'рекомендований шлях встановлення',
    ]
    return 'claude code' in readme_lower and any(probe in readme_lower for probe in probes)


def main() -> int:
    missing = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            missing.append(rel)

    forbidden_cache_files: list[str] = []
    forbidden_matches: list[dict[str, str]] = []
    self_path = pathlib.Path(__file__).resolve()
    for path in ROOT.rglob("*"):
        rel = str(path.relative_to(ROOT))
        if path.resolve() == self_path:
            continue
        if ".git" in path.parts:
            continue
        if "__pycache__" in path.parts or path.suffix.lower() in BINARY_FILE_SUFFIXES:
            forbidden_cache_files.append(rel)
            continue
        if not path.is_file() or not _is_text_file(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for pattern in FORBIDDEN_PATTERNS:
            for match in pattern.finditer(text):
                forbidden_matches.append(
                    {
                        "file": rel,
                        "pattern": pattern.pattern,
                        "match": match.group(0),
                    }
                )

    broken_markdown_links = _broken_markdown_links(ROOT)
    readme_has_claude_code_path_notice = _readme_has_claude_code_path_notice(ROOT)
    compose_defaults_are_loopback_and_configured = _compose_defaults_are_loopback_and_configured(ROOT)
    env_examples_reference_supported_defaults = _env_examples_reference_supported_defaults(ROOT)
    project_templates_include_codebase_memory_and_claude_sections = _project_templates_include_codebase_memory_and_claude_sections(ROOT)
    project_settings_declare_reproducible_plugins = _project_settings_declare_reproducible_plugins(ROOT)
    docs_capture_codebase_memory_bootstrap = _docs_capture_codebase_memory_bootstrap(ROOT)
    stale_report_removed = _stale_report_removed(ROOT)
    docs_capture_supported_platforms = _docs_capture_supported_platforms(ROOT)
    docs_capture_baseline_boundaries = _docs_capture_baseline_boundaries(ROOT)
    docs_capture_openai_generic_boundary = _docs_capture_openai_generic_boundary(ROOT)
    tutorial_entry_points_are_linked = _tutorial_entry_points_are_linked(ROOT)

    report = {
        "ok": not missing and not forbidden_cache_files and not forbidden_matches and not broken_markdown_links and readme_has_claude_code_path_notice and compose_defaults_are_loopback_and_configured and env_examples_reference_supported_defaults and project_templates_include_codebase_memory_and_claude_sections and project_settings_declare_reproducible_plugins and docs_capture_codebase_memory_bootstrap and stale_report_removed and docs_capture_supported_platforms and docs_capture_baseline_boundaries and docs_capture_openai_generic_boundary and tutorial_entry_points_are_linked,
        "missing_required_files": missing,
        "forbidden_cache_files": forbidden_cache_files,
        "forbidden_matches": forbidden_matches,
        "broken_markdown_links": broken_markdown_links,
        "readme_has_claude_code_path_notice": readme_has_claude_code_path_notice,
        "compose_defaults_are_loopback_and_configured": compose_defaults_are_loopback_and_configured,
        "env_examples_reference_supported_defaults": env_examples_reference_supported_defaults,
        "project_templates_include_codebase_memory_and_claude_sections": project_templates_include_codebase_memory_and_claude_sections,
        "project_settings_declare_reproducible_plugins": project_settings_declare_reproducible_plugins,
        "docs_capture_codebase_memory_bootstrap": docs_capture_codebase_memory_bootstrap,
        "stale_report_removed": stale_report_removed,
        "docs_capture_supported_platforms": docs_capture_supported_platforms,
        "docs_capture_baseline_boundaries": docs_capture_baseline_boundaries,
        "docs_capture_openai_generic_boundary": docs_capture_openai_generic_boundary,
        "tutorial_entry_points_are_linked": tutorial_entry_points_are_linked,
        "required_file_count": len(REQUIRED_FILES),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
