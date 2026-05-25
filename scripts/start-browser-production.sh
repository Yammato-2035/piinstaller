#!/bin/bash
# Setuphelfer – Browser-Oberfläche im Produktionsmodus (stdlib HTTP server auf frontend/dist).
# Kein Vite/Node im Dienstprozess — stabil bei Browser-Reloads und ohne npm zur Laufzeit.
# Backend: setuphelfer-backend.service (nicht hier starten).
#
# systemd: setuphelfer.service → exec python3 …serve-frontend-production.py

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export npm_config_cache="${npm_config_cache:-$REPO_ROOT/.npm-cache}"
mkdir -p "$npm_config_cache"

BACKEND_PORT="${PI_INSTALLER_BACKEND_PORT:-8000}"
BACKEND_HEALTH="${PI_INSTALLER_BACKEND_HEALTH_URL:-http://127.0.0.1:${BACKEND_PORT}/api/version}"

echo "Setuphelfer Web-UI production (static SPA server)"
echo "Backend health: $BACKEND_HEALTH"

backend_ready=0
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sS --max-time 4 "$BACKEND_HEALTH" >/dev/null 2>&1; then
    backend_ready=1
    break
  fi
  if [ "$attempt" -lt 10 ]; then
    sleep 1
  fi
done

if [ "$backend_ready" -ne 1 ]; then
  echo "Backend antwortet nicht unter $BACKEND_HEALTH"
  echo "Standard: sudo systemctl enable --now setuphelfer-backend.service"
  exit 1
fi

DIST_DIR="$REPO_ROOT/frontend/dist"
if [ ! -f "$DIST_DIR/index.html" ]; then
  echo "Frontend-Build fehlt: $DIST_DIR/index.html"
  echo "Bitte vorher bauen/deployen: cd frontend && npm run build"
  exit 1
fi

echo "Frontend: http://127.0.0.1:3001"
exec python3 "$REPO_ROOT/scripts/serve-frontend-production.py" \
  --root "$DIST_DIR" \
  --host 127.0.0.1 \
  --port 3001
