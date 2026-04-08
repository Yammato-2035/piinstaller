#!/bin/bash
# Setuphelfer – Zentrale Startfunktion: Backend und alle Frontend-Varianten
# Ein Einstieg für alle Startmöglichkeiten aus dem Repo.
# Siehe: docs/START_APPS.md

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_URL="http://127.0.0.1:8000"
BACKEND_LOG="/tmp/setuphelfer-backend.log"

wait_for_backend() {
  local max="${1:-60}"
  local waited=0
  while [ "$waited" -lt "$max" ]; do
    if curl -sS --max-time 2 "$BACKEND_URL/api/version" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
    waited=$((waited + 2))
    printf "."
  done
  return 1
}

ensure_backend_then() {
  if curl -sS --max-time 2 "$BACKEND_URL/api/version" >/dev/null 2>&1; then
    echo "✅ Backend läuft bereits auf :8000"
    "$@"
    return $?
  fi
  echo "📡 Backend nicht erreichbar – starte Backend..."
  nohup "$REPO_ROOT/scripts/start-backend.sh" >>"$BACKEND_LOG" 2>&1 &
  echo -n "   Warte auf Backend "
  if ! wait_for_backend; then
    echo ""
    echo "❌ Backend antwortet nicht (Timeout). Log: $BACKEND_LOG"
    return 1
  fi
  echo ""
  echo "✅ Backend bereit"
  "$@"
  return $?
}

show_menu() {
  echo ""
  echo "🚀 Setuphelfer – Alle Startoptionen"
  echo "===================================="
  echo ""
  echo "  Backend:"
  echo "    1) Nur Backend starten (Port 8000, Vordergrund)"
  echo "    2) Nur Backend starten (Hintergrund)"
  echo ""
  echo "  Backend + Frontend gemeinsam:"
  echo "    3) Backend + Frontend im Browser (beide im Terminal, Strg+C beendet)"
  echo "    4) Backend + Frontend (Tauri-App-Fenster)"
  echo "    5) Backend + Frontend (nur Vite-Server, Port 3001)"
  echo ""
  echo "  Setuphelfer (Backend prüfen, dann Auswahl Tauri/Browser/Vite):"
  echo "    6) Setuphelfer starten (Dialog oder Auswahl)"
  echo ""
  echo "  Nur Frontend (Backend muss laufen oder wird gestartet):"
  echo "    7) Nur Frontend – Browser (Vite + Browser öffnen)"
  echo "    8) Nur Frontend – Tauri-App-Fenster"
  echo "    9) Nur Frontend – nur Vite-Server (Port 3001)"
  echo ""
  echo "  0) Beenden"
  echo ""
  echo -n "Wahl [6]: "
  read -r choice
  echo ""
  case "${choice:-6}" in
    1) run_backend_foreground ;;
    2) run_backend_background ;;
    3) run_both_browser ;;
    4) run_both_tauri ;;
    5) run_both_vite ;;
    6) run_setuphelfer ;;
    7) run_frontend_browser ;;
    8) run_frontend_tauri ;;
    9) run_frontend_vite ;;
    0) exit 0 ;;
    *) echo "Ungültige Wahl." ; show_menu ;;
  esac
}

run_backend_foreground() {
  echo "📡 Starte Backend (Vordergrund, Strg+C beendet)..."
  exec "$REPO_ROOT/scripts/start-backend.sh"
}

run_backend_background() {
  echo "📡 Starte Backend im Hintergrund..."
  nohup "$REPO_ROOT/scripts/start-backend.sh" >>"$BACKEND_LOG" 2>&1 &
  echo "   Log: $BACKEND_LOG"
  echo -n "   Warte auf Backend "
  if wait_for_backend; then
    echo ""
    echo "✅ Backend läuft auf http://localhost:8000"
    echo "   Beenden: kill \$(lsof -t -i:8000)"
  else
    echo ""
    echo "❌ Timeout – prüfe $BACKEND_LOG"
  fi
}

run_both_browser() {
  echo "📡🎨 Backend + Frontend (Browser)..."
  exec "$REPO_ROOT/start.sh"
}

run_both_tauri() {
  ensure_backend_then run_frontend_tauri
}

run_both_vite() {
  ensure_backend_then run_frontend_vite
}

run_setuphelfer() {
  exec "$REPO_ROOT/scripts/start-pi-installer.sh"
}

run_frontend_browser() {
  ensure_backend_then "$REPO_ROOT/scripts/start-frontend-desktop.sh" --browser
}

run_frontend_tauri() {
  "$REPO_ROOT/scripts/start-frontend-desktop.sh" --window
}

run_frontend_vite() {
  ensure_backend_then exec "$REPO_ROOT/scripts/start-frontend.sh"
}

# --- Hauptprogramm ---
cd "$REPO_ROOT" || exit 1

MODE="${1:-}"

case "$MODE" in
  backend)
    run_backend_foreground
    ;;
  backend-bg)
    run_backend_background
    ;;
  both-browser)
    run_both_browser
    ;;
  both-tauri)
    run_both_tauri
    ;;
  both-vite)
    run_both_vite
    ;;
  menu|setuphelfer|pi-installer)
    if [ "$MODE" = "menu" ]; then
      show_menu
    else
      run_setuphelfer
    fi
    ;;
  frontend-browser)
    run_frontend_browser
    ;;
  frontend-tauri)
    run_frontend_tauri
    ;;
  frontend-vite)
    run_frontend_vite
    ;;
  help|--help|-h)
    echo "Setuphelfer – Zentrale Startfunktion"
    echo ""
    echo "Aufruf: $0 [ Option ]"
    echo ""
    echo "Optionen (ohne Dialog):"
    echo "  backend          Nur Backend (Vordergrund)"
    echo "  backend-bg       Nur Backend (Hintergrund)"
    echo "  both-browser     Backend + Frontend im Browser (wie start.sh)"
    echo "  both-tauri       Backend starten/prüfen + Tauri-App"
    echo "  both-vite        Backend starten/prüfen + nur Vite (Port 3001)"
    echo "  menu             Menü im Terminal (alle Optionen)"
    echo "  setuphelfer      Dialog Tauri/Browser/Vite (Alias: pi-installer)"
    echo "  frontend-browser Nur Frontend – Browser (Backend ggf. automatisch)"
    echo "  frontend-tauri   Nur Frontend – Tauri-App"
    echo "  frontend-vite    Nur Frontend – nur Vite-Server"
    echo ""
    echo "Ohne Option: Menü wird angezeigt."
    echo ""
    echo "Beispiele:"
    echo "  $0                  # Menü"
    echo "  $0 backend          # Nur Backend"
    echo "  $0 both-browser     # Backend + Browser-Frontend"
    echo "  $0 frontend-tauri   # Nur Tauri (Backend muss laufen)"
    exit 0
    ;;
  "")
    show_menu
    ;;
  *)
    echo "Unbekannte Option: $MODE"
    echo "  $0 help   für alle Optionen"
    exit 1
    ;;
esac
