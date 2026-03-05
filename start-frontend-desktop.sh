#!/bin/bash
# PI-Installer Frontend starten (für Desktop-Starter)
# Aufruf: $0 [ --window | --tauri | --browser ]
#   --window, --tauri = Vite + Tauri-App-Fenster (Port 5173)
#   --browser        = Vite (Port 3001) + Standard-Browser öffnen
#   ohne Arg         = nur Vite starten (Port 3001)
# Siehe: docs/START_APPS.md

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
MODE="${1:-}"
BACKEND_URL="http://127.0.0.1:8000"
BACKEND_MAX_WAIT=60
BACKEND_POLL_INTERVAL=2

wait_for_backend() {
  local waited=0
  while [ $waited -lt $BACKEND_MAX_WAIT ]; do
    if curl -sS --max-time 2 "$BACKEND_URL/api/version" >/dev/null 2>&1; then
      return 0
    fi
    sleep $BACKEND_POLL_INTERVAL
    waited=$((waited + BACKEND_POLL_INTERVAL))
    printf "."
  done
  return 1
}

ensure_backend_running() {
  if curl -sS --max-time 2 "$BACKEND_URL/api/version" >/dev/null 2>&1; then
    echo "✅ Backend läuft bereits auf :8000"
    return 0
  fi

  echo "📡 Backend nicht erreichbar auf :8000 – starte Backend im Hintergrund..."
  "$PROJECT_ROOT/start-backend.sh" >/tmp/pi-installer-backend.log 2>&1 &
  echo -n "   Warte auf Backend-Ready"
  if ! wait_for_backend; then
    echo ""
    echo "❌ Backend konnte nicht rechtzeitig gestartet werden."
    echo "   Log: /tmp/pi-installer-backend.log"
    return 1
  fi
  echo ""
  echo "✅ Backend bereit"
  return 0
}

kill_port() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    local pid
    pid=$(lsof -t -i:"$port" 2>/dev/null)
    if [ -n "$pid" ]; then
      echo "⏹  Beende Prozess auf Port $port (PID $pid)..."
      kill $pid 2>/dev/null
      sleep 2
      if lsof -t -i:"$port" >/dev/null 2>&1; then
        kill -9 $(lsof -t -i:"$port") 2>/dev/null
        sleep 1
      fi
    fi
  fi
}

case "$MODE" in
  --window|--tauri)
    echo "🚀 PI-Installer Frontend (App-Fenster)"
    echo "======================================="
    ensure_backend_running || exit 1
    kill_port 5173
    echo ""
    cd "$FRONTEND_DIR" || exit 1
    if [ ! -d "node_modules" ]; then
      echo "📦 Installiere Dependencies..."
      npm install
    fi
    exec npm run tauri:dev
    ;;
  --browser)
    echo "🚀 PI-Installer Frontend (Browser)"
    echo "==================================="
    ensure_backend_running || exit 1
    kill_port 3001
    echo ""
    cd "$FRONTEND_DIR" || exit 1
    if [ ! -d "node_modules" ]; then
      echo "📦 Installiere Dependencies..."
      npm install
    fi
    echo "✅ Starte Vite auf http://localhost:3001"
    echo "   Browser öffnet sich gleich..."
    echo ""
    npm run dev &
    VITE_PID=$!
    sleep 5
    if command -v xdg-open >/dev/null 2>&1; then
      xdg-open "http://localhost:3001" 2>/dev/null
    elif command -v sensible-browser >/dev/null 2>&1; then
      sensible-browser "http://localhost:3001" 2>/dev/null
    else
      echo "💡 Browser bitte manuell öffnen: http://localhost:3001"
    fi
    wait $VITE_PID
    ;;
  *)
    echo "🚀 PI-Installer Frontend starten"
    echo "================================="
    ensure_backend_running || exit 1
    kill_port 3001
    echo ""
    exec "$PROJECT_ROOT/start-frontend.sh"
    ;;
esac
