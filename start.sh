#!/bin/bash
# PI-Installer - Startet Backend und Frontend

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

# Starte Backend im Hintergrund (oder nutze bestehendes)
echo "📡 Starte Backend..."
cd "$SCRIPT_DIR/backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installiere Backend-Dependencies..."
    pip install -r requirements.txt --only-binary :all: 2>/dev/null || pip install -r requirements.txt
fi
# Optional: Dev reload nur wenn PI_INSTALLER_DEV=1
RELOAD_ARGS=""
if [ "$PI_INSTALLER_DEV" = "1" ]; then
    RELOAD_ARGS="--reload --timeout-keep-alive 1"
fi

# Remote-Zugriff: aus Einstellungen lesen (Checkbox "Remote Zugriff deaktivieren")
REMOTE_DISABLED=1
if [ -f "$SCRIPT_DIR/scripts/read_remote_access_disabled.py" ]; then
    python3 "$SCRIPT_DIR/scripts/read_remote_access_disabled.py" 2>/dev/null && REMOTE_DISABLED=0
fi
if [ "$REMOTE_DISABLED" = "0" ]; then
    BIND_HOST="127.0.0.1"
    FRONTEND_DEV="dev:local"
    echo "🔒 Remote-Zugriff deaktiviert – nur localhost"
else
    BIND_HOST="0.0.0.0"
    FRONTEND_DEV="dev"
fi

# Wenn Port 8000 schon belegt ist, prüfe ob Backend antwortet; sonst abbrechen.
if sudo lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
    if curl -sS --max-time 2 http://127.0.0.1:8000/api/version >/dev/null 2>&1; then
        echo "ℹ️  Backend läuft bereits auf :8000 – starte kein zweites."
        BACKEND_PID=""
    else
        echo "❌ Port 8000 ist belegt, aber Backend antwortet nicht."
        echo "   Bitte alten Prozess beenden: sudo lsof -nP -iTCP:8000 -sTCP:LISTEN"
        exit 1
    fi
else
    python3 -m uvicorn app:app --host "$BIND_HOST" --port 8000 $RELOAD_ARGS &
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
