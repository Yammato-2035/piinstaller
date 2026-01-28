#!/bin/bash
# PI-Installer Backend Startskript

cd "$(dirname "$0")/backend"

echo "🚀 Starte PI-Installer Backend..."
echo "📁 Arbeitsverzeichnis: $(pwd)"

# Prüfe ob venv existiert
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual Environment nicht gefunden!"
    echo "📦 Erstelle venv..."
    python3 -m venv venv
fi

# Aktiviere venv
echo "🔧 Aktiviere Virtual Environment..."
source venv/bin/activate

# Prüfe ob Dependencies installiert sind
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installiere Dependencies..."
    pip install -r requirements.txt --only-binary :all: 2>/dev/null || pip install -r requirements.txt
fi

# Starte Backend
echo "✅ Starte Backend auf http://localhost:8000"
echo "📝 API Docs: http://localhost:8000/docs"
echo ""
# Standard: stabil ohne reload. Dev-Rewrite nur wenn PI_INSTALLER_DEV=1
RELOAD_ARGS=""
if [ "$PI_INSTALLER_DEV" = "1" ]; then
  RELOAD_ARGS="--reload --timeout-keep-alive 1"
fi
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 $RELOAD_ARGS
