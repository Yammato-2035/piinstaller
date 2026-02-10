#!/bin/bash
# PI-Installer – Systemweite Installation aktualisieren
# Aktualisiert eine bestehende Installation in /opt/pi-installer/
#
# Verwendung:
#   sudo ./scripts/update-system.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[FEHLER]${NC} $*"; }

# Prüfe Root-Rechte
if [ "$(id -u)" -ne 0 ]; then
  err "Dieses Skript muss mit sudo ausgeführt werden: sudo $0"
  exit 1
fi

INSTALL_DIR="/opt/pi-installer"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CURRENT_USER="${SUDO_USER:-$USER}"

# Prüfe ob Installation existiert
if [ ! -d "$INSTALL_DIR" ]; then
  err "Keine Installation gefunden in ${INSTALL_DIR}"
  err "Bitte zuerst installieren mit: sudo ./scripts/install-system.sh"
  exit 1
fi

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  PI-Installer Update${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# Stoppe Service falls aktiv
if systemctl is-active --quiet pi-installer.service 2>/dev/null; then
  info "Stoppe PI-Installer Service..."
  systemctl stop pi-installer.service
  SERVICE_WAS_RUNNING=1
else
  SERVICE_WAS_RUNNING=0
fi

# Backup erstellen
BACKUP_DIR="/tmp/pi-installer-backup-$(date +%Y%m%d-%H%M%S)"
info "Erstelle Backup nach ${BACKUP_DIR}..."
mkdir -p "$BACKUP_DIR"
cp -a "$INSTALL_DIR" "$BACKUP_DIR/" 2>/dev/null || true
ok "Backup erstellt"

# Dateien aktualisieren
info "Aktualisiere Dateien..."
rsync -a --exclude='.git' \
      --exclude='node_modules' \
      --exclude='venv' \
      --exclude='__pycache__' \
      --exclude='*.pyc' \
      --exclude='.env' \
      --exclude='dist' \
      --exclude='target' \
      "$REPO_ROOT/" "$INSTALL_DIR/"

chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
find "$INSTALL_DIR" -type f -name "*.sh" -exec chmod +x {} \;
ok "Dateien aktualisiert"

# Backend-Dependencies aktualisieren
info "Aktualisiere Backend-Dependencies..."
cd "$INSTALL_DIR/backend"
if [ -d "venv" ]; then
  source venv/bin/activate
  pip install --upgrade pip --quiet
  pip install -r requirements.txt --upgrade --quiet 2>&1 | grep -v "already satisfied" || true
  ok "Backend-Dependencies aktualisiert"
else
  warn "venv nicht gefunden. Erstelle neu..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt --quiet
  ok "Backend-Dependencies installiert"
fi

# Frontend-Dependencies aktualisieren
if command -v npm >/dev/null 2>&1; then
  info "Aktualisiere Frontend-Dependencies..."
  cd "$INSTALL_DIR/frontend"
  npm install --silent 2>&1 | grep -v "npm WARN" || true
  ok "Frontend-Dependencies aktualisiert"
fi

# Service neu laden
info "Lade systemd Service neu..."
systemctl daemon-reload
ok "Service neu geladen"

# Service wieder starten falls er vorher lief
if [ "$SERVICE_WAS_RUNNING" -eq 1 ]; then
  info "Starte Service wieder..."
  systemctl start pi-installer.service
  sleep 2
  if systemctl is-active --quiet pi-installer.service; then
    ok "Service gestartet"
  else
    warn "Service konnte nicht gestartet werden. Prüfe Logs mit: journalctl -u pi-installer -n 50"
  fi
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Update abgeschlossen!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${CYAN}Backup:${NC} ${BACKUP_DIR}"
echo ""
