#!/bin/bash
# Legt Desktop-Starter ab, u. a.:
#   • SetupHelfer.desktop auf dem Schreibtisch (Tauri / Browser / Nur Backend, Logo-Icon)
#   • Weitere Einträge im Ordner „PI-Installer“ auf dem Desktop:
#   • PI-Installer (Kombi: Frontend-Auswahl, Backend läuft als Service) — nur falls desktop-frontend eigene Starter anlegt
#   • Frontend starten (nur Vite-Server)
#   • Frontend (App-Fenster) – eigene Oberfläche (Tauri)
#   • Frontend (Browser) – im Standard-Browser öffnen
#   • DSI Radio
#   • Sabrina Tuner (QML)
#   • Bilderrahmen
#
# Aufruf: bash scripts/desktop-launcher-alle-anlegen.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🖥️  SetupHelfer / PI-Installer – Desktop-Starter anlegen"
echo "========================================================"
echo "   SetupHelfer.desktop → Schreibtisch (Hauptstarter)"
echo "   Weitere Starter → Desktop/PI-Installer/ (falls vorhanden)"
echo ""

# Frontend-Starter (alle drei: Server, App-Fenster, Browser)
bash "$SCRIPT_DIR/desktop-frontend-launcher-anlegen.sh"
echo ""

# SetupHelfer (Kombi: Tauri/Browser/Nur Backend)
bash "$SCRIPT_DIR/desktop-pi-installer-launcher-anlegen.sh"
echo ""

# DSI Radio
bash "$SCRIPT_DIR/desktop-dsi-radio-launcher-anlegen.sh"
echo ""

# Sabrina Tuner (QML)
bash "$SCRIPT_DIR/desktop-sabrina-tuner-qml-launcher-anlegen.sh"
echo ""

# Bilderrahmen
bash "$SCRIPT_DIR/desktop-bilderrahmen-launcher-anlegen.sh"

echo ""
echo "==============================================="
echo "✅ Fertig."
echo "   • Auf dem Schreibtisch: SetupHelfer.desktop (Logo, Auswahl Tauri / Browser / Nur Backend)"
echo "   • Ordner Desktop/PI-Installer/: weitere Frontend-Starter (Vite, Tauri, Browser)"
echo "   • PI-Installer Frontend starten       (nur Vite-Server)"
echo "   • PI-Installer Frontend (App-Fenster)  (eigene Oberfläche)"
echo "   • PI-Installer Frontend (Browser)      (im Browser öffnen)"
echo "   • DSI Radio                           (eigenständige PyQt-App, DSI/TFT)"
echo "   • Sabrina Tuner (QML)                 (QML-Prototyp, Internetradio)"
echo "   • Bilderrahmen                        (Fotos im Loop, TFT-Seite)"
