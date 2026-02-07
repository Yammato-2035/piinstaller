#!/bin/bash
# PI-Installer – Startet zuerst Backend, wartet auf Ready, dann Auswahl (Tauri/Browser/Frontend)
# Für Desktop-Starter: Backend im Hintergrund, dann gewählte Ausgabemöglichkeit
# Siehe: docs/START_APPS.md

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_URL="http://127.0.0.1:8000"
MAX_WAIT=60
POLL_INTERVAL=2

wait_for_backend() {
  local waited=0
  while [ $waited -lt $MAX_WAIT ]; do
    if curl -sS --max-time 2 "$BACKEND_URL/api/version" >/dev/null 2>&1; then
      return 0
    fi
    sleep $POLL_INTERVAL
    waited=$((waited + POLL_INTERVAL))
    printf "."
  done
  return 1
}

# --- 1. Backend prüfen / starten ---
echo "🚀 PI-Installer starten"
echo "========================"
echo ""

if curl -sS --max-time 2 "$BACKEND_URL/api/version" >/dev/null 2>&1; then
  echo "✅ Backend läuft bereits auf :8000"
else
  echo "📡 Starte Backend..."
  cd "$PROJECT_ROOT/backend" || exit 1
  if [ ! -d "venv" ]; then
    python3 -m venv venv
  fi
  source venv/bin/activate
  if ! python3 -c "import fastapi" 2>/dev/null; then
    pip install -r requirements.txt --only-binary :all: 2>/dev/null || pip install -r requirements.txt
  fi
  python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 &
  BACKEND_PID=$!
  echo -n "   Warte auf Backend-Ready"
  if ! wait_for_backend; then
    echo ""
    echo "❌ Backend konnte nicht gestartet werden (Timeout nach ${MAX_WAIT}s)."
    kill $BACKEND_PID 2>/dev/null
    exit 1
  fi
  echo ""
  echo "✅ Backend bereit"
fi
echo ""

# --- 2. Auswahl (Tauri, Browser, Nur Frontend) ---
MODE=""
if [ -n "$PI_INSTALLER_MODE" ]; then
  MODE="$PI_INSTALLER_MODE"
elif command -v zenity >/dev/null 2>&1; then
  MODE=$(zenity --list --radiolist \
    --title="PI-Installer starten" \
    --text="Wie soll PI-Installer geöffnet werden?" \
    --column="" --column="Option" --column="Beschreibung" \
    TRUE "tauri" "App-Fenster (Tauri, empfohlen)" \
    FALSE "browser" "Im Standard-Browser öffnen" \
    FALSE "frontend" "Nur Vite-Server (Port 3001)" \
    --width=450 --height=220 2>/dev/null)
elif command -v kdialog >/dev/null 2>&1; then
  MODE=$(kdialog --radiolist "PI-Installer starten" tauri "App-Fenster (Tauri)" on browser "Im Browser" off frontend "Nur Vite-Server" off 2>/dev/null)
fi

if [ -z "$MODE" ]; then
  # Fallback: Terminal-Auswahl
  echo "Wie soll PI-Installer geöffnet werden?"
  echo "  1) App-Fenster (Tauri)"
  echo "  2) Browser"
  echo "  3) Nur Vite-Server (Port 3001)"
  echo -n "Wahl [1]: "
  read -r choice
  case "${choice:-1}" in
    2) MODE="browser" ;;
    3) MODE="frontend" ;;
    *) MODE="tauri" ;;
  esac
fi

# --- 3. Gewählte Option starten ---
cd "$PROJECT_ROOT" || exit 1

kill_port() {
  local port="$1"
  local pid
  pid=$(lsof -t -i:"$port" 2>/dev/null)
  if [ -n "$pid" ]; then
    kill $pid 2>/dev/null
    sleep 2
    pid=$(lsof -t -i:"$port" 2>/dev/null)
    [ -n "$pid" ] && kill -9 $pid 2>/dev/null
  fi
}

case "$MODE" in
  tauri)
    echo "🎨 Starte PI-Installer (App-Fenster)..."
    echo "   (GDK_BACKEND=x11 für stabiles Rendering unter Wayland)"
    echo ""
    kill_port 5173
    cd "$PROJECT_ROOT/frontend" || exit 1
    [ ! -d "node_modules" ] && npm install
    exec env GDK_BACKEND=x11 npm run tauri:dev
    ;;
  browser)
    echo "🌐 Starte PI-Installer (Browser)..."
    echo ""
    kill_port 3001
    cd "$PROJECT_ROOT/frontend" || exit 1
    [ ! -d "node_modules" ] && npm install
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
  frontend|*)
    echo "🎨 Starte PI-Installer (nur Vite-Server)..."
    echo ""
    exec "$PROJECT_ROOT/start-frontend.sh"
    ;;
esac
