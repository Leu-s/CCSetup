from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "tools" / "graphiti_bootstrap.py"
BASELINE_DOCTOR = ROOT / "tools" / "baseline_doctor.py"


def _bootstrap_repo(tmp_path: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    repo = tmp_path / "repo"
    fake_home = tmp_path / "home"
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir(parents=True, exist_ok=True)

    for name in ("npx", "codebase-memory-mcp"):
        script = fake_bin / name
        script.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        script.chmod(0o755)

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
        env={**os.environ, "CODEBASE_MEMORY_MCP_BIN": str(fake_bin / "codebase-memory-mcp")},
    )

    return repo, fake_home, fake_bin


def _doctor_env(fake_home: pathlib.Path, fake_bin: pathlib.Path) -> dict[str, str]:
    return {
        **os.environ,
        "HOME": str(fake_home),
        "PATH": str(fake_bin),
        "CODEBASE_MEMORY_MCP_BIN": str(fake_bin / "codebase-memory-mcp"),
    }


class BaselineDoctorTests(unittest.TestCase):
    def test_repo_declarations_and_npx_fallback_make_baseline_doctor_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            repo, fake_home, fake_bin = _bootstrap_repo(tmp_path)
            result = subprocess.run(
                [sys.executable, str(BASELINE_DOCTOR), str(repo)],
                check=True,
                capture_output=True,
                text=True,
                env=_doctor_env(fake_home, fake_bin),
            )
            report = json.loads(result.stdout)
            self.assertTrue(report["ok"])
            self.assertTrue(report["repo_plugin_baseline"]["ok"])
            self.assertTrue(report["repo_services"]["graphiti_memory_present"])
            self.assertTrue(report["repo_services"]["codebase_memory"]["resolvable"])
            self.assertTrue(report["local_machine"]["repomix"]["available"])
            self.assertTrue(report["local_machine"]["ccusage"]["available"])
            self.assertFalse(report["local_machine"]["claude_cli_present"])
            self.assertIn("will install repo-declared plugins", "\n".join(report["warnings"]))

    def test_repo_without_memory_overlap_reports_empty_overlap_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            repo, fake_home, fake_bin = _bootstrap_repo(tmp_path)
            result = subprocess.run(
                [sys.executable, str(BASELINE_DOCTOR), str(repo)],
                check=True,
                capture_output=True,
                text=True,
                env=_doctor_env(fake_home, fake_bin),
            )
            report = json.loads(result.stdout)
            repo_services = report["repo_services"]
            self.assertIn("graphiti_overlap_mcps_in_repo", repo_services)
            self.assertEqual(repo_services["graphiti_overlap_mcps_in_repo"], [])
            self.assertTrue(report["ok"])

    def test_repo_with_memory_mcp_is_flagged_as_graphiti_overlap_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            repo, fake_home, fake_bin = _bootstrap_repo(tmp_path)

            mcp_path = repo / ".mcp.json"
            mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
            mcp_data.setdefault("mcpServers", {})["memory"] = {"command": "/usr/bin/false"}
            mcp_path.write_text(json.dumps(mcp_data, ensure_ascii=False, indent=2), encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(BASELINE_DOCTOR), str(repo)],
                check=False,
                capture_output=True,
                text=True,
                env=_doctor_env(fake_home, fake_bin),
            )
            report = json.loads(result.stdout)
            self.assertFalse(report["ok"])
            self.assertIn("memory", report["repo_services"]["graphiti_overlap_mcps_in_repo"])
            joined_errors = "\n".join(report["errors"])
            self.assertIn("memory", joined_errors)
            self.assertIn("Graphiti", joined_errors)


if __name__ == "__main__":
    unittest.main()
