#!/bin/bash
# Legt einen Desktop-Starter „PI-Installer“ auf dem Desktop ab:
#   Startet zuerst Backend, wartet auf Ready, dann Auswahl (Tauri / Browser / Nur Frontend)
#   Mit PI-Installer-Icon
#
# Aufruf: bash scripts/desktop-pi-installer-launcher-anlegen.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
START_SCRIPT="$PROJECT_ROOT/start-pi-installer.sh"
ICON_PATH="$PROJECT_ROOT/frontend/src-tauri/icons/icon.png"

chmod +x "$START_SCRIPT" 2>/dev/null
chmod +x "$PROJECT_ROOT/start-backend.sh" 2>/dev/null
chmod +x "$PROJECT_ROOT/start-frontend-desktop.sh" 2>/dev/null

# Desktop-Ordner (englisch und/oder deutsch)
DESKTOPS=()
[ -d "$HOME/Desktop" ]      && DESKTOPS+=("$HOME/Desktop")
[ -d "$HOME/Schreibtisch" ] && DESKTOPS+=("$HOME/Schreibtisch")
[ ${#DESKTOPS[@]} -eq 0 ]   && DESKTOPS+=("$HOME")

# Icon: absoluter Pfad, fallback auf system-icon
ICON="$ICON_PATH"
[ ! -f "$ICON" ] && ICON="utilities-terminal"

echo "🖥️  PI-Installer Desktop-Starter anlegen"
echo "========================================"
echo ""

for DESKTOP in "${DESKTOPS[@]}"; do
  DESKTOP_FILE="$DESKTOP/PI-Installer.desktop"
  cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PI-Installer
Comment=Startet Backend, dann Auswahl: Tauri / Browser / Vite-Server
Exec="$START_SCRIPT"
Path=$PROJECT_ROOT
Icon=$ICON
Terminal=true
Categories=Development;System;Utility;
Keywords=raspberry;pi;installer;admin;
EOF
  chmod +x "$DESKTOP_FILE"
  echo "✅ Desktop-Starter: $DESKTOP_FILE"
done

echo ""
echo "Doppelklick auf „PI-Installer“ startet:"
echo "  1. Backend (falls nicht läuft)"
echo "  2. Wartet auf Backend-Ready"
echo "  3. Dialog zur Auswahl: App-Fenster (Tauri) / Browser / Nur Vite-Server"
echo ""
