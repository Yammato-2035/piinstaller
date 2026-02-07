#!/bin/bash
# PI-Installer Frontend Startskript
# Nur Vite-Server (Port 3001). Für Tauri/Browser: start-frontend-desktop.sh
# Siehe: docs/START_APPS.md

cd "$(dirname "$0")/frontend"

echo "🚀 Starte PI-Installer Frontend..."
echo "📁 Arbeitsverzeichnis: $(pwd)"

# Prüfe ob node_modules existiert
if [ ! -d "node_modules" ]; then
    echo "📦 Installiere Dependencies..."
    npm install
fi

# Starte Frontend
echo "✅ Starte Frontend auf http://localhost:3001"
echo ""
npm run dev
