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
  if [ -x "$PROJECT_ROOT/start-backend.sh" ]; then
    nohup "$PROJECT_ROOT/start-backend.sh" >>/tmp/pi-installer-backend.log 2>&1 &
    disown 2>/dev/null || true
    echo -n "[Tauri-Dev] Warte auf Backend "
    if ! wait_for_backend; then
      echo ""
      echo "[Tauri-Dev] Backend konnte nicht gestartet werden. Starte manuell: $PROJECT_ROOT/start-backend.sh"
      echo "[Tauri-Dev] Vite startet trotzdem (API-Calls schlagen fehl)."
    else
      echo ""
      echo "[Tauri-Dev] Backend bereit."
    fi
  else
    echo "[Tauri-Dev] start-backend.sh nicht gefunden. Backend manuell starten."
  fi
fi

cd "$FRONTEND_DIR" && exec npm run dev:tauri
