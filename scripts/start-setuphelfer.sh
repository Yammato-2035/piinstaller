#!/bin/bash
# SetupHelfer – Startet zuerst Backend, wartet auf Ready, dann Auswahl (Tauri-App / Browser / Nur Backend)
# Für Desktop-Starter: Backend im Hintergrund, dann gewählte Ausgabemöglichkeit
# SETUPHELFER_MODE oder PI_INSTALLER_MODE=tauri|browser|backend|frontend (frontend = nur Vite; PI_* = Legacy)
# Siehe: docs/START_APPS.md

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
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
echo "🚀 SetupHelfer starten"
echo "======================="
echo ""

if curl -sS --max-time 2 "$BACKEND_URL/api/version" >/dev/null 2>&1; then
  echo "✅ Backend läuft bereits auf :8000"
else
  echo "📡 Backend antwortet nicht – starte Backend..."
  if [ -x "$PROJECT_ROOT/scripts/start-backend.sh" ]; then
    nohup "$PROJECT_ROOT/scripts/start-backend.sh" >>/tmp/setuphelfer-backend.log 2>&1 &
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
      echo "   Alternativ: sudo systemctl start setuphelfer.service"
      exit 1
    fi
  else
    echo "   Warte auf Backend (z. B. Service auf Port 8000)..."
    echo -n "   "
    if ! wait_for_backend; then
      echo ""
      echo "❌ Backend antwortet nicht (Timeout nach ${MAX_WAIT}s)."
      echo "   Bitte starten: $PROJECT_ROOT/scripts/start-backend.sh"
      echo "   Oder Service: sudo systemctl start setuphelfer.service"
      exit 1
    fi
    echo ""
    echo "✅ Backend bereit"
  fi
fi
echo ""

# --- 2. Auswahl (Tauri-App, Browser, Nur Backend) ---
MODE=""
if [ -n "${SETUPHELFER_MODE:-}" ]; then
  MODE="$SETUPHELFER_MODE"
elif [ -n "${PI_INSTALLER_MODE:-}" ]; then
  MODE="$PI_INSTALLER_MODE"
elif command -v zenity >/dev/null 2>&1; then
  MODE=$(zenity --list --radiolist \
    --title="SetupHelfer starten" \
    --text="Wie soll SetupHelfer geöffnet werden?" \
    --column="" --column="Option" --column="Beschreibung" \
    TRUE "tauri" "Desktop-App (Tauri, empfohlen)" \
    FALSE "browser" "Weboberfläche im Standard-Browser" \
    FALSE "backend" "Nur Backend (API auf Port 8000, kein Fenster)" \
    --width=520 --height=260 2>/dev/null)
elif command -v kdialog >/dev/null 2>&1; then
  MODE=$(kdialog --radiolist "SetupHelfer starten" \
    tauri "Desktop-App (Tauri)" on \
    browser "Im Browser" off \
    backend "Nur Backend (API)" off 2>/dev/null)
fi

if [ -z "$MODE" ]; then
  # Fallback: Terminal-Auswahl
  echo "Wie soll SetupHelfer geöffnet werden?"
  echo "  1) Desktop-App (Tauri)"
  echo "  2) Browser (Weboberfläche)"
  echo "  3) Nur Backend (API, kein Fenster)"
  echo -n "Wahl [1]: "
  read -r choice
  case "${choice:-1}" in
    2) MODE="browser" ;;
    3) MODE="backend" ;;
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

# Liest Versions-String aus dem Repo (nur Anzeige; blockiert nicht bei Fehler).
setuphelfer_read_repo_version() {
  local vf="$PROJECT_ROOT/config/version.json"
  if [ ! -f "$vf" ]; then
    echo "?"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('version','?'))" "$vf" 2>/dev/null || echo "?"
  else
    echo "?"
  fi
}

# Verhindert stilles Starten einer veralteten Release-Tauri aus dem Entwicklungs-Repo,
# wenn eine aktuellere Binary unter /opt/setuphelfer existiert.
# Überspringen: SETUPHELFER_ALLOW_OLD_REPO_TAURI=1
setuphelfer_block_stale_repo_tauri_if_needed() {
  [ "$MODE" = "tauri" ] || return 0
  [ "$PROJECT_ROOT" != "/opt/setuphelfer" ] || return 0
  [ "${SETUPHELFER_ALLOW_OLD_REPO_TAURI:-}" = "1" ] && return 0

  local repo_t opt_t rm om rs os thresh stale=0
  repo_t="$PROJECT_ROOT/frontend/src-tauri/target/release/pi-installer"
  opt_t="/opt/setuphelfer/frontend/src-tauri/target/release/pi-installer"
  [ -x "$repo_t" ] || return 0
  [ -x "$opt_t" ] || return 0

  rm=$(stat -c '%Y' "$repo_t" 2>/dev/null || stat -f '%m' "$repo_t" 2>/dev/null) || return 0
  om=$(stat -c '%Y' "$opt_t" 2>/dev/null || stat -f '%m' "$opt_t" 2>/dev/null) || return 0
  rs=$(stat -c '%s' "$repo_t" 2>/dev/null || stat -f '%z' "$repo_t" 2>/dev/null) || return 0
  os=$(stat -c '%s' "$opt_t" 2>/dev/null || stat -f '%z' "$opt_t" 2>/dev/null) || return 0

  if [ -n "$rm" ] && [ -n "$om" ] && [ "$rm" -lt "$om" ]; then
    stale=1
  fi
  thresh=$((os * 9 / 10))
  if [ -n "$rs" ] && [ -n "$os" ] && [ "$rs" -lt "$thresh" ]; then
    stale=1
  fi
  [ "$stale" -eq 1 ] || return 0

  echo ""
  echo "❌ Repo-Tauri-Release ist veraltet gegenüber /opt/setuphelfer — Start abgebrochen."
  echo "   config/version.json (Repo): $(setuphelfer_read_repo_version)"
  echo "   Repo-Binary:  mtime=$rm Größe=${rs} Bytes — $repo_t"
  echo "   /opt-Binary:  mtime=$om Größe=${os} Bytes — $opt_t"
  echo ""
  echo "   Abhilfe: cd \"$PROJECT_ROOT/frontend\" && npm run tauri:build"
  echo "   Oder System-Starter: /opt/setuphelfer/scripts/start-setuphelfer.sh"
  echo "   Absichtlich alte Binary: SETUPHELFER_ALLOW_OLD_REPO_TAURI=1 \"\$0\""
  echo ""
  exit 2
}

