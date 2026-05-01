#!/bin/bash
# Setuphelfer – Systemweite Installation aktualisieren
# Aktualisiert eine bestehende Installation unter /opt/setuphelfer/
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CURRENT_USER="${SUDO_USER:-$USER}"

INSTALL_DIR="/opt/setuphelfer"

# Prüfe ob Installation existiert
if [ ! -d "$INSTALL_DIR" ]; then
  err "Keine Installation gefunden in /opt/setuphelfer"
  err "Bitte zuerst installieren mit: sudo ./scripts/install-system.sh"
  exit 1
fi

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Setuphelfer Update${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

SERVICE_NAME="setuphelfer.service"
LEGACY_SERVICE="pi-installer.service"
SERVICE_WAS_RUNNING=0

# Stoppe Service falls aktiv (neu, dann Legacy)
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
  info "Stoppe Setuphelfer-Service ($SERVICE_NAME)..."
  systemctl stop "$SERVICE_NAME"
  SERVICE_WAS_RUNNING=1
elif systemctl is-active --quiet "$LEGACY_SERVICE" 2>/dev/null; then
  info "Stoppe Legacy-Service ($LEGACY_SERVICE)..."
  systemctl stop "$LEGACY_SERVICE"
  SERVICE_WAS_RUNNING=1
fi

# Backup erstellen
BACKUP_DIR="/tmp/setuphelfer-backup-$(date +%Y%m%d-%H%M%S)"
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
info "Lade systemd neu..."
systemctl daemon-reload
ok "systemd neu geladen"

# Service wieder starten falls er vorher lief
if [ "$SERVICE_WAS_RUNNING" -eq 1 ]; then
  if systemctl cat "$SERVICE_NAME" >/dev/null 2>&1; then
    info "Starte $SERVICE_NAME wieder..."
    systemctl start "$SERVICE_NAME"
    sleep 2
    if systemctl is-active --quiet "$SERVICE_NAME"; then
      ok "Service gestartet ($SERVICE_NAME)"
    else
      warn "Service konnte nicht gestartet werden. Prüfe Logs mit: journalctl -u setuphelfer -n 50"
    fi
  elif systemctl cat "$LEGACY_SERVICE" >/dev/null 2>&1; then
    info "Starte Legacy $LEGACY_SERVICE wieder..."
    systemctl start "$LEGACY_SERVICE"
    sleep 2
    if systemctl is-active --quiet "$LEGACY_SERVICE"; then
      ok "Legacy-Service gestartet"
    else
      warn "Legacy-Service konnte nicht starten. Prüfe: journalctl -u pi-installer -n 50"
    fi
  fi
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Update abgeschlossen!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${CYAN}Backup:${NC} ${BACKUP_DIR}"
echo ""
