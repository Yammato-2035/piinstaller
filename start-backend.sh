#!/bin/bash
# PI-Installer Backend Startskript
# Startet Backend auf http://localhost:8000 (nutzt immer die Venv im backend/, nie System-Python)
# Siehe: docs/START_APPS.md

BACKEND_DIR="$(cd "$(dirname "$0")/backend" && pwd)"
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

# Backend starten – immer mit Venv-Python
echo "✅ Starte Backend auf http://localhost:8000"
echo "📝 API Docs: http://localhost:8000/docs"
echo ""
RELOAD_ARGS=""
if [ "$PI_INSTALLER_DEV" = "1" ]; then
  RELOAD_ARGS="--reload --timeout-keep-alive 1"
fi
exec "$PYTHON" -m uvicorn app:app --host 0.0.0.0 --port 8000 $RELOAD_ARGS