case "$MODE" in
  backend)
    echo "🖥️  Nur Backend (SetupHelfer-API)"
    if ! curl -sS --max-time 2 "$BACKEND_URL/api/version" >/dev/null 2>&1; then
      echo "📡 Backend antwortet nicht – versuche Start..."
      if [ -x "$PROJECT_ROOT/scripts/start-backend.sh" ]; then
        nohup "$PROJECT_ROOT/scripts/start-backend.sh" >>/tmp/setuphelfer-backend.log 2>&1 &
        _bpid=$!
        disown "$_bpid" 2>/dev/null || true
        echo -n "   Warte auf Backend "
        if ! wait_for_backend; then
          echo ""
          echo "❌ Backend nicht erreichbar (Timeout ${MAX_WAIT}s)."
          echo "   Service: sudo systemctl start setuphelfer.service"
          exit 1
        fi
        echo ""
      else
        echo -n "   "
        if ! wait_for_backend; then
          echo ""
          echo "❌ Backend nicht erreichbar."
          exit 1
        fi
        echo ""
      fi
    fi
    echo "✅ Backend läuft: $BACKEND_URL"
    if command -v zenity >/dev/null 2>&1; then
      zenity --info --title="SetupHelfer" \
        --text="Das SetupHelfer-Backend läuft.\n\n• API: ${BACKEND_URL}\n• Version: ${BACKEND_URL}/api/version" \
        --width=420 2>/dev/null || true
    fi
    exit 0
    ;;
  tauri)
    echo "🎨 Starte SetupHelfer (Tauri-App)..."
    echo "   (GDK_BACKEND=x11 für stabiles Rendering unter Wayland)"
    echo ""
    kill_port 5173
    setuphelfer_block_stale_repo_tauri_if_needed
    TAURI_BINARY="$PROJECT_ROOT/frontend/src-tauri/target/release/pi-installer"
    if [ -x "$TAURI_BINARY" ]; then
      # Installation unter /opt: gebaute Binary nutzen (kein Rust/Cargo nötig)
      # Starte im Hintergrund und prüfe ob sie läuft
      echo "Starte Tauri-Binary: $TAURI_BINARY"
      # Log-Datei vorbereiten
      touch /tmp/setuphelfer-tauri.log
      chmod 666 /tmp/setuphelfer-tauri.log 2>/dev/null || true
      env GDK_BACKEND=x11 "$TAURI_BINARY" >>/tmp/setuphelfer-tauri.log 2>&1 &
      TAURI_PID=$!
      sleep 2
      if kill -0 "$TAURI_PID" 2>/dev/null; then
        # Binary läuft, warte auf Beendigung
        wait $TAURI_PID
        exit 0
      else
        # Binary beendete sich sofort (Absturz/Fehler)
        echo "⚠️  Tauri-Binary stürzte ab oder startete nicht."
        if [ -f /tmp/setuphelfer-tauri.log ] && [ -s /tmp/setuphelfer-tauri.log ]; then
          echo "   Log (letzte 10 Zeilen):"
          tail -10 /tmp/setuphelfer-tauri.log | sed 's/^/   /'
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
        echo "⚠️  Keine Schreibrechte für Entwicklungsmodus (Verzeichnis gehört ggf. dem Service-User setuphelfer)."
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
      if [ -x "$PROJECT_ROOT/scripts/start-backend.sh" ]; then
        nohup "$PROJECT_ROOT/scripts/start-backend.sh" >>/tmp/setuphelfer-backend.log 2>&1 &
        sleep 3
      fi
    fi
    # Frontend starten (als aktueller User)
    cd "$PROJECT_ROOT/frontend" || exit 1
    [ ! -d "node_modules" ] && npm install
    echo "✅ Starte Frontend auf http://localhost:3001"
    npm run dev >/tmp/setuphelfer-frontend.log 2>&1 &
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
      echo "❌ Frontend konnte nicht gestartet werden. Log: /tmp/setuphelfer-frontend.log"
      [ -f /tmp/setuphelfer-frontend.log ] && tail -20 /tmp/setuphelfer-frontend.log | sed 's/^/   /'
      exit 1
    fi
    ;;
  browser)
    echo "🌐 Starte SetupHelfer (Browser)..."
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
  frontend)
    echo "🎨 Starte SetupHelfer (nur Vite-Server, Kompatibilität)..."
    echo ""
    exec "$PROJECT_ROOT/scripts/start-frontend.sh"
    ;;
  *)
    echo "⚠️  Unbekannte Auswahl: $MODE" >&2
    exit 1
    ;;
esac
