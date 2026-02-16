#!/bin/bash
# PI-Installer – Deploy aus aktuellem Repo nach /opt/pi-installer
# Legt Service-User pi-installer an, kopiert Dateien, richtet Venv/Frontend ein, startet Service.
# Kann vom PI-Installer (Backend) per sudo aufgerufen werden oder manuell.
#
# Verwendung:
#   sudo ./scripts/deploy-to-opt.sh [QUELLVERZEICHNIS]
#   Ohne Argument: Quellverzeichnis = Repo-Root (über diesem Skript).
#   Mit Argument: z. B. sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller

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

if [ "$(id -u)" -ne 0 ]; then
  err "Dieses Skript muss mit sudo ausgeführt werden: sudo $0 [QUELLVERZEICHNIS]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
DEFAULT_SOURCE="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="${1:-$DEFAULT_SOURCE}"
INSTALL_DIR="/opt/pi-installer"
CONFIG_DIR="/etc/pi-installer"
LOG_DIR="/var/log/pi-installer"
SYSTEMD_DIR="/etc/systemd/system"
SERVICE_USER_NAME="pi-installer"

if [ ! -f "$SOURCE_DIR/start.sh" ] || [ ! -d "$SOURCE_DIR/backend" ] || [ ! -d "$SOURCE_DIR/frontend" ]; then
  err "Kein gültiges PI-Installer-Repo unter: $SOURCE_DIR"
  exit 1
