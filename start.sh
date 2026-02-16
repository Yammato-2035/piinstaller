#!/bin/bash
# PI-Installer - Startet Backend und Frontend (Browser-Modus)
# Für Tauri-App: start-backend.sh + start-frontend-desktop.sh --window
# Siehe: docs/START_APPS.md

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 PI-Installer Startskript"
echo "================================"
echo ""

# Funktion zum Beenden beider Prozesse
cleanup() {
    echo ""
    echo "🛑 Beende Prozesse..."
    kill $FRONTEND_PID 2>/dev/null
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    exit
}

trap cleanup SIGINT SIGTERM

# Starte Backend im Hintergrund (oder nutze bestehendes) – immer Venv, nie System-Python (PEP 668)
echo "📡 Starte Backend..."
BACKEND_DIR="$SCRIPT_DIR/backend"
cd "$BACKEND_DIR"
if [ ! -d "venv" ] || [ ! -f "venv/bin/python3" ]; then
    python3 -m venv venv
fi
PYTHON="$BACKEND_DIR/venv/bin/python3"
PIP="$BACKEND_DIR/venv/bin/pip"
if ! "$PYTHON" -c "import fastapi" 2>/dev/null; then
    echo "📦 Installiere Backend-Dependencies (in Venv)..."
    "$PIP" install -r requirements.txt --only-binary :all: 2>/dev/null || "$PIP" install -r requirements.txt
fi
RELOAD_ARGS=""
if [ "$PI_INSTALLER_DEV" = "1" ]; then
    RELOAD_ARGS="--reload --timeout-keep-alive 1"
fi

# Remote-Zugriff: aus Einstellungen lesen (Checkbox "Remote Zugriff deaktivieren")
REMOTE_DISABLED=1
if [ -f "$SCRIPT_DIR/scripts/read_remote_access_disabled.py" ]; then
    "$PYTHON" "$SCRIPT_DIR/scripts/read_remote_access_disabled.py" 2>/dev/null && REMOTE_DISABLED=0
fi
if [ "$REMOTE_DISABLED" = "0" ]; then
    BIND_HOST="127.0.0.1"
    FRONTEND_DEV="dev:local"
    echo "🔒 Remote-Zugriff deaktiviert – nur localhost"
else
    BIND_HOST="0.0.0.0"
    FRONTEND_DEV="dev"
fi

# Port-Check ohne sudo (wichtig wenn start.sh als systemd-Service-User läuft)
_port_in_use() {
    command -v ss >/dev/null 2>&1 && ss -tlnp 2>/dev/null | grep -q ':8000 ' && return 0
    lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1 && return 0
    return 1
}
if _port_in_use; then
    if curl -sS --max-time 2 http://127.0.0.1:8000/api/version >/dev/null 2>&1; then
        echo "ℹ️  Backend läuft bereits auf :8000 – starte kein zweites."
        BACKEND_PID=""
    else
        echo "❌ Port 8000 ist belegt, aber Backend antwortet nicht."
        echo "   Prüfen: ss -tlnp | grep 8000  oder  lsof -iTCP:8000 -sTCP:LISTEN"
        exit 1
    fi
else
    "$PYTHON" -m uvicorn app:app --host "$BIND_HOST" --port 8000 $RELOAD_ARGS &
    BACKEND_PID=$!
fi

# Warte kurz
sleep 2

# Healthcheck (nur wenn wir gestartet haben)
if [ -n "$BACKEND_PID" ]; then
    if ! curl -sS --max-time 2 http://127.0.0.1:8000/api/version >/dev/null 2>&1; then
        echo "❌ Backend konnte nicht gestartet werden (kein /api/version)."
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
fi

# Starte Frontend im Hintergrund
echo "🎨 Starte Frontend..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo "📦 Installiere Frontend-Dependencies..."
    npm install
fi
npm run "$FRONTEND_DEV" &
FRONTEND_PID=$!

echo ""
echo "✅ Beide Services gestartet!"
echo "📡 Backend:   http://localhost:8000"
echo "🎨 Frontend:  http://localhost:3001 (lokal)"
if [ "$REMOTE_DISABLED" = "0" ]; then
  echo "🔒 Remote-Zugriff deaktiviert – nur von diesem Rechner erreichbar"
else
  LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
  if [ -n "$LAN_IP" ] && [ "$LAN_IP" != "0.0.0.0" ] && [ "$LAN_IP" != "127.0.0.1" ]; then
    echo "🌐 Im Netzwerk: http://${LAN_IP}:3001 (von anderen Geräten)"
  fi
fi
echo "📝 API Docs:  http://localhost:8000/docs"
echo ""
echo "Hinweis: 0.0.0.0 ist nicht erreichbar – andere Geräte nutzen die Netzwerk-IP (z. B. oben)."
echo "         Bei Zugriffsproblemen: Firewall prüfen (Einstellungen → Frontend-Netzwerk-Zugriff)."
echo ""
echo "Drücke Ctrl+C zum Beenden"
echo ""

# Warte auf beide Prozesse
wait
