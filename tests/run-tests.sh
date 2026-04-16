#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export ROOT_DIR

cleanup_cache() {
  find "$ROOT_DIR" -type d -name '__pycache__' -prune -exec rm -rf {} +
  find "$ROOT_DIR" -type f -name '*.pyc' -delete
}

python3 -m compileall "$ROOT_DIR/templates/project/.claude/hooks" "$ROOT_DIR/tools" "$ROOT_DIR/tests" >/dev/null
cleanup_cache

bash -n "$ROOT_DIR/tools/install-graphiti-stack.sh"
bash -n "$ROOT_DIR/tools/install-hook-runtime.sh"
bash -n "$ROOT_DIR/tools/configure-codebase-memory.sh"
bash -n "$ROOT_DIR/templates/project/.claude/hooks/run_python.sh"
bash -n "$ROOT_DIR/tests/run-tests.sh"

python3 - <<'PY'
import json
import os
import pathlib
import re

root = pathlib.Path(os.environ['ROOT_DIR'])
for path in root.rglob('*.json'):
    json.loads(path.read_text(encoding='utf-8'))

for md_path in root.rglob('*.md'):
    text = md_path.read_text(encoding='utf-8')
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
        if '://' in target or target.startswith('#'):
            continue
        target = target.split('#', 1)[0]
        candidate = md_path.parent / target
        if not candidate.exists() and not (root / target).exists():
            raise SystemExit(f'broken markdown link: {md_path} -> {target}')
print('static_json_and_docs_ok')
PY

python3 "$ROOT_DIR/tools/validate-package.py" >/dev/null

if command -v systemd-analyze >/dev/null 2>&1; then
  tmp_repo="$(mktemp -d)"
  unit_dir="$(mktemp -d)"
  mkdir -p "$tmp_repo/.claude/hooks"
  escaped="$(systemd-escape --path "$tmp_repo")"
  cp "$ROOT_DIR/ops/systemd/graphiti-flush@.service" "$unit_dir/graphiti-flush@${escaped}.service"
  cp "$ROOT_DIR/ops/systemd/graphiti-flush@.timer" "$unit_dir/graphiti-flush@${escaped}.timer"
  systemd-analyze verify "$unit_dir/graphiti-flush@${escaped}.service" "$unit_dir/graphiti-flush@${escaped}.timer" >/dev/null 2>&1
  rm -rf "$tmp_repo" "$unit_dir"
fi

if command -v docker >/dev/null 2>&1; then
  # Compose services load env from ${HOME}/.claude/graphiti.{neo4j,falkordb}.env with
  # required=false, so `config` resolves even when those files are absent. Tests exercise
  # that path — we do not pre-create files under $HOME.
  docker compose -f "$ROOT_DIR/ops/docker-compose.graphiti-neo4j.yml" config >/dev/null
  docker compose -f "$ROOT_DIR/ops/docker-compose.graphiti-falkordb.yml" config >/dev/null
fi

python3 -m unittest discover -s "$ROOT_DIR/tests" -p "test_*.py"
cleanup_cache
