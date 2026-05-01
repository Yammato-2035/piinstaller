#!/bin/bash
# Legt „SetupHelfer.desktop“ direkt auf dem Schreibtisch ab:
#   Backend prüfen/starten, dann Auswahl: Tauri-App / Browser / Nur Backend
#   Icon: Tauri-App-Icon (PNG) oder Logo-SVG
#
# Aufruf: bash scripts/desktop-setuphelfer-launcher-anlegen.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
START_SCRIPT="$PROJECT_ROOT/scripts/start-setuphelfer.sh"
ICON_PNG="$PROJECT_ROOT/frontend/src-tauri/icons/icon.png"
ICON_SVG="$PROJECT_ROOT/frontend/public/assets/branding/logo/logo-main.svg"

chmod +x "$PROJECT_ROOT/scripts/start-setuphelfer.sh" 2>/dev/null
chmod +x "$PROJECT_ROOT/scripts/start-backend.sh" 2>/dev/null
chmod +x "$PROJECT_ROOT/scripts/start-frontend-desktop.sh" 2>/dev/null

DESKTOPS=()
[ -d "$HOME/Desktop" ]      && DESKTOPS+=("$HOME/Desktop")
[ -d "$HOME/Schreibtisch" ] && DESKTOPS+=("$HOME/Schreibtisch")
if command -v xdg-user-dir >/dev/null 2>&1; then
  XDG_DESK="$(xdg-user-dir DESKTOP 2>/dev/null)"
  [ -n "$XDG_DESK" ] && [ -d "$XDG_DESK" ] && DESKTOPS+=("$XDG_DESK")
fi
[ ${#DESKTOPS[@]} -eq 0 ]   && DESKTOPS+=("$HOME")

ICON="$ICON_PNG"
[ ! -f "$ICON" ] && [ -f "$ICON_SVG" ] && ICON="$ICON_SVG"
[ ! -f "$ICON" ] && ICON="utilities-terminal"

echo "🖥️  SetupHelfer Desktop-Starter anlegen"
echo "======================================="
echo ""

for DESKTOP in "${DESKTOPS[@]}"; do
  # Einmal pro physischem Pfad (Desktop/Schreibtisch können identisch sein)
  DESKTOP_FILE="$DESKTOP/SetupHelfer.desktop"
  cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SetupHelfer
Comment=Auswahl: Tauri-App, Browser oder nur Backend (API)
Exec=$START_SCRIPT
Path=$PROJECT_ROOT
Icon=$ICON
Terminal=true
Categories=System;Settings;Utility;
Keywords=setuphelfer;raspberry;pi;linux;installer;
StartupWMClass=setuphelfer
EOF
  chmod +x "$DESKTOP_FILE"
  echo "✅ $DESKTOP_FILE"
done

echo ""
echo "Doppelklick auf „SetupHelfer“:"
echo "  • Prüft/startet Backend (Port 8000)"
echo "  • Dialog: Desktop-App (Tauri) / Browser / Nur Backend"
echo ""
