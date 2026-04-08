#!/bin/bash
# Setuphelfer – Saubere Deinstallation (manuelle Installation aus install-system.sh / deploy-to-opt.sh)
# Entfernt Service, Startmenü-Einträge, Symlinks, Verzeichnisse und optional den User.
# Bei Installation per .deb: sudo apt purge setuphelfer
#
# Aufruf: sudo ./scripts/uninstall-system.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }

if [ "$(id -u)" -ne 0 ]; then
  echo -e "${RED}Dieses Skript muss mit sudo ausgeführt werden.${NC}" >&2
  exit 1
fi

INSTALL_DIR="/opt/setuphelfer"
CONFIG_DIR="/etc/setuphelfer"
LOG_DIR="/var/log/setuphelfer"
STATE_DIR="/var/lib/setuphelfer"
BIN_DIR="/usr/local/bin"
SYSTEMD_DIR="/etc/systemd/system"
ENV_DIR="/etc/profile.d"
APPLICATIONS_DIR="/usr/share/applications"
SERVICE_USER="setuphelfer"

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Setuphelfer Deinstallation${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Prüfen ob als .deb installiert
if dpkg -l setuphelfer 2>/dev/null | grep -q '^ii'; then
  echo -e "${YELLOW}Setuphelfer ist als Paket installiert. Bitte deinstallieren mit:${NC}"
  echo "  sudo apt remove setuphelfer    # oder: sudo apt purge setuphelfer"
  echo ""
  read -p "Trotzdem dieses Skript ausführen (Reste entfernen)? (j/n) " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[JjYy]$ ]]; then
    exit 0
  fi
fi

# 1. Service stoppen und entfernen
info "Service stoppen und deaktivieren..."
for u in setuphelfer.service setuphelfer-backend.service pi-installer.service pi-installer-backend.service; do
  systemctl stop "$u" 2>/dev/null || true
  systemctl disable "$u" 2>/dev/null || true
done
rm -f "$SYSTEMD_DIR/setuphelfer.service" "$SYSTEMD_DIR/setuphelfer-backend.service" \
      "$SYSTEMD_DIR/pi-installer.service" "$SYSTEMD_DIR/pi-installer-backend.service"
systemctl daemon-reload
ok "Service entfernt"

# 2. Startmenü-Einträge entfernen
info "Startmenü-Einträge entfernen..."
rm -f "$APPLICATIONS_DIR/pi-installer.desktop" "$APPLICATIONS_DIR/pi-installer-browser.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database -q "$APPLICATIONS_DIR" 2>/dev/null || true
fi
ok "Startmenü-Einträge entfernt"

# 3. Symlinks in /usr/local/bin
info "Symlinks entfernen..."
rm -f "$BIN_DIR/setuphelfer" "$BIN_DIR/setuphelfer-backend" "$BIN_DIR/setuphelfer-frontend" \
      "$BIN_DIR/setuphelfer-start" "$BIN_DIR/setuphelfer-scripts" \
      "$BIN_DIR/pi-installer" "$BIN_DIR/pi-installer-backend" "$BIN_DIR/pi-installer-frontend" \
      "$BIN_DIR/pi-installer-start" "$BIN_DIR/pi-installer-scripts"
ok "Symlinks entfernt"

# 4. Umgebungsvariablen (profile.d)
rm -f "$ENV_DIR/setuphelfer.sh" "$ENV_DIR/pi-installer.sh"
ok "Profile.d-Eintrag entfernt"

# 5. Verzeichnisse löschen
info "Installationsverzeichnisse entfernen..."
rm -rf "$INSTALL_DIR"
rm -rf "$CONFIG_DIR"
rm -rf "$LOG_DIR"
rm -rf "$STATE_DIR"
ok "Verzeichnisse entfernt"

# 6. Optional: Service-User entfernen
if getent passwd "$SERVICE_USER" >/dev/null 2>&1; then
  read -p "Service-User '$SERVICE_USER' ebenfalls entfernen? (j/n) " -n 1 -r
  echo ""
  if [[ $REPLY =~ ^[JjYy]$ ]]; then
    deluser --system "$SERVICE_USER" 2>/dev/null || userdel "$SERVICE_USER" 2>/dev/null || true
    ok "User $SERVICE_USER entfernt"
  else
    warn "User $SERVICE_USER bleibt bestehen."
  fi
fi

echo ""
echo -e "${GREEN}Deinstallation abgeschlossen.${NC}"
echo ""
