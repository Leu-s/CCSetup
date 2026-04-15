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

class EndToEndMockTests(unittest.TestCase):
    def test_stop_flush_and_session_start_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "demo-repo"
            bootstrap = subprocess.run(
                [
                    sys.executable,
                    str(BOOTSTRAP),
                    str(repo),
                    "--backend", "neo4j",
                    "--provider", "openai",
                    "--logical-group-id", "Демо / Repo – №1",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertIn("Storage group id:", bootstrap.stdout)

            registry_path = repo / ".claude" / "state" / "graphiti-group-registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            groups = registry.get("groups", {})
            self.assertEqual(len(groups), 1)
            logical_key = next(iter(groups))
            self.assertIn("Repo", logical_key)

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = str(repo)
            env["GRAPHITI_MOCK_INGEST"] = "1"
            env["GRAPHITI_HEALTH_URL"] = "http://127.0.0.1:65535/health"

            stop_payload = {
                "hook_event_name": "Stop",
                "session_id": "session-123",
                "cwd": str(repo),
                "model": "claude-opus-4-6",
                "transcript_path": str(repo / ".claude" / "state" / "transcript.jsonl"),
                "last_assistant_message": "Зроблено: налаштовано Graphiti і перевірено recovery path.",
                "stop_hook_active": False,
            }
            subprocess.run(
                [sys.executable, str(repo / ".claude" / "hooks" / "graphiti_stop.py")],
                input=json.dumps(stop_payload),
                env=env,
                text=True,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [sys.executable, str(repo / ".claude" / "hooks" / "graphiti_flush.py"), "--limit", "5"],
                env=env,
                text=True,
                check=True,
                capture_output=True,
            )
            session = subprocess.run(
                [sys.executable, str(repo / ".claude" / "hooks" / "session_start.py")],
                input=json.dumps({"hook_event_name": "SessionStart", "source": "startup", "session_id": "session-123"}),
                env=env,
                text=True,
                check=True,
                capture_output=True,
            )
            self.assertIn("Memory checkpoint from previous sessions:", session.stdout)
            self.assertIn("налаштовано Graphiti", session.stdout)

            doctor = subprocess.run(
                [sys.executable, str(repo / ".claude" / "hooks" / "graphiti_doctor.py")],
                env=env,
                text=True,
                capture_output=True,
            )
            report = json.loads(doctor.stdout)
            self.assertTrue(report["config"]["required_hook_events_present"])
            self.assertTrue(report["config"]["graphiti_mcp_present"])
            self.assertTrue(report["group"]["storage_matches_expected"])

if __name__ == "__main__":
    unittest.main()
