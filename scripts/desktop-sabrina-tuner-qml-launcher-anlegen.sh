#!/bin/bash
# Legt einen Desktop-Starter „Sabrina Tuner (QML)“ im Ordner Desktop/PI-Installer/ ab.
# Startet die QML-Version des Sabrina Tuners (PyQt6 + GStreamer).
#
# Aufruf: bash scripts/desktop-sabrina-tuner-qml-launcher-anlegen.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
START_SCRIPT="$PROJECT_ROOT/scripts/start-dsi-radio-qml.sh"

chmod +x "$START_SCRIPT" 2>/dev/null

# Desktop-Ordner (englisch und/oder deutsch)
DESKTOPS=()
[ -d "$HOME/Desktop" ]      && DESKTOPS+=("$HOME/Desktop")
[ -d "$HOME/Schreibtisch" ] && DESKTOPS+=("$HOME/Schreibtisch")
[ ${#DESKTOPS[@]} -eq 0 ]   && DESKTOPS+=("$HOME")

echo "🖥️  Sabrina Tuner (QML) – Desktop-Starter anlegen"
echo "================================================="
echo ""

ICON_PATH="$PROJECT_ROOT/apps/dsi_radio/qml/sabrina-tuner-icon.png"
for DESKTOP in "${DESKTOPS[@]}"; do
  LAUNCHER_DIR="$DESKTOP/PI-Installer"
  mkdir -p "$LAUNCHER_DIR"
  DESKTOP_FILE="$LAUNCHER_DIR/Sabrina-Tuner-QML.desktop"
  if [ -f "$ICON_PATH" ]; then
    ICON_LINE="Icon=$ICON_PATH"
  else
    ICON_LINE="Icon=applications-multimedia"
  fi
  cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Sabrina Tuner (QML)
Comment=Internetradio – QML-Prototyp (Sabrina Tuner)
Exec=$START_SCRIPT
Path=$PROJECT_ROOT
$ICON_LINE
Terminal=false
Categories=Audio;Music;
Keywords=radio;internet;sabrina;qml;dsi;
EOF
  chmod +x "$DESKTOP_FILE"
  echo "✅ Desktop-Starter: $DESKTOP_FILE"
done

echo ""
echo "Doppelklick auf „Sabrina Tuner (QML)“ startet die QML-Radio-App."
echo ""
