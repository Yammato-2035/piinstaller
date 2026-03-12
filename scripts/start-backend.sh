#!/bin/bash
# PI-Installer Backend Startskript
# Startet Backend auf http://localhost:8000 (nutzt immer die Venv im backend/, nie System-Python)
# Siehe: docs/START_APPS.md

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
cd "$BACKEND_DIR"

echo "🚀 Starte PI-Installer Backend..."
echo "📁 Arbeitsverzeichnis: $BACKEND_DIR"

# Venv anlegen, falls nicht vorhanden
if [ ! -d "venv" ] || [ ! -f "venv/bin/python3" ]; then
    echo "📦 Erstelle Virtual Environment..."
    python3 -m venv venv
fi

PYTHON="$BACKEND_DIR/venv/bin/python3"
PIP="$BACKEND_DIR/venv/bin/pip"

# Dependencies in der Venv installieren (niemals system-weit – PEP 668)
if ! "$PYTHON" -c "import fastapi" 2>/dev/null; then
    echo "📦 Installiere Dependencies (in Venv)..."
    "$PIP" install -r requirements.txt --only-binary :all: 2>/dev/null || "$PIP" install -r requirements.txt
fi

# Port: Standard 8000, überschreibbar mit PI_INSTALLER_BACKEND_PORT (z. B. wenn 8000 belegt)
PORT="${PI_INSTALLER_BACKEND_PORT:-8000}"

# Prüfen ob Port belegt ist
if command -v ss >/dev/null 2>&1; then
  if ss -tuln 2>/dev/null | grep -q ":$PORT "; then
    echo "⚠️  Port $PORT ist bereits belegt."
    if command -v lsof >/dev/null 2>&1; then
      echo "   Prozess(e) auf Port $PORT:"
      lsof -i ":$PORT" 2>/dev/null | sed 's/^/   /'
    else
      echo "   Anzeigen mit: ss -tulnp | grep $PORT  oder  sudo lsof -i :$PORT"
    fi
    echo ""
    echo "   Optionen:"
    echo "   - Vorhandenen Backend-Prozess beenden (z. B. kill \$(lsof -t -i:$PORT))"
    echo "   - Oder anderen Port nutzen: PI_INSTALLER_BACKEND_PORT=8001 ./start-backend.sh"
    echo "   - In der App dann unter Einstellungen → Backend-API-URL: http://127.0.0.1:8001 eintragen."
    echo ""
    exit 1
  fi
fi

# Backend starten – immer mit Venv-Python, genau ein Worker (wichtig für Sudo-Passwort-Speicherung)
echo "✅ Starte Backend auf http://localhost:$PORT"
echo "📝 API Docs: http://localhost:$PORT/docs"
echo ""
RELOAD_ARGS=""
if [ "$PI_INSTALLER_DEV" = "1" ]; then
  RELOAD_ARGS="--reload --timeout-keep-alive 1"
fi
exec "$PYTHON" -m uvicorn app:app --host 0.0.0.0 --port "$PORT" --workers 1 $RELOAD_ARGS
