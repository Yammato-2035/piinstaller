#!/bin/bash
# Legt ein Desktop-Starticon für den PI-Installer Bilderrahmen an
# (Desktop + Anwendungsmenü).
#
# Verwendung: ./scripts/desktop-picture-frame-launcher-anlegen.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DESKTOP_DIR="${HOME}/Desktop"
APP_DIR="${HOME}/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/pi-installer-picture-frame.desktop"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$APP_DIR"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Bilderrahmen (PI-Installer)
Comment=Bilder-Slideshow mit Datum und Themen (Weihnachten, Valentinstag, …)
Exec=$REPO_ROOT/scripts/start-picture-frame.sh
Icon=folder-pictures
Path=$REPO_ROOT
Terminal=false
Categories=Graphics;Viewer;
EOF

chmod +x "$DESKTOP_FILE"
cp "$DESKTOP_FILE" "$APP_DIR/pi-installer-picture-frame.desktop"
echo "Desktop-Icon: $DESKTOP_FILE"
echo "Anwendungsmenü: $APP_DIR/pi-installer-picture-frame.desktop"
