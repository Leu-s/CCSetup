#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: run_python.sh <script-name> [args...]" >&2
  exit 1
fi

SCRIPT_NAME="$1"
shift
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
HOOKS_DIR="$PROJECT_DIR/.claude/hooks"
RUNTIME_DIR="$PROJECT_DIR/.claude/state/graphiti-runtime"

if [[ -n "${GRAPHITI_HOOK_PYTHON:-}" && -x "${GRAPHITI_HOOK_PYTHON}" ]]; then
  PYTHON_BIN="$GRAPHITI_HOOK_PYTHON"
elif [[ -x "$RUNTIME_DIR/bin/python" ]]; then
  PYTHON_BIN="$RUNTIME_DIR/bin/python"
elif [[ -x "$RUNTIME_DIR/Scripts/python.exe" ]]; then
  PYTHON_BIN="$RUNTIME_DIR/Scripts/python.exe"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  PYTHON_BIN="$(command -v python)"
fi

exec "$PYTHON_BIN" "$HOOKS_DIR/$SCRIPT_NAME" "$@"
