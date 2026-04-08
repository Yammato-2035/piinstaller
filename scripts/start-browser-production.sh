#!/bin/bash
# PI-Installer – Browser-Oberfläche im Produktionsmodus (vite preview auf gebautem frontend/dist).
# Kein Vite-Dev-Server. Backend wird hier NICHT gestartet – einziger Owner: setuphelfer-backend.service
# bzw. manuell ./scripts/start-backend.sh (siehe docs/BETRIEB_REPO_VS_SERVICE.md).
#
# Verwendung:
#   – systemd: setuphelfer.service → ExecStart zeigt auf dieses Skript (nicht auf ./start.sh).
#   – Manuell: ./scripts/start-browser-production.sh  (aus dem Installations- oder Repo-Root)
#
# Entwicklung im Repo: weiterhin ./start.sh (Vite dev).

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_PID=""

BACKEND_PORT="${PI_INSTALLER_BACKEND_PORT:-8000}"
BACKEND_HEALTH="${PI_INSTALLER_BACKEND_HEALTH_URL:-http://127.0.0.1:${BACKEND_PORT}/api/version}"

echo "🚀 PI-Installer – Browser (Produktion, vite preview)"
echo "====================================================="
echo ""

cleanup() {
  echo ""
  echo "🛑 Beende Prozesse..."
  kill "$FRONTEND_PID" 2>/dev/null || true
  exit 0
}

trap cleanup SIGINT SIGTERM

echo "📡 Prüfe Backend (Port ${BACKEND_PORT}, einziger Owner: setuphelfer-backend oder start-backend.sh)..."
if ! curl -sS --max-time 4 "$BACKEND_HEALTH" >/dev/null 2>&1; then
  echo "❌ Backend antwortet nicht unter $BACKEND_HEALTH"
  echo "   Standard (systemd): sudo systemctl enable --now setuphelfer-backend.service"
  echo "   Manuell im Repo:  ./scripts/start-backend.sh"
  exit 1
fi

# Vite-Cache außerhalb von node_modules/.vite (kein EACCES bei restriktiven Rechten)
export PI_INSTALLER_VITE_CACHE_DIR="${PI_INSTALLER_VITE_CACHE_DIR:-/tmp/setuphelfer-vite-cache}"
mkdir -p "$PI_INSTALLER_VITE_CACHE_DIR"

echo "🎨 Frontend (Produktion)..."
cd "$REPO_ROOT/frontend"
if [ ! -d "node_modules" ]; then
  echo "📦 Installiere Frontend-Dependencies..."
  npm install
fi
if [ ! -f "dist/index.html" ]; then
  echo "📦 Erzeuge Produktions-Build (vite build)..."
  npm run build
fi

npm run preview &
FRONTEND_PID=$!

echo ""
echo "✅ Browser-UI: vite preview (gebündeltes dist/)"
echo "📡 Backend:   http://localhost:${BACKEND_PORT}"
echo "🎨 Frontend:  http://localhost:3001"
echo ""

wait
