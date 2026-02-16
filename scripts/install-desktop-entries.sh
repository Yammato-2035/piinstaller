#!/bin/bash
# Legt Startmenü-Einträge (/.desktop) für den PI-Installer an, damit die App
# nach der Installation unter „Anwendungen“ / Startmenü erscheint.
# Wird von install-system.sh und deploy-to-opt.sh aufgerufen.
#
# Verwendung (mit Root):
#   Aus dem Repo:  sudo /pfad/zum/piinstaller/scripts/install-desktop-entries.sh /opt/pi-installer
#   Oder aus /opt: sudo /opt/pi-installer/scripts/install-desktop-entries.sh [INSTALL_DIR]
#   Default INSTALL_DIR: /opt/pi-installer

set -e

INSTALL_DIR="${1:-/opt/pi-installer}"
APPLICATIONS_DIR="/usr/share/applications"

if [ "$(id -u)" -ne 0 ]; then
  echo "Dieses Skript muss mit sudo ausgeführt werden." >&2
  exit 1
fi

if [ ! -f "$INSTALL_DIR/start-pi-installer.sh" ]; then
  echo "Installationsverzeichnis nicht gefunden oder unvollständig: $INSTALL_DIR" >&2
  exit 1
fi

mkdir -p "$APPLICATIONS_DIR"

# Icon: aus Installationsverzeichnis oder Fallback
ICON="$INSTALL_DIR/frontend/src-tauri/icons/icon.png"
[ ! -f "$ICON" ] && ICON="utilities-terminal"

# PI-Installer (Hauptstarter: Backend prüfen, dann Auswahl Tauri/Browser/Vite)
DESKTOP_FILE="$APPLICATIONS_DIR/pi-installer.desktop"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PI-Installer
Comment=Konfigurations-Assistent für Raspberry Pi – Backend als Service, dann Auswahl (Tauri/Browser/Frontend)
Exec=$INSTALL_DIR/start-pi-installer.sh
Path=$INSTALL_DIR
Icon=$ICON
Terminal=true
Categories=Development;System;Utility;
Keywords=raspberry;pi;installer;admin;
EOF
chmod 644 "$DESKTOP_FILE"

# Optional: Direkt „Frontend im Browser öffnen“ für Nutzer, die nur die Oberfläche wollen
DESKTOP_FILE_BROWSER="$APPLICATIONS_DIR/pi-installer-browser.desktop"
cat > "$DESKTOP_FILE_BROWSER" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PI-Installer (im Browser)
Comment=PI-Installer im Standard-Browser öffnen (Backend muss laufen)
Exec=sh -c "xdg-open http://127.0.0.1:3001 2>/dev/null || sensible-browser http://127.0.0.1:3001"
Path=$INSTALL_DIR
Icon=$ICON
Terminal=false
Categories=Development;System;Utility;
Keywords=raspberry;pi;installer;
EOF
chmod 644 "$DESKTOP_FILE_BROWSER"

# Desktop-Datenbank aktualisieren (KDE/LXDE etc.)
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q "$APPLICATIONS_DIR" 2>/dev/null || true
fi

echo "Startmenü-Einträge angelegt:"
echo "  $APPLICATIONS_DIR/pi-installer.desktop"
echo "  $APPLICATIONS_DIR/pi-installer-browser.desktop"
echo "  → PI-Installer erscheint unter Anwendungen / Startmenü."
