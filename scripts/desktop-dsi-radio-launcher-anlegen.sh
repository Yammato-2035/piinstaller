#!/bin/bash
# Legt einen Desktop-Starter „DSI Radio“ im Ordner Desktop/PI-Installer/ ab.
# Startet die eigenständige PyQt6-Radio-App (kein Browser, kein Frontend nötig).
#
# Aufruf: bash scripts/desktop-dsi-radio-launcher-anlegen.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
START_SCRIPT="$PROJECT_ROOT/scripts/start-dsi-radio.sh"

chmod +x "$PROJECT_ROOT/scripts/start-dsi-radio.sh" 2>/dev/null
chmod +x "$PROJECT_ROOT/scripts/start-dsi-radio-native.sh" 2>/dev/null

# Desktop-Ordner (englisch und/oder deutsch)
DESKTOPS=()
[ -d "$HOME/Desktop" ]      && DESKTOPS+=("$HOME/Desktop")
[ -d "$HOME/Schreibtisch" ] && DESKTOPS+=("$HOME/Schreibtisch")
[ ${#DESKTOPS[@]} -eq 0 ]   && DESKTOPS+=("$HOME")

echo "🖥️  DSI Radio – Desktop-Starter anlegen"
echo "======================================="
echo ""

for DESKTOP in "${DESKTOPS[@]}"; do
  LAUNCHER_DIR="$DESKTOP/PI-Installer"
  mkdir -p "$LAUNCHER_DIR"
  DESKTOP_FILE="$LAUNCHER_DIR/DSI-Radio.desktop"
  cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=DSI Radio
Comment=Eigenständige PyQt6-Radio-App – Internetradio (Freenove-TFT/DSI)
Exec=$START_SCRIPT
Path=$PROJECT_ROOT
Icon=applications-multimedia
Terminal=false
Categories=Audio;Music;
Keywords=radio;internet;dsi;freenove;
EOF
  chmod +x "$DESKTOP_FILE"
  echo "✅ Desktop-Starter: $DESKTOP_FILE"
done

echo ""
echo "Doppelklick auf „DSI Radio“ startet die PyQt-Radio-App (eigene App, kein Browser)."
echo ""
