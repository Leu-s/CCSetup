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


class BaselineDoctorTests(unittest.TestCase):
    def test_repo_declarations_and_npx_fallback_make_baseline_doctor_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
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

            env = {
                **os.environ,
                "HOME": str(fake_home),
                "PATH": f"{fake_bin}:{os.environ.get('PATH', '')}",
                "CODEBASE_MEMORY_MCP_BIN": str(fake_bin / "codebase-memory-mcp"),
            }
            result = subprocess.run(
                [sys.executable, str(BASELINE_DOCTOR), str(repo)],
                check=True,
                capture_output=True,
                text=True,
                env=env,
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


if __name__ == "__main__":
    unittest.main()
