from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "tools" / "graphiti_bootstrap.py"
TEMPLATE_HOOKS = ROOT / "templates" / "project" / ".claude" / "hooks"


class BootstrapHygieneTests(unittest.TestCase):
    def test_bootstrap_ignores_template_cache_artifacts(self) -> None:
        cache_dir = TEMPLATE_HOOKS / "__pycache__"
        dummy = cache_dir / "ignored.cpython-313.pyc"
        cache_dir.mkdir(parents=True, exist_ok=True)
        dummy.write_bytes(b"not-a-real-pyc")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                repo = pathlib.Path(tmp) / "repo"
                subprocess.run(
                    [
                        sys.executable,
                        str(BOOTSTRAP),
                        str(repo),
                        "--backend",
                        "neo4j",
                        "--provider",
                        "openai",
                        "--logical-group-id",
                        "demo/repo",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertFalse((repo / ".claude" / "hooks" / "__pycache__").exists())
        finally:
            dummy.unlink(missing_ok=True)
            shutil.rmtree(cache_dir, ignore_errors=True)

    def test_bootstrap_replaces_managed_groups_but_preserves_custom_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            settings_path = repo / ".claude" / "settings.json"
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            settings_path.write_text(
                json.dumps(
                    {
                        "autoMemoryEnabled": True,
                        "hooks": {
                            "SessionStart": [
                                {
                                    "matcher": "startup",
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/run_python.sh session_start.py --old",
                                        }
                                    ],
                                },
                                {
                                    "matcher": "startup",
                                    "hooks": [
                                        {
                                            "type": "command",
                                            "command": "/usr/local/bin/custom-session-start.sh",
                                        }
                                    ],
                                },
                            ]
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP),
                    str(repo),
                    "--backend",
                    "neo4j",
                    "--provider",
                    "openai",
                    "--logical-group-id",
                    "demo/repo",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            session_groups = settings["hooks"]["SessionStart"]
            commands = [hook["command"] for group in session_groups for hook in group["hooks"]]
            self.assertIn("/usr/local/bin/custom-session-start.sh", commands)
            self.assertEqual(sum("session_start.py" in command for command in commands), 1)
            self.assertFalse(settings["autoMemoryEnabled"])
            self.assertTrue(settings["enabledPlugins"]["ecc@ecc"])
            self.assertTrue(settings["enabledPlugins"]["context-mode@context-mode"])
            self.assertTrue(settings["enabledPlugins"]["ui-ux-pro-max@ui-ux-pro-max-skill"])
            self.assertEqual(
                settings["extraKnownMarketplaces"]["ecc"]["source"]["repo"],
                "affaan-m/everything-claude-code",
            )

    def test_force_prunes_stale_managed_files_from_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP),
                    str(repo),
                    "--backend",
                    "neo4j",
                    "--provider",
                    "openai",
                    "--logical-group-id",
                    "demo/repo",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            stale = repo / ".claude" / "hooks" / "obsolete_graphiti_hook.py"
            stale.write_text("# stale managed hook\n", encoding="utf-8")
            manifest_path = repo / ".claude" / "state" / "bootstrap-receipts" / "managed-files.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            files = set(manifest.get("files") or [])
            files.add(str(stale.relative_to(repo)))
            manifest["files"] = sorted(files)
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP),
                    str(repo),
                    "--backend",
                    "neo4j",
                    "--provider",
                    "openai",
                    "--logical-group-id",
                    "demo/repo",
                    "--force",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertFalse(stale.exists())

    def test_bootstrap_preserves_existing_graphiti_mcp_auth_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            mcp_path = repo / ".mcp.json"
            mcp_path.parent.mkdir(parents=True, exist_ok=True)
            mcp_path.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "graphiti-memory": {
                                "type": "http",
                                "url": "https://graphiti.example.com/mcp/",
                                "headers": {"Authorization": "Bearer ${GRAPHITI_MCP_AUTH_TOKEN}"},
                                "headersHelper": "python3 ~/.claude/bin/graphiti_headers.py",
                            }
                        }
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP),
                    str(repo),
                    "--backend",
                    "neo4j",
                    "--provider",
                    "openai",
                    "--logical-group-id",
                    "demo/repo",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            merged = json.loads(mcp_path.read_text(encoding="utf-8"))
            spec = merged["mcpServers"]["graphiti-memory"]
            self.assertEqual(spec["url"], "https://graphiti.example.com/mcp/")
            self.assertIn("Authorization", spec["headers"])
            self.assertIn("headersHelper", spec)
            self.assertIn("codebase-memory-mcp", merged["mcpServers"])

    def test_bootstrap_seeds_claude_template_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP),
                    str(repo),
                    "--backend",
                    "neo4j",
                    "--provider",
                    "openai",
                    "--logical-group-id",
                    "demo/repo",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            content = (repo / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("## Working Principles", content)
            self.assertIn("## Tool Priority", content)
            self.assertIn("MEMORY_GROUP_ID: demo/repo", content)
            self.assertIn("Graphiti is the canonical long-term memory", content)


if __name__ == "__main__":
    unittest.main()
