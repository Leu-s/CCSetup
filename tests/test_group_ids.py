from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOOKS_ROOT = ROOT / "templates" / "project" / ".claude" / "hooks"
sys.path.insert(0, str(HOOKS_ROOT))

from lib.group_ids import make_storage_group_id, normalize_logical_group_id, upsert_claude_memory_block, parse_claude_memory_ids

class GroupIdTests(unittest.TestCase):
    def test_storage_id_is_deterministic(self) -> None:
        logical = "Демо / Repo – №1"
        a = make_storage_group_id(logical)
        b = make_storage_group_id(logical)
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("g_"))

    def test_claude_memory_block_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "CLAUDE.md"
            upsert_claude_memory_block(path, "verbalium/mobile-app", "g_verbalium_mobile_app_abcdef0123456789")
            logical, storage = parse_claude_memory_ids(path)
            content = path.read_text(encoding="utf-8")
            self.assertEqual(logical, "verbalium/mobile-app")
            self.assertEqual(storage, "g_verbalium_mobile_app_abcdef0123456789")
            self.assertIn("## Working Principles", content)
            self.assertIn("## Tool Priority", content)
            self.assertIn("codebase-memory-mcp", content)

if __name__ == "__main__":
    unittest.main()
