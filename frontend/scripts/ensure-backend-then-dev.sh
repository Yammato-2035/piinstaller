#!/bin/bash
# Startet Backend (falls nötig), wartet auf Ready, dann Vite für Tauri-Dev.
# Wird von beforeDevCommand (tauri.conf.json) aufgerufen.
# CWD: frontend/ (Tauri startet das Skript dort)

# Von src-tauri/ oder frontend/ aufrufbar; Pfade relativ zu Skript
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="$(cd "$FRONTEND_DIR/.." && pwd)"
BACKEND_URL="http://127.0.0.1:8000"
MAX_WAIT=30
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

if curl -sS --max-time 2 "$BACKEND_URL/api/version" >/dev/null 2>&1; then
  : # Backend läuft
else
  echo "[Tauri-Dev] Backend nicht erreichbar – starte Backend..."
  if [ -x "$PROJECT_ROOT/scripts/start-backend.sh" ]; then
    nohup "$PROJECT_ROOT/scripts/start-backend.sh" >>/tmp/pi-installer-backend.log 2>&1 &
    disown 2>/dev/null || true
    echo -n "[Tauri-Dev] Warte auf Backend "
    if ! wait_for_backend; then
      echo ""
      echo "[Tauri-Dev] Backend konnte nicht gestartet werden. Starte manuell: $PROJECT_ROOT/scripts/start-backend.sh"
      echo "[Tauri-Dev] Vite startet trotzdem (API-Calls schlagen fehl)."
    else
      echo ""
      echo "[Tauri-Dev] Backend bereit."
    fi
  else
    echo "[Tauri-Dev] scripts/start-backend.sh nicht gefunden. Backend manuell starten."
  fi
fi

# Vite nutzt --strictPort 5173; ein alter Vite/Tauri-Dev blockiert sonst den Start.
free_vite_port_5173() {
  local pids=""
  if command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -t -iTCP:5173 -sTCP:LISTEN 2>/dev/null || true)
  fi
  if [ -z "$pids" ] && command -v fuser >/dev/null 2>&1; then
    if fuser 5173/tcp >/dev/null 2>&1; then
      echo "[Tauri-Dev] Port 5173 belegt – beende Listener (meist alter Vite-Dev-Server)..."
      fuser -k 5173/tcp >/dev/null 2>&1 || true
      sleep 1
      return 0
    fi
    return 0
  fi
  if [ -n "$pids" ]; then
    echo "[Tauri-Dev] Port 5173 belegt – beende Listener (PID: $pids)..."
    for pid in $pids; do
      kill "$pid" 2>/dev/null || true
    done
    sleep 1
  fi
}
free_vite_port_5173

cd "$FRONTEND_DIR" && exec npm run dev:tauri
