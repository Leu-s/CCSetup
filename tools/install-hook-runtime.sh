#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
  cat <<'USAGE'
Usage:
  install-hook-runtime.sh <repo-path> [--backend neo4j|falkordb] [--provider openai|openai_generic|gemini]

Creates a dedicated Python runtime in <repo>/.claude/state/graphiti-runtime
and installs the host-side dependencies used by graphiti_flush.py.

Optional environment overrides:
  GRAPHITI_SKIP_PIP_BOOTSTRAP=1     Skip pip/wheel/setuptools self-upgrade.
  GRAPHITI_RUNTIME_PIP_EXTRA_ARGS   Extra arguments appended to pip install commands.
USAGE
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

REPO_PATH="$1"
shift
BACKEND="neo4j"
PROVIDER="openai"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend)
      BACKEND="$2"
      shift 2
      ;;
    --provider)
      PROVIDER="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

GRAPHITI_CORE_VERSION="$({
  python3 - "$REPO_PATH" "$PACKAGE_ROOT/templates/project/.claude/graphiti.json" <<'PY'
import json
import pathlib
import sys
repo = pathlib.Path(sys.argv[1])
template = pathlib.Path(sys.argv[2])
paths = [repo / '.claude' / 'graphiti.json', template]
for path in paths:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        version = ((data.get('engine') or {}).get('graphitiCoreVersion') or '').strip()
        if version:
            print(version)
            raise SystemExit(0)
    except FileNotFoundError:
        continue
    except Exception:
        continue
print('0.28.2')
PY
} 2>/dev/null || echo '0.28.2')"

RUNTIME_DIR="$REPO_PATH/.claude/state/graphiti-runtime"
STAMP_PATH="$REPO_PATH/.claude/state/graphiti-runtime-stamp.json"
mkdir -p "$REPO_PATH/.claude/state"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  PYTHON_BIN="$(command -v python)"
fi

"$PYTHON_BIN" -m venv "$RUNTIME_DIR"
PIP_BIN="$RUNTIME_DIR/bin/pip"
PY_BIN="$RUNTIME_DIR/bin/python"
if [[ ! -x "$PIP_BIN" ]]; then
  PIP_BIN="$RUNTIME_DIR/Scripts/pip.exe"
  PY_BIN="$RUNTIME_DIR/Scripts/python.exe"
fi

PIP_EXTRA_ARGS=()
if [[ -n "${GRAPHITI_RUNTIME_PIP_EXTRA_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  PIP_EXTRA_ARGS=( ${GRAPHITI_RUNTIME_PIP_EXTRA_ARGS} )
fi

if [[ "${GRAPHITI_SKIP_PIP_BOOTSTRAP:-0}" != "1" ]]; then
  "$PIP_BIN" install --upgrade pip wheel setuptools "${PIP_EXTRA_ARGS[@]}" >/dev/null
fi

EXTRAS=()
if [[ "$BACKEND" == "falkordb" ]]; then
  EXTRAS+=("falkordb")
fi
if [[ "$PROVIDER" == "gemini" ]]; then
  EXTRAS+=("google-genai")
fi
if [[ ${#EXTRAS[@]} -gt 0 ]]; then
  EXTRA_SPEC="[${EXTRAS[*]}]"
  EXTRA_SPEC="${EXTRA_SPEC// /,}"
else
  EXTRA_SPEC=""
fi
"$PIP_BIN" install "graphiti-core${EXTRA_SPEC}==${GRAPHITI_CORE_VERSION}" "${PIP_EXTRA_ARGS[@]}" >/dev/null

cat > "$STAMP_PATH" <<STAMP
{
  "installed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "python": "${PY_BIN}",
  "backend": "${BACKEND}",
  "provider": "${PROVIDER}",
  "graphiti_core_version": "${GRAPHITI_CORE_VERSION}"
}
STAMP

echo "Installed Graphiti hook runtime: $PY_BIN"
echo "graphiti-core version: ${GRAPHITI_CORE_VERSION}"
