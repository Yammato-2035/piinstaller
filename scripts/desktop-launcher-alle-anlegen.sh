#!/bin/bash
# Legt alle PI-Installer-Desktop-Starter auf dem Desktop ab:
#   • Backend starten
#   • Frontend starten (nur Vite-Server)
#   • Frontend (App-Fenster) – eigene Oberfläche (Tauri)
#   • Frontend (Browser) – im Standard-Browser öffnen
#
# Aufruf: bash scripts/desktop-launcher-alle-anlegen.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🖥️  PI-Installer – alle Desktop-Starter anlegen"
echo "==============================================="
echo ""

# Backend-Starter
bash "$SCRIPT_DIR/desktop-backend-launcher-anlegen.sh"
echo ""

# Frontend-Starter (alle drei: Server, App-Fenster, Browser)
bash "$SCRIPT_DIR/desktop-frontend-launcher-anlegen.sh"

# PI-Installer (Kombi: Backend + Auswahl Tauri/Browser/Frontend)
bash "$SCRIPT_DIR/desktop-pi-installer-launcher-anlegen.sh"

echo ""
echo "==============================================="
echo "✅ Fertig. Auf dem Desktop liegen jetzt:"
echo "   • PI-Installer                        (Backend + Auswahl Tauri/Browser/Vite)"
echo "   • PI-Installer Backend starten"
echo "   • PI-Installer Frontend starten       (nur Vite-Server)"
echo "   • PI-Installer Frontend (App-Fenster) (eigene Oberfläche)"
echo "   • PI-Installer Frontend (Browser)     (im Browser öffnen)"
