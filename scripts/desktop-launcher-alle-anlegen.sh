#!/bin/bash
# Legt alle PI-Installer-Desktop-Starter im Ordner „PI-Installer“ auf dem Desktop ab:
#   • PI-Installer (Kombi: Frontend-Auswahl, Backend läuft als Service)
#   • Frontend starten (nur Vite-Server)
#   • Frontend (App-Fenster) – eigene Oberfläche (Tauri)
#   • Frontend (Browser) – im Standard-Browser öffnen
#   • DSI Radio
#   • Bilderrahmen
#
# Aufruf: bash scripts/desktop-launcher-alle-anlegen.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🖥️  PI-Installer – alle Desktop-Starter anlegen"
echo "==============================================="
echo "   Ordner: Desktop/PI-Installer/"
echo ""

# Frontend-Starter (alle drei: Server, App-Fenster, Browser)
bash "$SCRIPT_DIR/desktop-frontend-launcher-anlegen.sh"
echo ""

# PI-Installer (Kombi: Auswahl Tauri/Browser/Frontend; Backend als Service)
bash "$SCRIPT_DIR/desktop-pi-installer-launcher-anlegen.sh"
echo ""

# DSI Radio
bash "$SCRIPT_DIR/desktop-dsi-radio-launcher-anlegen.sh"
echo ""

# Bilderrahmen
bash "$SCRIPT_DIR/desktop-bilderrahmen-launcher-anlegen.sh"

echo ""
echo "==============================================="
echo "✅ Fertig. Im Ordner Desktop/PI-Installer/ liegen:"
echo "   • PI-Installer                        (Auswahl Tauri/Browser/Vite; Backend als Service)"
echo "   • PI-Installer Frontend starten       (nur Vite-Server)"
echo "   • PI-Installer Frontend (App-Fenster)  (eigene Oberfläche)"
echo "   • PI-Installer Frontend (Browser)      (im Browser öffnen)"
echo "   • DSI Radio                           (eigenständige PyQt-App, DSI/TFT)"
echo "   • Bilderrahmen                        (Fotos im Loop, TFT-Seite)"
