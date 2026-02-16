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

# --- 1. Backend prüfen, ggf. starten ---
echo "🚀 PI-Installer starten"
echo "========================"
echo ""

if curl -sS --max-time 2 "$BACKEND_URL/api/version" >/dev/null 2>&1; then
  echo "✅ Backend läuft bereits auf :8000"
else
  echo "📡 Backend antwortet nicht – starte Backend..."
  if [ -x "$PROJECT_ROOT/start-backend.sh" ]; then
    nohup "$PROJECT_ROOT/start-backend.sh" >>/tmp/pi-installer-backend.log 2>&1 &
    BACKEND_LAUNCH_PID=$!
    disown $BACKEND_LAUNCH_PID 2>/dev/null || true
    echo -n "   Warte auf Backend "
    if wait_for_backend; then
      echo ""
      echo "✅ Backend gestartet"
    else
      echo ""
      echo "❌ Backend antwortet nicht (Timeout nach ${MAX_WAIT}s)."
      kill $BACKEND_LAUNCH_PID 2>/dev/null
      echo "   Alternativ: sudo systemctl start pi-installer.service"
      exit 1
    fi
  else
    echo "   Warte auf Backend (z. B. Service auf Port 8000)..."
    echo -n "   "
    if ! wait_for_backend; then
      echo ""
      echo "❌ Backend antwortet nicht (Timeout nach ${MAX_WAIT}s)."
      echo "   Bitte starten: $PROJECT_ROOT/start-backend.sh"
      echo "   Oder Service: sudo systemctl start pi-installer.service"
      exit 1
    fi
    echo ""
    echo "✅ Backend bereit"
  fi
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
    TAURI_BINARY="$PROJECT_ROOT/frontend/src-tauri/target/release/pi-installer"
    if [ -x "$TAURI_BINARY" ]; then
      # Installation unter /opt: gebaute Binary nutzen (kein Rust/Cargo nötig)
      # Starte im Hintergrund und prüfe ob sie läuft
      echo "Starte Tauri-Binary: $TAURI_BINARY"
      # Log-Datei vorbereiten
      touch /tmp/pi-installer-tauri.log
      chmod 666 /tmp/pi-installer-tauri.log 2>/dev/null || true
      env GDK_BACKEND=x11 "$TAURI_BINARY" >>/tmp/pi-installer-tauri.log 2>&1 &
      TAURI_PID=$!
      sleep 2
      if kill -0 "$TAURI_PID" 2>/dev/null; then
        # Binary läuft, warte auf Beendigung
        wait $TAURI_PID
        exit 0
      else
        # Binary beendete sich sofort (Absturz/Fehler)
        echo "⚠️  Tauri-Binary stürzte ab oder startete nicht."
        if [ -f /tmp/pi-installer-tauri.log ] && [ -s /tmp/pi-installer-tauri.log ]; then
          echo "   Log (letzte 10 Zeilen):"
          tail -10 /tmp/pi-installer-tauri.log | sed 's/^/   /'
        else
          echo "   (Kein Log verfügbar – Binary startete möglicherweise nicht)"
        fi
        echo "   Öffne im Browser..."
        MODE="browser"
      fi
    fi
    # Keine Binary gefunden: Entwicklungsmodus (Cargo) oder Browser-Fallback
    echo "ℹ️  Tauri-Binary nicht gefunden unter: $TAURI_BINARY"
    cd "$PROJECT_ROOT/frontend" || exit 1
    [ ! -d "node_modules" ] && npm install
    if [ "$MODE" = "tauri" ] && command -v cargo >/dev/null 2>&1; then
      # Entwicklungsmodus mit Cargo - nur wenn Schreibrechte vorhanden
      if [ -w "$PROJECT_ROOT/frontend/node_modules" ] && [ -w "$PROJECT_ROOT/frontend/src-tauri" ]; then
        echo "   Versuche Entwicklungsmodus (tauri:dev)..."
        exec env GDK_BACKEND=x11 npm run tauri:dev
      else
        echo "⚠️  Keine Schreibrechte für Entwicklungsmodus (Verzeichnis gehört pi-installer)."
        echo "   Öffne im Browser..."
        MODE="browser"
      fi
    fi
    # Fallback Browser (keine Binary, kein Cargo, oder Binary abgestürzt)
    echo "ℹ️  App-Fenster (Tauri) nicht verfügbar – öffne im Browser..."
    echo ""
    kill_port 3001
    # Prüfe ob Backend läuft (wird vom Service gestartet)
    if ! curl -sS --max-time 2 http://127.0.0.1:8000/api/version >/dev/null 2>&1; then
      echo "⚠️  Backend läuft nicht. Starte Backend..."
      if [ -x "$PROJECT_ROOT/start-backend.sh" ]; then
        nohup "$PROJECT_ROOT/start-backend.sh" >>/tmp/pi-installer-backend.log 2>&1 &
        sleep 3
      fi
    fi
    # Frontend starten (als aktueller User, nicht als pi-installer)
    cd "$PROJECT_ROOT/frontend" || exit 1
    [ ! -d "node_modules" ] && npm install
    echo "✅ Starte Frontend auf http://localhost:3001"
    npm run dev >/tmp/pi-installer-frontend.log 2>&1 &
    VITE_PID=$!
    sleep 5
    # Prüfe ob Frontend läuft
    if kill -0 "$VITE_PID" 2>/dev/null && curl -sS --max-time 2 http://127.0.0.1:3001 >/dev/null 2>&1; then
      echo "✅ Frontend läuft. Öffne Browser..."
      if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "http://localhost:3001" 2>/dev/null &
      elif command -v sensible-browser >/dev/null 2>&1; then
        sensible-browser "http://localhost:3001" 2>/dev/null &
      else
        echo "💡 Browser bitte manuell öffnen: http://localhost:3001"
      fi
      wait $VITE_PID
    else
      echo "❌ Frontend konnte nicht gestartet werden. Log: /tmp/pi-installer-frontend.log"
      [ -f /tmp/pi-installer-frontend.log ] && tail -20 /tmp/pi-installer-frontend.log | sed 's/^/   /'
      exit 1
    fi
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
