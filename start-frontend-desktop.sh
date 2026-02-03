#!/bin/bash
# PI-Installer Frontend starten (für Desktop-Starter)
# Aufruf: $0 [ --window | --browser ]
#   --window  = Vite + Tauri-App-Fenster (Port 5173)
#   --browser = Vite (Port 3001) + Standard-Browser öffnen
#   ohne Arg  = nur Vite starten (Port 3001)

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
MODE="${1:-}"

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
    kill_port 3001
    echo ""
    exec "$PROJECT_ROOT/start-frontend.sh"
    ;;
esac
