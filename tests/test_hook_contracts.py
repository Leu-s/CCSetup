from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "tools" / "graphiti_bootstrap.py"


class HookContractTests(unittest.TestCase):
    def _bootstrap_repo(self, repo: pathlib.Path) -> None:
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
                "verbalium/mobile-app",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def _link_runtime_python(self, repo: pathlib.Path) -> pathlib.Path:
        runtime_python = repo / ".claude" / "state" / "graphiti-runtime" / "bin" / "python"
        runtime_python.parent.mkdir(parents=True, exist_ok=True)
        runtime_python.symlink_to(pathlib.Path(sys.executable))
        return runtime_python

    def test_cwd_and_file_changed_export_runtime_and_watch_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            self._bootstrap_repo(repo)
            self._link_runtime_python(repo)
            env_file = repo / ".claude" / "state" / "session.env"
            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = str(repo)
            env["CLAUDE_ENV_FILE"] = str(env_file)

            cwd_proc = subprocess.run(
                [str(repo / ".claude" / "hooks" / "run_python.sh"), "cwd_changed.py"],
                cwd=repo,
                env=env,
                input=json.dumps({"hook_event_name": "CwdChanged", "cwd": str(repo)}),
                capture_output=True,
                text=True,
                check=True,
            )
            cwd_json = json.loads(cwd_proc.stdout)
            watch_paths = cwd_json["hookSpecificOutput"]["watchPaths"]
            self.assertIn(str((repo / "CLAUDE.md").resolve()), watch_paths)
            self.assertIn("GRAPHITI_HOOK_PYTHON", env_file.read_text(encoding="utf-8"))

            file_proc = subprocess.run(
                [str(repo / ".claude" / "hooks" / "run_python.sh"), "file_changed.py"],
                cwd=repo,
                env=env,
                input=json.dumps({
                    "hook_event_name": "FileChanged",
                    "file_path": str((repo / ".claude" / "settings.json").resolve()),
                    "event": "change",
                }),
                capture_output=True,
                text=True,
                check=True,
            )
            file_json = json.loads(file_proc.stdout)
            self.assertIn(
                str((repo / ".claude" / "settings.json").resolve()),
                file_json["hookSpecificOutput"]["watchPaths"],
            )

    def test_config_change_blocks_invalid_project_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            self._bootstrap_repo(repo)
            settings_path = repo / ".claude" / "settings.json"
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            settings["autoMemoryEnabled"] = True
            settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = str(repo)
            proc = subprocess.run(
                [str(repo / ".claude" / "hooks" / "run_python.sh"), "config_drift_guard.py"],
                cwd=repo,
                env=env,
                input=json.dumps({"hook_event_name": "ConfigChange", "source": "project_settings", "file_path": str(settings_path)}),
                capture_output=True,
                text=True,
                check=True,
            )
            report = json.loads(proc.stdout)
            self.assertEqual(report["decision"], "block")
            self.assertIn("autoMemoryEnabled", report["reason"])

    def test_stale_flush_lock_is_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            self._bootstrap_repo(repo)
            cfg_path = repo / ".claude" / "graphiti.json"
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg["queue"]["flushLockMaxAgeSeconds"] = 1
            cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            lock_path = repo / ".claude" / "state" / "locks" / "graphiti-flush.lock"
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_text("2000-01-01T00:00:00+00:00", encoding="utf-8")

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = str(repo)
            env["GRAPHITI_MOCK_INGEST"] = "1"
            proc = subprocess.run(
                [str(repo / ".claude" / "hooks" / "run_python.sh"), "graphiti_flush.py", "--dry-run", "--limit", "1"],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(proc.returncode, 0)
            last_flush = json.loads((repo / ".claude" / "state" / "graphiti-last-flush.json").read_text(encoding="utf-8"))
            self.assertTrue(last_flush["dry_run"])
            self.assertFalse(lock_path.exists())

    def _install_flush_marker_stub(self, repo: pathlib.Path) -> pathlib.Path:
        flush_script = repo / ".claude" / "hooks" / "graphiti_flush.py"
        marker_path = repo / ".claude" / "state" / "async-flush-marker.txt"
        stub = (
            "#!/usr/bin/env python3\n"
            "import os, pathlib, sys\n"
            "marker = pathlib.Path(os.environ[\"CLAUDE_PROJECT_DIR\"]) / \".claude\" / \"state\" / \"async-flush-marker.txt\"\n"
            "marker.parent.mkdir(parents=True, exist_ok=True)\n"
            "marker.write_text(os.environ.get(\"GRAPHITI_ASYNC_FLUSH\", \"\"), encoding=\"utf-8\")\n"
            "sys.exit(0)\n"
        )
        flush_script.write_text(stub, encoding="utf-8")
        flush_script.chmod(0o755)
        return marker_path

    def _run_stop_hook(self, repo: pathlib.Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["CLAUDE_PROJECT_DIR"] = str(repo)
        return subprocess.run(
            [str(repo / ".claude" / "hooks" / "run_python.sh"), "graphiti_stop.py"],
            cwd=repo,
            env=env,
            input=json.dumps({
                "hook_event_name": "Stop",
                "stop_hook_active": False,
                "last_assistant_message": "test",
            }),
            capture_output=True,
            text=True,
            check=True,
        )

    def test_stop_hook_does_not_spawn_async_flush_when_flag_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            self._bootstrap_repo(repo)
            self._link_runtime_python(repo)
            marker_path = self._install_flush_marker_stub(repo)

            cfg_path = repo / ".claude" / "graphiti.json"
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            self.assertFalse(cfg["queue"]["asyncFlushOnStop"])

            proc = self._run_stop_hook(repo)
            self.assertEqual(proc.returncode, 0)

            deadline = time.monotonic() + 1.0
            while time.monotonic() < deadline:
                if marker_path.exists():
                    break
                time.sleep(0.1)
            self.assertFalse(
                marker_path.exists(),
                "async flush was spawned despite queue.asyncFlushOnStop=false",
            )

    def test_stop_hook_spawns_async_flush_when_flag_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            self._bootstrap_repo(repo)
            self._link_runtime_python(repo)
            marker_path = self._install_flush_marker_stub(repo)

            cfg_path = repo / ".claude" / "graphiti.json"
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            cfg["queue"]["asyncFlushOnStop"] = True
            cfg_path.write_text(
                json.dumps(cfg, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            proc = self._run_stop_hook(repo)
            self.assertEqual(proc.returncode, 0)

            deadline = time.monotonic() + 5.0
            while time.monotonic() < deadline:
                if marker_path.exists():
                    break
                time.sleep(0.1)
            self.assertTrue(
                marker_path.exists(),
                "async flush was not spawned despite queue.asyncFlushOnStop=true",
            )
            self.assertEqual(marker_path.read_text(encoding="utf-8"), "1")

    def test_post_compact_hook_queues_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            self._bootstrap_repo(repo)
            self._link_runtime_python(repo)

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = str(repo)
            proc = subprocess.run(
                [str(repo / ".claude" / "hooks" / "run_python.sh"), "post_compact.py"],
                cwd=repo,
                env=env,
                input=json.dumps({"hook_event_name": "PostCompact", "source": "auto"}),
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(proc.returncode, 0)

            spool_dir = repo / ".claude" / "state" / "graphiti-spool"
            queued = list(spool_dir.glob("*.json"))
            self.assertTrue(queued, "post_compact did not enqueue any payload")
            wrapped = json.loads(queued[-1].read_text(encoding="utf-8"))
            payload = wrapped["payload"]
            self.assertEqual(payload["hook_event_name"], "PostCompact")
            self.assertIn("post-compact", payload["episode_body"].lower())

    def test_post_tool_use_failure_hook_captures_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            self._bootstrap_repo(repo)
            self._link_runtime_python(repo)

            env = os.environ.copy()
            env["CLAUDE_PROJECT_DIR"] = str(repo)
            proc = subprocess.run(
                [str(repo / ".claude" / "hooks" / "run_python.sh"), "post_tool_use_failure.py"],
                cwd=repo,
                env=env,
                input=json.dumps({
                    "hook_event_name": "PostToolUseFailure",
                    "tool_name": "Bash",
                    "tool_error": "timeout after 120s running docker compose",
                    "tool_use_id": "test_use_1",
                }),
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(proc.returncode, 0)

            spool_dir = repo / ".claude" / "state" / "graphiti-spool"
            queued = list(spool_dir.glob("*.json"))
            self.assertTrue(queued, "post_tool_use_failure did not enqueue any payload")
            wrapped = json.loads(queued[-1].read_text(encoding="utf-8"))
            payload = wrapped["payload"]
            self.assertEqual(payload["hook_event_name"], "PostToolUseFailure")
            self.assertIn("Bash", payload["episode_body"])
            self.assertIn("timeout", payload["episode_body"].lower())


if __name__ == "__main__":
    unittest.main()
