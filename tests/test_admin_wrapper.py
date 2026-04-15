from __future__ import annotations

import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ADMIN = ROOT / "tools" / "graphiti_admin.py"


class AdminWrapperTests(unittest.TestCase):
    def test_admin_uses_repo_wrapper_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp) / "repo"
            hooks = repo / ".claude" / "hooks"
            hooks.mkdir(parents=True)
            marker = repo / ".claude" / "wrapper-called.txt"
            wrapper = hooks / "run_python.sh"
            wrapper.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "printf '%s\n' \"$1\" > \"${CLAUDE_PROJECT_DIR}/.claude/wrapper-called.txt\"\n",
                encoding="utf-8",
            )
            wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)

            proc = subprocess.run(
                [sys.executable, str(ADMIN), "doctor", str(repo)],
                env={**os.environ, "CLAUDE_PROJECT_DIR": str(repo)},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertTrue(marker.exists())
            self.assertEqual(marker.read_text(encoding="utf-8").strip(), "graphiti_doctor.py")


if __name__ == "__main__":
    unittest.main()
