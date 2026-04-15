from __future__ import annotations

import http.server
import json
import os
import pathlib
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "tools" / "install-graphiti-stack.sh"
ADMIN = ROOT / "tools" / "graphiti_admin.py"


def _write_dummy_cbm_binary(bin_dir: pathlib.Path) -> pathlib.Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    cbm_path = bin_dir / "codebase-memory-mcp"
    cbm_path.write_text(
        """#!/usr/bin/env python3
import json
import os
import pathlib
import sys

log_path = pathlib.Path(os.environ[\"CBM_LOG_PATH\"])
payload = {\"argv\": sys.argv[1:]}
if len(sys.argv) >= 4 and sys.argv[1:4] == [\"config\", \"set\", \"auto_index\"]:
    payload[\"value\"] = sys.argv[4] if len(sys.argv) > 4 else None
elif len(sys.argv) >= 3 and sys.argv[1:3] == [\"cli\", \"index_repository\"]:
    payload[\"repo_path\"] = json.loads(sys.argv[3]).get(\"repo_path\")
with log_path.open(\"a\", encoding=\"utf-8\") as fh:
    fh.write(json.dumps(payload, ensure_ascii=False) + \"\\n\")
print(\"ok\")
""",
        encoding="utf-8",
    )
    cbm_path.chmod(0o755)
    return cbm_path


def _write_dummy_graphiti_wheel(wheelhouse: pathlib.Path) -> pathlib.Path:
    wheelhouse.mkdir(parents=True, exist_ok=True)
    wheel_path = wheelhouse / "graphiti_core-0.28.2-py3-none-any.whl"
    dist_info = "graphiti_core-0.28.2.dist-info"
    with zipfile.ZipFile(wheel_path, "w") as zf:
        zf.writestr("graphiti_core/__init__.py", "__version__ = '0.28.2'\n")
        zf.writestr(
            f"{dist_info}/WHEEL",
            "Wheel-Version: 1.0\nGenerator: offline-test\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
        )
        zf.writestr(
            f"{dist_info}/METADATA",
            "Metadata-Version: 2.1\nName: graphiti-core\nVersion: 0.28.2\nSummary: offline test wheel\n",
        )
        zf.writestr(f"{dist_info}/top_level.txt", "graphiti_core\n")
        zf.writestr(f"{dist_info}/RECORD", "")
    return wheel_path


class _HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


