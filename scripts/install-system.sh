#!/bin/bash
# PI-Installer – Systemweite Installation gemäß Linux Filesystem Hierarchy Standard
# Installiert PI-Installer nach /opt/pi-installer/ mit Konfiguration in /etc/pi-installer/
# Erstellt Symlinks, setzt Umgebungsvariablen und richtet systemd Service ein
#
# Verwendung:
#   sudo ./scripts/install-system.sh
#   Oder aus dem Repository: curl -sSL https://raw.githubusercontent.com/.../install-system.sh | sudo bash

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

# Installationsverzeichnisse (gemäß Linux FHS)
INSTALL_DIR="/opt/pi-installer"
CONFIG_DIR="/etc/pi-installer"
LOG_DIR="/var/log/pi-installer"
BIN_DIR="/usr/local/bin"
SYSTEMD_DIR="/etc/systemd/system"
ENV_DIR="/etc/profile.d"

# Aktuelles Verzeichnis (Repository-Root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Prüfe ob wir im Repository sind
if [ ! -f "$REPO_ROOT/start.sh" ] || [ ! -d "$REPO_ROOT/backend" ] || [ ! -d "$REPO_ROOT/frontend" ]; then
  err "Repository-Struktur nicht gefunden. Bitte aus dem PI-Installer-Verzeichnis ausführen."
  exit 1
fi

