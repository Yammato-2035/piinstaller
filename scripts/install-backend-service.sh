#!/bin/bash
# PI-Installer – Backend nur als systemd-Service einrichten (Start bei Boot, Port 8000).
# Aufruf: ./scripts/install-backend-service.sh
#   oder: PI_INSTALLER_DIR=/opt/pi-installer ./scripts/install-backend-service.sh
#
# Danach läuft das Backend automatisch beim Boot (pi-installer-backend.service).
# Status: sudo systemctl status pi-installer-backend
# Neustart nach Backend-Update: ./scripts/restart-backend-service.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$REPO_ROOT/start-backend.sh" ] && [ -d "$REPO_ROOT/backend" ]; then
  INSTALL_DIR="${PI_INSTALLER_DIR:-$REPO_ROOT}"
else
  INSTALL_DIR="${PI_INSTALLER_DIR:-}"
  if [ -z "$INSTALL_DIR" ] || [ ! -f "$INSTALL_DIR/start-backend.sh" ]; then
    echo "Fehler: Bitte Skript aus dem PI-Installer-Projektordner aufrufen oder PI_INSTALLER_DIR setzen." >&2
    exit 1
  fi
fi

CURRENT_USER="${SUDO_USER:-$USER}"
[ -z "$CURRENT_USER" ] && CURRENT_USER="$(whoami)"

BACKEND_SERVICE_FILE="$INSTALL_DIR/pi-installer-backend.service"
SYSTEMD_DIR="/etc/systemd/system"

if [ ! -f "$BACKEND_SERVICE_FILE" ]; then
  echo "Fehler: Service-Vorlage nicht gefunden: $BACKEND_SERVICE_FILE" >&2
  exit 1
fi

echo "Backend-Service einrichten (Start bei Boot, Port 8000)..."
echo "  Installationsverzeichnis: $INSTALL_DIR"
echo "  Benutzer: $CURRENT_USER"
echo ""

TMP_BS="$(mktemp)"
trap 'rm -f "$TMP_BS"' EXIT
sed -e "s|{{INSTALL_DIR}}|$INSTALL_DIR|g" -e "s|{{USER}}|$CURRENT_USER|g" "$BACKEND_SERVICE_FILE" > "$TMP_BS"
sudo cp "$TMP_BS" "$SYSTEMD_DIR/pi-installer-backend.service"
sudo systemctl daemon-reload
sudo systemctl enable pi-installer-backend
sudo systemctl start pi-installer-backend

if systemctl is-active --quiet pi-installer-backend; then
  echo "Backend-Service aktiviert und gestartet: pi-installer-backend (http://localhost:8000)."
  echo "  Status: sudo systemctl status pi-installer-backend"
  echo "  Neustart: sudo systemctl restart pi-installer-backend  oder  ./scripts/restart-backend-service.sh"
else
  echo "Hinweis: Service wurde eingerichtet, startet aber nicht. Log prüfen:"
  echo "  sudo journalctl -u pi-installer-backend -n 30"
  exit 1
fi