class _TCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class InstallFlowOfflineTests(unittest.TestCase):
    def test_full_install_flow_with_local_runtime_wheel_and_mock_ingest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            wheelhouse = tmp_path / "wheelhouse"
            _write_dummy_graphiti_wheel(wheelhouse)
            repo = tmp_path / "repo"
            cbm_bin = _write_dummy_cbm_binary(tmp_path / "bin")
            cbm_log = tmp_path / "cbm.log"

            with _TCPServer(("127.0.0.1", 0), _HealthHandler) as server:
                host, port = server.server_address
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    env = os.environ.copy()
                    env.update(
                        {
                            "GRAPHITI_SKIP_PIP_BOOTSTRAP": "1",
                            "GRAPHITI_RUNTIME_PIP_EXTRA_ARGS": f"--no-index --find-links {wheelhouse}",
                            "OPENAI_API_KEY": "test-openai-key",
                            "GRAPHITI_HEALTH_URL": f"http://{host}:{port}/health",
                            "GRAPHITI_MCP_ENDPOINT": f"http://{host}:{port}/mcp/",
                            "CLAUDE_PROJECT_DIR": str(repo),
                            "CODEBASE_MEMORY_MCP_BIN": str(cbm_bin),
                            "CBM_LOG_PATH": str(cbm_log),
                        }
                    )

                    install = subprocess.run(
                        [
                            str(INSTALLER),
                            str(repo),
                            "--backend",
                            "neo4j",
                            "--provider",
                            "openai",
                            "--logical-group-id",
                            "verbalium/mobile-app",
                        ],
                        cwd=ROOT,
                        env=env,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    self.assertIn("Installed Graphiti hook runtime:", install.stdout)
                    self.assertIn("Configured codebase-memory-mcp: auto_index=true", install.stdout)
                    self.assertIn("Primed codebase-memory-mcp initial index:", install.stdout)
                    stamp_path = repo / ".claude" / "state" / "graphiti-runtime-stamp.json"
                    stamp = json.loads(stamp_path.read_text(encoding="utf-8"))
                    self.assertEqual(stamp["graphiti_core_version"], "0.28.2")
                    self.assertTrue(pathlib.Path(stamp["python"]).exists())

                    status = subprocess.run(
                        [sys.executable, str(ADMIN), "status", str(repo)],
                        cwd=ROOT,
                        env=env,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    status_json = json.loads(status.stdout)
                    self.assertEqual(status_json["group"]["logical_group_id"], "verbalium/mobile-app")
                    self.assertTrue(status_json["mcp_health"]["ok"])
                    self.assertEqual(status_json["runtime"]["stamp"]["graphiti_core_version"], "0.28.2")
                    self.assertTrue(status_json["runtime"]["selected_python"])
                    self.assertTrue(status_json["mcp"]["codebase_memory_mcp_present"])
                    self.assertTrue(status_json["codebase_memory"]["resolvable"])

                    cbm_events = [json.loads(line) for line in cbm_log.read_text(encoding="utf-8").splitlines() if line.strip()]
                    self.assertTrue(any(event.get("argv", [])[:4] == ["config", "set", "auto_index", "true"] for event in cbm_events))
                    self.assertTrue(any(event.get("argv", [])[:2] == ["cli", "index_repository"] and event.get("repo_path") == str(repo.resolve()) for event in cbm_events))

                    doctor_env = {**env, "GRAPHITI_MOCK_INGEST": "1"}
                    doctor = subprocess.run(
                        [sys.executable, str(ADMIN), "doctor", str(repo)],
                        cwd=ROOT,
                        env=doctor_env,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    doctor_json = json.loads(doctor.stdout)
                    self.assertTrue(doctor_json["ok"])
                    self.assertTrue(doctor_json["config"]["required_hook_events_present"])
                    self.assertTrue(doctor_json["config"]["graphiti_mcp_present"])
                    self.assertTrue(doctor_json["config"]["codebase_memory_mcp_present"])

                    stop_payload = {
                        "hook_event_name": "Stop",
                        "session_id": "offline-install-session",
                        "cwd": str(repo),
                        "model": "claude-opus-4-6",
                        "transcript_path": str(repo / ".claude" / "state" / "transcript.jsonl"),
                        "last_assistant_message": "Інфраструктуру встановлено, flush path готовий, memory contract активний.",
                        "stop_hook_active": False,
                    }
                    subprocess.run(
                        [str(repo / ".claude" / "hooks" / "run_python.sh"), "graphiti_stop.py"],
                        cwd=repo,
                        env=doctor_env,
                        input=json.dumps(stop_payload),
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    subprocess.run(
                        [str(repo / ".claude" / "hooks" / "run_python.sh"), "graphiti_flush.py", "--limit", "5"],
                        cwd=repo,
                        env=doctor_env,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    session = subprocess.run(
                        [str(repo / ".claude" / "hooks" / "run_python.sh"), "session_start.py"],
                        cwd=repo,
                        env=doctor_env,
                        input=json.dumps({"hook_event_name": "SessionStart", "source": "startup", "session_id": "offline-install-session"}),
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    self.assertIn("Memory checkpoint from previous sessions:", session.stdout)
                    self.assertIn("Інфраструктуру встановлено", session.stdout)
                    claude_md = (repo / "CLAUDE.md").read_text(encoding="utf-8")
                    self.assertIn("## Working Principles", claude_md)
                    self.assertIn("## Tool Priority", claude_md)
                finally:
                    server.shutdown()
                    thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
