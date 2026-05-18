#!/bin/bash
# Setuphelfer – Browser-Oberfläche im Produktionsmodus (vite preview auf gebautem frontend/dist).
# Backend: setuphelfer-backend.service (nicht hier starten).
#
# systemd: setuphelfer.service → dieses Skript mit exec npm run preview (Vordergrund, PID 1 = vite).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

export npm_config_cache="${npm_config_cache:-$REPO_ROOT/.npm-cache}"
mkdir -p "$npm_config_cache"

BACKEND_PORT="${PI_INSTALLER_BACKEND_PORT:-8000}"
BACKEND_HEALTH="${PI_INSTALLER_BACKEND_HEALTH_URL:-http://127.0.0.1:${BACKEND_PORT}/api/version}"

echo "Setuphelfer Web-UI production preview"
echo "Backend health: $BACKEND_HEALTH"

if ! curl -sS --max-time 4 "$BACKEND_HEALTH" >/dev/null 2>&1; then
  echo "Backend antwortet nicht unter $BACKEND_HEALTH"
  echo "Standard: sudo systemctl enable --now setuphelfer-backend.service"
  exit 1
fi

export PI_INSTALLER_VITE_CACHE_DIR="${PI_INSTALLER_VITE_CACHE_DIR:-/tmp/setuphelfer-vite-cache}"
mkdir -p "$PI_INSTALLER_VITE_CACHE_DIR"

cd "$REPO_ROOT/frontend"

if [ ! -f "dist/index.html" ]; then
  echo "Frontend-Build fehlt: $REPO_ROOT/frontend/dist/index.html"
  echo "Bitte vorher bauen/deployen: cd frontend && npm run build"
  exit 1
fi

if [ ! -d "node_modules" ]; then
  echo "Frontend node_modules fehlt unter $REPO_ROOT/frontend"
  echo "Bitte einmalig installieren (nicht im Produktivstart): cd frontend && npm install"
  exit 1
fi

echo "Frontend: http://127.0.0.1:3001"
exec npm run preview -- --host 127.0.0.1 --port 3001 --strictPort
