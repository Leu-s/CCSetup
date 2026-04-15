#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage:
  install-graphiti-stack.sh <repo-path> [--backend neo4j|falkordb] [--provider openai|openai_generic|gemini] [--logical-group-id VALUE] [--keep-existing-storage-id] [--force]

Example:
  ./tools/install-graphiti-stack.sh /absolute/path/to/repo \
    --backend neo4j \
    --provider openai \
    --logical-group-id verbalium/mobile-app
EOF
}

if [[ $# -lt 1 ]]; then
  usage >&2
  exit 1
fi

REPO_PATH="$1"
shift
BACKEND="neo4j"
PROVIDER="openai"
FORWARD_ARGS=("$REPO_PATH")

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend)
      BACKEND="$2"
      FORWARD_ARGS+=("$1" "$2")
      shift 2
      ;;
    --provider)
      PROVIDER="$2"
      FORWARD_ARGS+=("$1" "$2")
      shift 2
      ;;
    --logical-group-id|--keep-existing-storage-id|--force)
      FORWARD_ARGS+=("$1")
      if [[ "$1" == "--logical-group-id" ]]; then
        FORWARD_ARGS+=("$2")
        shift 2
      else
        shift 1
      fi
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

python3 "$SCRIPT_DIR/graphiti_bootstrap.py" "${FORWARD_ARGS[@]}"
"$SCRIPT_DIR/install-hook-runtime.sh" "$REPO_PATH" --backend "$BACKEND" --provider "$PROVIDER"
"$SCRIPT_DIR/configure-codebase-memory.sh" "$REPO_PATH"
