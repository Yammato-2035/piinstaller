#!/bin/bash
# Legt einen Desktop-Starter „Bilderrahmen“ auf dem Desktop ab.
# Öffnet die PI-Installer TFT-Seite (Bilderrahmen / Fotos im Loop).
#
# Aufruf: bash scripts/desktop-bilderrahmen-launcher-anlegen.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
START_SCRIPT="$PROJECT_ROOT/scripts/start-picture-frame.sh"

chmod +x "$START_SCRIPT" 2>/dev/null

# Desktop-Ordner (englisch und/oder deutsch)
DESKTOPS=()
[ -d "$HOME/Desktop" ]      && DESKTOPS+=("$HOME/Desktop")
[ -d "$HOME/Schreibtisch" ] && DESKTOPS+=("$HOME/Schreibtisch")
[ ${#DESKTOPS[@]} -eq 0 ]   && DESKTOPS+=("$HOME")

echo "🖥️  Bilderrahmen – Desktop-Starter anlegen"
echo "=========================================="
echo ""

for DESKTOP in "${DESKTOPS[@]}"; do
  LAUNCHER_DIR="$DESKTOP/PI-Installer"
  mkdir -p "$LAUNCHER_DIR"
  DESKTOP_FILE="$LAUNCHER_DIR/Bilderrahmen.desktop"
  cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Bilderrahmen
Comment=Fotos im Loop auf dem TFT/DSI-Display (PI-Installer)
Exec=$START_SCRIPT
Path=$PROJECT_ROOT
Icon=image-x-generic
Terminal=false
Categories=Graphics;Viewer;
Keywords=bilderrahmen;fotos;slideshow;tft;dsi;
EOF
  chmod +x "$DESKTOP_FILE"
  echo "✅ Desktop-Starter: $DESKTOP_FILE"
done

echo ""
echo "Doppelklick auf „Bilderrahmen“ öffnet die TFT-Seite im PI-Installer."
echo ""
