#!/bin/bash
# Setuphelfer – Backend nur als systemd-Service einrichten (Start bei Boot, Port 8000).
# Aufruf: ./scripts/install-backend-service.sh
#   oder: SETUPHELFER_DIR=/opt/setuphelfer ./scripts/install-backend-service.sh
#   Legacy: PI_INSTALLER_DIR=… (wenn SETUPHELFER_DIR nicht gesetzt)
#
# Danach: setuphelfer-backend.service
# Status: sudo systemctl status setuphelfer-backend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$REPO_ROOT/scripts/start-backend.sh" ] && [ -d "$REPO_ROOT/backend" ]; then
  INSTALL_DIR="${SETUPHELFER_DIR:-${PI_INSTALLER_DIR:-$REPO_ROOT}}"
else
  INSTALL_DIR="${SETUPHELFER_DIR:-${PI_INSTALLER_DIR:-}}"
  if [ -z "$INSTALL_DIR" ] || [ ! -f "$INSTALL_DIR/scripts/start-backend.sh" ]; then
    echo "Fehler: Bitte Skript aus dem Projektordner aufrufen oder SETUPHELFER_DIR / PI_INSTALLER_DIR setzen." >&2
    exit 1
  fi
fi

CURRENT_USER="${SUDO_USER:-$USER}"
[ -z "$CURRENT_USER" ] && CURRENT_USER="$(whoami)"

if [ "$INSTALL_DIR" = "/opt/setuphelfer" ] && getent passwd setuphelfer >/dev/null 2>&1; then
  CURRENT_USER="setuphelfer"
fi

PI_CFG_DIR="${SETUPHELFER_CONFIG_DIR:-${PI_INSTALLER_CONFIG_DIR:-/etc/setuphelfer}}"
PI_LOG_DIR="${SETUPHELFER_LOG_DIR:-${PI_INSTALLER_LOG_DIR:-/var/log/setuphelfer}}"
PI_STATE_DIR="${SETUPHELFER_STATE_DIR:-${PI_INSTALLER_STATE_DIR:-/var/lib/setuphelfer}}"

BACKEND_SERVICE_FILE="$INSTALL_DIR/setuphelfer-backend.service"
SYSTEMD_DIR="/etc/systemd/system"

if [ ! -f "$BACKEND_SERVICE_FILE" ]; then
  echo "Fehler: Service-Vorlage nicht gefunden: $BACKEND_SERVICE_FILE" >&2
  exit 1
fi

echo "Backend-Service einrichten (Port 8000)..."
echo "  Installationsverzeichnis: $INSTALL_DIR"
echo "  Benutzer: $CURRENT_USER"
echo ""

sudo mkdir -p "$PI_CFG_DIR" "$PI_LOG_DIR" "$PI_STATE_DIR" 2>/dev/null || true

TMP_BS="$(mktemp)"
trap 'rm -f "$TMP_BS"' EXIT
sed -e "s|{{INSTALL_DIR}}|$INSTALL_DIR|g" -e "s|{{USER}}|$CURRENT_USER|g" \
  -e "s|{{PI_INSTALLER_CONFIG_DIR}}|$PI_CFG_DIR|g" -e "s|{{PI_INSTALLER_LOG_DIR}}|$PI_LOG_DIR|g" \
  -e "s|{{PI_INSTALLER_STATE_DIR}}|$PI_STATE_DIR|g" \
  "$BACKEND_SERVICE_FILE" > "$TMP_BS"
sudo cp "$TMP_BS" "$SYSTEMD_DIR/setuphelfer-backend.service"
sudo systemctl daemon-reload
sudo systemctl enable setuphelfer-backend
sudo systemctl start setuphelfer-backend

if systemctl is-active --quiet setuphelfer-backend; then
  echo "Backend-Service: setuphelfer-backend (http://localhost:8000)."
  echo "  Status: sudo systemctl status setuphelfer-backend"
  echo "  Neustart: sudo systemctl restart setuphelfer-backend  oder  ./scripts/restart-backend-service.sh"
else
  echo "Hinweis: Service startet nicht. Log:"
  echo "  sudo journalctl -u setuphelfer-backend -n 30"
  exit 1
fi
