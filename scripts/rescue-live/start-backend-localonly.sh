#!/usr/bin/env bash
# Rescue live temp runtime — Backend nur localhost (127.0.0.1:8000).
# Kein sudo, apt, mount, restore, backup, partition apply.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESCUE_ROOT="${SETUPHELFER_RESCUE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
BACKEND_DIR="$RESCUE_ROOT/backend"
PORT="${SETUPHELFER_RESCUE_BACKEND_PORT:-8000}"
BIND_HOST="127.0.0.1"

if [[ "${ALLOW_REMOTE_ACCESS:-false}" == "true" || "${ALLOW_REMOTE_ACCESS:-false}" == "1" ]]; then
  echo "ERROR: ALLOW_REMOTE_ACCESS is blocked for rescue temp runtime" >&2
  exit 1
fi

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "ERROR: backend not found under $RESCUE_ROOT" >&2
  exit 1
fi

PYTHON="$BACKEND_DIR/venv/bin/python3"
if [[ ! -x "$PYTHON" ]]; then
  echo "ERROR: bundled venv missing at $PYTHON (no pip/apt sync in rescue-live mode)" >&2
  exit 1
fi

export PI_INSTALLER_SKIP_VENV_SYNC=1
export SETUPHELFER_SKIP_SERVICE_CONFLICT_GUARD=1
export PI_INSTALLER_SKIP_SERVICE_CONFLICT_GUARD=1
unset ALLOW_REMOTE_ACCESS 2>/dev/null || true

cd "$BACKEND_DIR"
echo "Rescue temp runtime: backend http://${BIND_HOST}:${PORT}/ (local-only)"
exec "$PYTHON" -m uvicorn app:app --host "$BIND_HOST" --port "$PORT" --workers 1
