#!/bin/bash
# Legt Startmenü-Einträge (/.desktop) für Setuphelfer an.
# Wird von install-system.sh und deploy-to-opt.sh aufgerufen.
#
# Verwendung (mit Root):
#   sudo /pfad/zum/repo/scripts/install-desktop-entries.sh [/opt/setuphelfer]
#   Default INSTALL_DIR: /opt/setuphelfer

set -e

INSTALL_DIR="${1:-/opt/setuphelfer}"
APPLICATIONS_DIR="/usr/share/applications"

if [ "$(id -u)" -ne 0 ]; then
  echo "Dieses Skript muss mit sudo ausgeführt werden." >&2
  exit 1
fi

START_SCRIPT="$INSTALL_DIR/scripts/start-setuphelfer.sh"
if [ ! -x "$START_SCRIPT" ] && [ -f "$INSTALL_DIR/scripts/start-pi-installer.sh" ]; then
  START_SCRIPT="$INSTALL_DIR/scripts/start-pi-installer.sh"
fi
if [ ! -f "$START_SCRIPT" ]; then
  echo "Installationsverzeichnis nicht gefunden oder Starter fehlt: $INSTALL_DIR" >&2
  exit 1
fi

mkdir -p "$APPLICATIONS_DIR"

ICON="$INSTALL_DIR/frontend/src-tauri/icons/icon.png"
[ ! -f "$ICON" ] && ICON="utilities-terminal"

DESKTOP_FILE="$APPLICATIONS_DIR/setuphelfer.desktop"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SetupHelfer
Comment=Backend prüfen, dann Auswahl: Tauri-App, Browser oder nur Backend (API)
Exec=$START_SCRIPT
Path=$INSTALL_DIR
Icon=$ICON
Terminal=true
Categories=System;Settings;Utility;
Keywords=setuphelfer;raspberry;pi;linux;
StartupWMClass=setuphelfer
EOF
chmod 644 "$DESKTOP_FILE"

DESKTOP_FILE_BROWSER="$APPLICATIONS_DIR/setuphelfer-browser.desktop"
cat > "$DESKTOP_FILE_BROWSER" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SetupHelfer (Browser)
Comment=Weboberfläche im Standard-Browser (Port 3001; Backend muss laufen)
Exec=sh -c "xdg-open http://127.0.0.1:3001 2>/dev/null || sensible-browser http://127.0.0.1:3001"
Path=$INSTALL_DIR
Icon=$ICON
Terminal=false
Categories=System;Settings;Utility;
Keywords=setuphelfer;browser;raspberry;
EOF
chmod 644 "$DESKTOP_FILE_BROWSER"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q "$APPLICATIONS_DIR" 2>/dev/null || true
fi

echo "Startmenü-Einträge angelegt:"
echo "  $DESKTOP_FILE"
echo "  $DESKTOP_FILE_BROWSER"
echo "  → SetupHelfer unter Anwendungen / Startmenü."