# Aktueller Benutzer (für Dateiberechtigungen)
CURRENT_USER="${SUDO_USER:-$USER}"
CURRENT_HOME=$(getent passwd "$CURRENT_USER" | cut -d: -f6)

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  PI-Installer Systemweite Installation${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "${CYAN}Installationsverzeichnisse:${NC}"
echo -e "  Programm:     ${INSTALL_DIR}"
echo -e "  Konfiguration: ${CONFIG_DIR}"
echo -e "  Logs:          ${LOG_DIR}"
echo -e "  Binaries:      ${BIN_DIR}"
echo ""
echo -e "${CYAN}Benutzer:${NC} ${CURRENT_USER}"
echo ""

# --- Schritt 1: System-Abhängigkeiten installieren ---
info "[1/8] System-Abhängigkeiten prüfen und installieren..."

if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    nodejs \
    npm \
    git \
    curl \
    wget \
    build-essential \
    >/dev/null 2>&1 || true
  ok "System-Pakete installiert"
else
  warn "apt-get nicht gefunden. Bitte Python 3.9+, Node.js und npm manuell installieren."
fi

# Prüfe Python-Version
PYTHON=""
for py in python3.12 python3.11 python3.10 python3.9 python3; do
  if command -v "$py" >/dev/null 2>&1; then
    if "$py" -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
      PYTHON="$py"
      ok "Python gefunden: $py ($($py --version 2>&1))"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  err "Python 3.9+ wird benötigt. Bitte installieren Sie Python und starten Sie das Skript erneut."
  exit 1
fi

# Prüfe Node.js
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  ok "Node.js gefunden: $(node -v 2>&1), npm $(npm -v 2>&1)"
else
  warn "Node.js/npm nicht gefunden. Frontend kann später installiert werden."
fi

# --- Schritt 2: Verzeichnisse erstellen ---
info "[2/8] Verzeichnisse erstellen..."

mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$ENV_DIR"

# Setze Berechtigungen
chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
chown -R "$CURRENT_USER:$CURRENT_USER" "$CONFIG_DIR"
chown -R "$CURRENT_USER:$CURRENT_USER" "$LOG_DIR"
chmod 755 "$INSTALL_DIR"
chmod 755 "$CONFIG_DIR"
chmod 755 "$LOG_DIR"

ok "Verzeichnisse erstellt"

# --- Schritt 3: Dateien kopieren ---
info "[3/8] Dateien nach ${INSTALL_DIR} kopieren..."

# Kopiere alle Dateien (ausgenommen .git, node_modules, venv, etc.)
rsync -a --exclude='.git' \
      --exclude='node_modules' \
      --exclude='venv' \
      --exclude='__pycache__' \
      --exclude='*.pyc' \
      --exclude='.env' \
      --exclude='dist' \
      --exclude='target' \
      "$REPO_ROOT/" "$INSTALL_DIR/"

# Setze Berechtigungen
chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
find "$INSTALL_DIR" -type f -name "*.sh" -exec chmod +x {} \;

ok "Dateien kopiert"

# --- Schritt 4: Backend einrichten ---
info "[4/8] Backend einrichten..."

cd "$INSTALL_DIR/backend"

# Erstelle venv
if [ ! -d "venv" ]; then
  "$PYTHON" -m venv venv
  ok "Python Virtual Environment erstellt"
fi

# Aktiviere venv und installiere Dependencies
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet 2>&1 | grep -v "already satisfied" || true
ok "Backend-Dependencies installiert"

# --- Schritt 5: Frontend einrichten ---
info "[5/8] Frontend einrichten..."

if command -v npm >/dev/null 2>&1; then
  cd "$INSTALL_DIR/frontend"
  npm install --silent 2>&1 | grep -v "npm WARN" || true
  ok "Frontend-Dependencies installiert"
else
  warn "npm nicht verfügbar. Frontend kann später mit 'cd $INSTALL_DIR/frontend && npm install' installiert werden."
fi

# --- Schritt 6: Konfiguration erstellen ---
info "[6/8] Konfiguration einrichten..."

# Erstelle Standard-Konfiguration
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
  cat > "$CONFIG_DIR/config.yaml" << 'CONFIGEOF'
# PI-Installer Konfiguration
# Wird automatisch beim Start geladen

install_dir: /opt/pi-installer
config_dir: /etc/pi-installer
log_dir: /var/log/pi-installer

backend:
  host: 0.0.0.0
  port: 8000

frontend:
  port: 3001
CONFIGEOF
  chown "$CURRENT_USER:$CURRENT_USER" "$CONFIG_DIR/config.yaml"
  ok "Konfigurationsdatei erstellt"
else
  ok "Konfigurationsdatei existiert bereits"
fi

# --- Schritt 7: Symlinks erstellen ---
info "[7/8] Symlinks erstellen..."

# Haupt-Symlinks
ln -sf "$INSTALL_DIR/start-pi-installer.sh" "$BIN_DIR/pi-installer"
ln -sf "$INSTALL_DIR/start-backend.sh" "$BIN_DIR/pi-installer-backend"
ln -sf "$INSTALL_DIR/start-frontend.sh" "$BIN_DIR/pi-installer-frontend"
ln -sf "$INSTALL_DIR/start.sh" "$BIN_DIR/pi-installer-start"

# Script-Symlinks
ln -sf "$INSTALL_DIR/scripts" "$BIN_DIR/pi-installer-scripts"

ok "Symlinks erstellt"

# --- Schritt 8: Umgebungsvariablen setzen ---
info "[8/8] Umgebungsvariablen setzen..."

ENV_FILE="$ENV_DIR/pi-installer.sh"
cat > "$ENV_FILE" << 'ENVEOF'
# PI-Installer Umgebungsvariablen
# Wird automatisch beim Login geladen

export PI_INSTALLER_DIR="/opt/pi-installer"
export PI_INSTALLER_CONFIG_DIR="/etc/pi-installer"
export PI_INSTALLER_LOG_DIR="/var/log/pi-installer"
export PATH="$PI_INSTALLER_DIR/scripts:$PATH"
ENVEOF

chmod 644 "$ENV_FILE"
ok "Umgebungsvariablen gesetzt"

# --- Schritt 9: systemd Service einrichten ---
info "[9/9] systemd Service einrichten..."

SERVICE_FILE="$SYSTEMD_DIR/pi-installer.service"

# Erstelle Service-Datei
cat > "$SERVICE_FILE" << SERVICEEOF
[Unit]
Description=PI-Installer (Backend + Frontend)
Documentation=https://github.com/pi-installer/PI-Installer
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${CURRENT_USER}
Group=${CURRENT_USER}
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/start.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="PI_INSTALLER_DIR=${INSTALL_DIR}"
Environment="PI_INSTALLER_CONFIG_DIR=${CONFIG_DIR}"
Environment="PI_INSTALLER_LOG_DIR=${LOG_DIR}"
Environment="PI_INSTALLER_DEV=0"

# Sicherheit
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=${INSTALL_DIR} ${CONFIG_DIR} ${LOG_DIR}

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Lade systemd neu
systemctl daemon-reload
ok "systemd Service erstellt"

# Frage ob Service aktiviert werden soll
echo ""
read -p "Soll der PI-Installer Service automatisch beim Booten starten? (j/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[JjYy]$ ]]; then
  systemctl enable pi-installer.service
  ok "Service aktiviert (startet beim Booten)"
  
  read -p "Soll der Service jetzt gestartet werden? (j/n) " -n 1 -r
  echo ""
  if [[ $REPLY =~ ^[JjYy]$ ]]; then
    systemctl start pi-installer.service
    sleep 2
    if systemctl is-active --quiet pi-installer.service; then
      ok "Service gestartet"
    else
      warn "Service konnte nicht gestartet werden. Prüfe Logs mit: journalctl -u pi-installer -n 50"
    fi
  fi
else
  info "Service nicht aktiviert. Starten mit: sudo systemctl start pi-installer"
fi

# --- Zusammenfassung ---
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Installation abgeschlossen!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "${CYAN}Installationsverzeichnisse:${NC}"
echo -e "  Programm:     ${INSTALL_DIR}"
echo -e "  Konfiguration: ${CONFIG_DIR}"
echo -e "  Logs:          ${LOG_DIR}"
echo ""
echo -e "${CYAN}Verfügbare Befehle:${NC}"
echo -e "  ${GREEN}pi-installer${NC}              - Startet PI-Installer (Backend + Frontend)"
echo -e "  ${GREEN}pi-installer-backend${NC}     - Startet nur Backend"
echo -e "  ${GREEN}pi-installer-frontend${NC}    - Startet nur Frontend"
echo -e "  ${GREEN}pi-installer-start${NC}      - Startet beide Services"
echo ""
echo -e "${CYAN}Service-Verwaltung:${NC}"
echo -e "  Status:        ${GREEN}sudo systemctl status pi-installer${NC}"
echo -e "  Starten:       ${GREEN}sudo systemctl start pi-installer${NC}"
echo -e "  Stoppen:       ${GREEN}sudo systemctl stop pi-installer${NC}"
echo -e "  Aktivieren:    ${GREEN}sudo systemctl enable pi-installer${NC}"
echo -e "  Logs:          ${GREEN}sudo journalctl -u pi-installer -f${NC}"
echo ""
echo -e "${CYAN}Zugriff:${NC}"
echo -e "  Web-Interface: ${GREEN}http://localhost:3001${NC}"
echo -e "  API:           ${GREEN}http://localhost:8000${NC}"
echo ""
echo -e "${CYAN}Umgebungsvariablen:${NC}"
echo -e "  Werden automatisch beim nächsten Login geladen"
echo -e "  Oder jetzt laden mit: ${GREEN}source ${ENV_FILE}${NC}"
echo ""
echo -e "${YELLOW}Hinweis:${NC} Nach der Installation müssen Sie sich einmal ab- und wieder anmelden,"
echo -e "damit die Umgebungsvariablen geladen werden. Oder führen Sie aus:"
echo -e "  ${CYAN}source ${ENV_FILE}${NC}"
echo ""