fi

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  PI-Installer → /opt installieren/aktualisieren${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "  Quelle:  ${SOURCE_DIR}"
echo -e "  Ziel:    ${INSTALL_DIR}"
echo -e "  User:    ${SERVICE_USER_NAME}"
echo ""

# Service-User anlegen
if ! getent passwd "$SERVICE_USER_NAME" >/dev/null 2>&1; then
  info "Lege Service-User an: $SERVICE_USER_NAME"
  useradd --system --no-create-home --comment "PI-Installer Service" "$SERVICE_USER_NAME"
  ok "User $SERVICE_USER_NAME erstellt"
else
  ok "Service-User $SERVICE_USER_NAME existiert bereits"
fi

# Verzeichnisse
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"

# Dateien kopieren (wie install-system.sh)
info "Kopiere Dateien nach ${INSTALL_DIR}..."
rsync -a --exclude='.git' \
      --exclude='node_modules' \
      --exclude='venv' \
      --exclude='__pycache__' \
      --exclude='*.pyc' \
      --exclude='.env' \
      --exclude='dist' \
      --exclude='target' \
      "$SOURCE_DIR/" "$INSTALL_DIR/"
# Berechtigungen erst am Ende setzen, damit root alle Build-Schritte (venv, npm, tauri) ausführen kann
find "$INSTALL_DIR" -type f -name "*.sh" -exec chmod +x {} \;
ok "Dateien kopiert"

# Backend Venv (als root anlegen, dann chown – Service braucht keine Schreibrechte in venv außer pip cache)
info "Backend Virtual Environment..."
cd "$INSTALL_DIR/backend"
PYTHON=""
for py in python3.12 python3.11 python3.10 python3.9 python3; do
  if command -v "$py" >/dev/null 2>&1; then
    if "$py" -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
      PYTHON="$py"
      break
    fi
  fi
done
if [ -z "$PYTHON" ]; then
  err "Python 3.9+ nicht gefunden."
  exit 1
fi
if [ ! -d "venv" ]; then
  "$PYTHON" -m venv venv
fi
export PIP_CACHE_DIR="$INSTALL_DIR/.pip-cache"
mkdir -p "$PIP_CACHE_DIR"
./venv/bin/pip install --upgrade pip -q 2>/dev/null || true
./venv/bin/pip install -r requirements.txt -q 2>&1 | grep -v "already satisfied" || true
ok "Backend-Dependencies installiert"

# Frontend (als root, damit dist/ und target/ erstellt werden können)
if command -v npm >/dev/null 2>&1; then
  info "Frontend Dependencies..."
  cd "$INSTALL_DIR/frontend"
  npm install --silent 2>&1 | grep -v "npm WARN" || true
  ok "Frontend-Dependencies installiert"
  # Tauri-Build: Cargo/Rust liegen oft im Benutzer-Kontext; mit sudo ist $HOME=/root und cargo fehlt.
  # Daher Build als der User ausführen, der sudo aufgerufen hat (der hat meist Rust).
  BUILD_USER="${SUDO_USER:-}"
  if [ -n "$BUILD_USER" ] && su - "$BUILD_USER" -c "command -v cargo" >/dev/null 2>&1; then
    info "Tauri-App bauen als User $BUILD_USER (kann einige Minuten dauern)..."
    chown -R "$BUILD_USER:$BUILD_USER" "$INSTALL_DIR/frontend"
    if su - "$BUILD_USER" -c "cd $INSTALL_DIR/frontend && export GDK_BACKEND=x11 && npm run tauri:build" 2>&1; then
      ok "Tauri-Binary erstellt (App-Fenster verfügbar)"
    else
      warn "Tauri-Build fehlgeschlagen. App-Fenster: Browser-Option oder manuell bauen (ohne sudo im Repo: npm run tauri:build, dann target/ nach /opt kopieren)."
    fi
    # Frontend wieder root, finaler chown kommt unten
    chown -R root:root "$INSTALL_DIR/frontend"
  elif command -v cargo >/dev/null 2>&1; then
    info "Tauri-App bauen (kann einige Minuten dauern)..."
    if ( export GDK_BACKEND=x11; npm run tauri:build 2>&1 ); then
      ok "Tauri-Binary erstellt (App-Fenster verfügbar)"
    else
      warn "Tauri-Build fehlgeschlagen. App-Fenster unter /opt: Browser-Option nutzen oder später mit Ihrem User bauen."
    fi
  else
    warn "Rust/Cargo nicht installiert (oder nur für einen anderen User). Tauri: Browser wählen oder als User mit Rust ausführen: sudo -u IhrUser ./scripts/deploy-to-opt.sh"
  fi
else
  warn "npm nicht gefunden. Frontend später: cd $INSTALL_DIR/frontend && npm install"
fi

# Jetzt alles an Service-User übergeben (nach allen Build-Schritten)
chown -R "$SERVICE_USER_NAME:$SERVICE_USER_NAME" "$INSTALL_DIR"
chown -R "$SERVICE_USER_NAME:$SERVICE_USER_NAME" "$CONFIG_DIR"
chown -R "$SERVICE_USER_NAME:$SERVICE_USER_NAME" "$LOG_DIR"

# systemd Service (falls noch nicht vorhanden oder anpassen)
SERVICE_FILE="$SYSTEMD_DIR/pi-installer.service"
if [ ! -f "$SERVICE_FILE" ] || ! grep -q "User=$SERVICE_USER_NAME" "$SERVICE_FILE" 2>/dev/null; then
  info "Systemd-Service einrichten..."
  cat > "$SERVICE_FILE" << SERVICEEOF
[Unit]
Description=PI-Installer (Backend + Frontend)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER_NAME
Group=$SERVICE_USER_NAME
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/start.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment="PI_INSTALLER_DIR=$INSTALL_DIR"
Environment="PI_INSTALLER_CONFIG_DIR=$CONFIG_DIR"
Environment="PI_INSTALLER_LOG_DIR=$LOG_DIR"
Environment="PI_INSTALLER_DEV=0"
Environment="PIP_CACHE_DIR=$INSTALL_DIR/.pip-cache"
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$INSTALL_DIR $CONFIG_DIR $LOG_DIR

[Install]
WantedBy=multi-user.target
SERVICEEOF
  systemctl daemon-reload
  ok "Service-Datei geschrieben"
fi

# Konfiguration (nur anlegen wenn nicht vorhanden)
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
  cat > "$CONFIG_DIR/config.yaml" << 'CONFIGEOF'
install_dir: /opt/pi-installer
config_dir: /etc/pi-installer
log_dir: /var/log/pi-installer
backend:
  host: 0.0.0.0
  port: 8000
frontend:
  port: 3001
CONFIGEOF
  chown "$SERVICE_USER_NAME:$SERVICE_USER_NAME" "$CONFIG_DIR/config.yaml"
  ok "Konfiguration erstellt"
fi

# Service starten/neu starten
systemctl daemon-reload
if systemctl is-active --quiet pi-installer.service 2>/dev/null; then
  info "Starte Service neu..."
  systemctl restart pi-installer.service
  ok "Service neu gestartet"
else
  info "Starte Service..."
  systemctl enable pi-installer.service 2>/dev/null || true
  systemctl start pi-installer.service
  ok "Service gestartet"
fi

# Startmenü-Einträge (Anwendungen)
if [ -f "$INSTALL_DIR/scripts/install-desktop-entries.sh" ]; then
  info "Startmenü-Einträge anlegen..."
  bash "$INSTALL_DIR/scripts/install-desktop-entries.sh" "$INSTALL_DIR"
  ok "PI-Installer erscheint im Startmenü"
fi

echo ""
ok "Deploy abgeschlossen. PI-Installer läuft unter $INSTALL_DIR als User $SERVICE_USER_NAME."
echo ""
