#!/usr/bin/env bash
# Rescue live temp runtime — Web-UI nur localhost (127.0.0.1:3001).
# Kein sudo, apt, mount, restore, backup.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESCUE_ROOT="${SETUPHELFER_RESCUE_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
DIST="$RESCUE_ROOT/frontend/dist"
SERVE="$RESCUE_ROOT/scripts/serve-frontend-production.py"
HOST="127.0.0.1"
PORT="${SETUPHELFER_RESCUE_UI_PORT:-3001}"

if [[ ! -f "$DIST/index.html" ]]; then
  echo "ERROR: frontend/dist/index.html missing under $RESCUE_ROOT" >&2
  exit 1
fi

if [[ ! -f "$SERVE" ]]; then
  echo "ERROR: serve-frontend-production.py missing at $SERVE" >&2
  exit 1
fi

PYTHON="${SETUPHELFER_RESCUE_PYTHON:-python3}"
echo "Rescue temp runtime: UI http://${HOST}:${PORT}/ (local-only)"
exec "$PYTHON" "$SERVE" --root "$DIST" --host "$HOST" --port "$PORT"
