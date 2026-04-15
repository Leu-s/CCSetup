#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  configure-codebase-memory.sh <repo-path>

Ensures codebase-memory-mcp is ready for the bootstrapped repository:
  - resolves the binary from CODEBASE_MEMORY_MCP_BIN or PATH
  - enables auto_index globally for first-connection indexing
  - primes the initial project index via CLI unless disabled

Environment overrides:
  CODEBASE_MEMORY_MCP_BIN                 Absolute path to the binary (preferred when not on PATH)
  CODEBASE_MEMORY_MCP_SKIP_INITIAL_INDEX  Set to 1 to skip immediate index_repository bootstrap
USAGE
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

REPO_PATH="$1"
REPO_PATH="$(python3 - <<'PY' "$REPO_PATH"
import pathlib, sys
print(pathlib.Path(sys.argv[1]).resolve())
PY
)"

resolve_cbm_bin() {
  if [[ -n "${CODEBASE_MEMORY_MCP_BIN:-}" ]]; then
    printf '%s\n' "$CODEBASE_MEMORY_MCP_BIN"
    return 0
  fi
  if command -v codebase-memory-mcp >/dev/null 2>&1; then
    command -v codebase-memory-mcp
    return 0
  fi
  return 1
}

if ! CBM_BIN="$(resolve_cbm_bin)"; then
  echo "codebase-memory-mcp binary not found. Install it first or set CODEBASE_MEMORY_MCP_BIN." >&2
  exit 1
fi

if [[ ! -x "$CBM_BIN" ]]; then
  echo "Resolved codebase-memory-mcp binary is not executable: $CBM_BIN" >&2
  exit 1
fi

"$CBM_BIN" config set auto_index true >/dev/null

echo "Configured codebase-memory-mcp: auto_index=true"

if [[ "${CODEBASE_MEMORY_MCP_SKIP_INITIAL_INDEX:-0}" != "1" ]]; then
  INDEX_PAYLOAD="$(python3 - <<'PY' "$REPO_PATH"
import json, pathlib, sys
print(json.dumps({"repo_path": str(pathlib.Path(sys.argv[1]).resolve())}, ensure_ascii=False))
PY
)"
  "$CBM_BIN" cli index_repository "$INDEX_PAYLOAD" >/dev/null
  echo "Primed codebase-memory-mcp initial index: $REPO_PATH"
else
  echo "Skipped initial codebase-memory-mcp index_repository bootstrap"
fi
