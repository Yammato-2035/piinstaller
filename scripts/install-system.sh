#!/bin/bash
# Setuphelfer – Systemweite Installation gemäß Linux Filesystem Hierarchy Standard
# Installiert nach /opt/setuphelfer/ mit Konfiguration in /etc/setuphelfer/
# Erstellt Symlinks, setzt Umgebungsvariablen und richtet systemd Service ein
#
# Verwendung:
#   sudo ./scripts/install-system.sh
#   Oder aus dem Repository: curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/install-system.sh | sudo bash
#
# Nicht-interaktiv (CI / VM-Test, keine read-Prompts):
#   sudo env SETUPHELFER_NONINTERACTIVE=1 \
#     SETUPHELFER_SYSTEMD_ENABLE=yes SETUPHELFER_SYSTEMD_START_NOW=yes \
#     PI_INSTALLER_USER=volker ./scripts/install-system.sh

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
INSTALL_DIR="/opt/setuphelfer"
CONFIG_DIR="/etc/setuphelfer"
LOG_DIR="/var/log/setuphelfer"
STATE_DIR="/var/lib/setuphelfer"
BIN_DIR="/usr/local/bin"
SYSTEMD_DIR="/etc/systemd/system"
ENV_DIR="/etc/profile.d"

# Aktuelles Verzeichnis (Repository-Root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Prüfe ob wir im Repository sind
if [ ! -f "$REPO_ROOT/start.sh" ] || [ ! -d "$REPO_ROOT/backend" ] || [ ! -d "$REPO_ROOT/frontend" ]; then
  err "Repository-Struktur nicht gefunden. Bitte aus dem Setuphelfer-Repository ausführen."
  exit 1
fi

# Service-User (Primär: SETUPHELFER_*; Legacy: PI_INSTALLER_*)
# - SETUPHELFER_USE_SERVICE_USER=1 oder PI_INSTALLER_USE_SERVICE_USER=1 → User setuphelfer
# - SETUPHELFER_USER=… oder PI_INSTALLER_USER=… → fester Login-User
# - sonst → SUDO_USER
SERVICE_USER_NAME="setuphelfer"
USE_SVC="${SETUPHELFER_USE_SERVICE_USER:-${PI_INSTALLER_USE_SERVICE_USER:-0}}"
if [ "$USE_SVC" = "1" ]; then
  if ! getent passwd "$SERVICE_USER_NAME" >/dev/null 2>&1; then
    info "Lege dedizierten Service-User an: $SERVICE_USER_NAME"
    useradd --system --no-create-home --comment "Setuphelfer Service" "$SERVICE_USER_NAME"
    ok "User $SERVICE_USER_NAME erstellt"
  else
    ok "Service-User $SERVICE_USER_NAME existiert bereits"
  fi
  CURRENT_USER="$SERVICE_USER_NAME"
elif [ -n "${SETUPHELFER_USER:-}" ] || [ -n "${PI_INSTALLER_USER:-}" ]; then
  CURRENT_USER="${SETUPHELFER_USER:-$PI_INSTALLER_USER}"
  if ! getent passwd "$CURRENT_USER" >/dev/null 2>&1; then
    err "User $CURRENT_USER existiert nicht. Bitte anlegen oder SETUPHELFER_USER/PI_INSTALLER_USER weglassen."
    exit 1
  fi
else
  CURRENT_USER="${SUDO_USER:-$USER}"
fi
CURRENT_HOME=$(getent passwd "$CURRENT_USER" | cut -d: -f6)

# Gruppe für sichere Backup-Mounts (0770, root:<Gruppe>); systemd: SupplementaryGroups im Backend-Unit
BACKUP_GROUP="${SETUPHELFER_BACKUP_GROUP:-setuphelfer}"
if ! getent group "$BACKUP_GROUP" >/dev/null 2>&1; then
  if groupadd --system "$BACKUP_GROUP" 2>/dev/null; then
    ok "Gruppe $BACKUP_GROUP angelegt (system)"
  elif groupadd "$BACKUP_GROUP" 2>/dev/null; then
    ok "Gruppe $BACKUP_GROUP angelegt"
  else
    warn "Konnte Gruppe $BACKUP_GROUP nicht anlegen — Backup-Ziele ggf. manuell mit root:$BACKUP_GROUP und 0770 einrichten."
  fi
else
  ok "Gruppe $BACKUP_GROUP existiert bereits"
fi
if [ -n "$CURRENT_USER" ] && [ "$CURRENT_USER" != root ] && id "$CURRENT_USER" >/dev/null 2>&1; then
  if usermod -aG "$BACKUP_GROUP" "$CURRENT_USER" 2>/dev/null; then
    ok "User $CURRENT_USER ist Mitglied von $BACKUP_GROUP (für interaktive Shells: neu einloggen)"
  fi
fi

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  Setuphelfer – Systemweite Installation${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""
echo -e "${CYAN}Installationsverzeichnisse:${NC}"
echo -e "  Programm:     ${INSTALL_DIR}"
echo -e "  Konfiguration: ${CONFIG_DIR}"
echo -e "  Logs:          ${LOG_DIR}"
echo -e "  Binaries:      ${BIN_DIR}"
echo ""
echo -e "${CYAN}Service-Benutzer:${NC} ${CURRENT_USER}"
[ "$USE_SVC" = "1" ] && echo -e "  (dedizierter System-User, kein Login)"
[ -n "${SETUPHELFER_USER:-}${PI_INSTALLER_USER:-}" ] && [ "$USE_SVC" != "1" ] && echo -e "  (gesetzt via SETUPHELFER_USER oder PI_INSTALLER_USER)"
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
    rsync \
    build-essential \
    python3-gi \
    gir1.2-gstreamer-1.0 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-pulseaudio \
    >/dev/null 2>&1 || true
  ok "System-Pakete installiert (inkl. GStreamer für DSI Radio v2.0)"
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
mkdir -p "$CONFIG_DIR" "$STATE_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$ENV_DIR"

# Setze Berechtigungen
chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
chown -R "$CURRENT_USER:$CURRENT_USER" "$CONFIG_DIR"
chown -R "$CURRENT_USER:$CURRENT_USER" "$STATE_DIR"
chown -R "$CURRENT_USER:$CURRENT_USER" "$LOG_DIR"
chmod 755 "$INSTALL_DIR"
chmod 755 "$CONFIG_DIR"
chmod 755 "$STATE_DIR"
chmod 755 "$LOG_DIR"

# --- Backup-Ziel /mnt/setuphelfer/backups (NVMe-Tests: nicht unter /media; Gruppe setuphelfer, 0770) ---
SETUPHELFER_BACKUP_STAGING_ROOT="${SETUPHELFER_BACKUP_STAGING_ROOT:-/mnt/setuphelfer}"
SETUPHELFER_BACKUP_DIR="${SETUPHELFER_BACKUP_DIR:-/mnt/setuphelfer/backups}"
if mkdir -p "$SETUPHELFER_BACKUP_DIR" 2>/dev/null; then
  if [ "$(id -u)" -eq 0 ]; then
    chown "root:$BACKUP_GROUP" "$SETUPHELFER_BACKUP_STAGING_ROOT" "$SETUPHELFER_BACKUP_DIR" 2>/dev/null || true
    chmod 0770 "$SETUPHELFER_BACKUP_STAGING_ROOT" "$SETUPHELFER_BACKUP_DIR" 2>/dev/null || true
    ok "Backup-Staging $SETUPHELFER_BACKUP_STAGING_ROOT und $SETUPHELFER_BACKUP_DIR (root:$BACKUP_GROUP, 0770)"
  else
    warn "Nicht als root: Besitzer root:$BACKUP_GROUP und chmod 0770 auf $SETUPHELFER_BACKUP_DIR ggf. manuell setzen."
  fi
else
  warn "Konnte $SETUPHELFER_BACKUP_DIR nicht anlegen (root nötig unter /mnt)."
fi

ok "Verzeichnisse erstellt"

# --- Schritt 2b: Downgrade-Schutz (ältere Quelle darf neuere /opt-Installation nicht überschreiben) ---
if [ -d "$INSTALL_DIR/backend" ] && [ -f "$REPO_ROOT/config/version.json" ]; then
  info "[2b/8] Versionscheck (Quelle vs. bestehende Installation unter $INSTALL_DIR)..."
  if SH_INSTALL_GUARD_REPO="$REPO_ROOT" SH_INSTALL_GUARD_TARGET="$INSTALL_DIR" "$PYTHON" -c "
import os, sys
from pathlib import Path
t = Path(os.environ['SH_INSTALL_GUARD_TARGET'])
sys.path.insert(0, str(t / 'backend'))
try:
    from core.service_conflict_guard import compare_versions, read_version_from_install_root
except ImportError:
    sys.exit(0)
repo = Path(os.environ['SH_INSTALL_GUARD_REPO'])
vr = read_version_from_install_root(repo) or '0'
vi = read_version_from_install_root(t)
if vi and compare_versions(vr, vi) < 0:
    sys.stderr.write(
        'Abbruch: Zielinstallation ist neuer (installiert %s) als die Quelle (%s).\\n'
        % (vi, vr)
    )
    sys.exit(2)
sys.exit(0)
"; then
    ok "Versionscheck bestanden"
  else
    if [ "${SETUPHELFER_ALLOW_DOWNGRADE:-0}" = "1" ]; then
      warn "Versionscheck umgangen (SETUPHELFER_ALLOW_DOWNGRADE=1)."
    else
      err "Installation abgebrochen: neuere Version liegt bereits unter $INSTALL_DIR."
      exit 1
    fi
  fi
fi

# --- Schritt 3: Dateien kopieren ---
info "[3/8] Dateien nach ${INSTALL_DIR} kopieren..."

if ! command -v rsync >/dev/null 2>&1; then
  err "rsync fehlt (wird zum Kopieren ins Installationsverzeichnis benötigt). z. B.: apt-get install -y rsync oder dnf install -y rsync"
  exit 1
fi

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
  # Produktions-Build im Installer erzeugen, damit der systemd-Start kein schweres Build mehr triggern muss.
  export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=1024}"
  if npm run build 2>&1; then
    ok "Frontend-Produktionsbuild erzeugt"
  else
    err "Frontend-Build fehlgeschlagen (npm run build)."
    exit 1
  fi
  if command -v cargo >/dev/null 2>&1; then
    info "Tauri-App bauen (App-Fenster für Startmenü)..."
    if ( cd "$INSTALL_DIR/frontend" && npm run tauri:build 2>&1 ); then
      chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR/frontend"
      ok "Tauri-Binary erstellt"
    else
      warn "Tauri-Build fehlgeschlagen. App-Fenster: später bauen oder Browser-Option nutzen."
    fi
  else
    warn "Rust nicht installiert. Für App-Fenster: Browser wählen oder Rust installieren, dann in frontend: npm run tauri:build"
  fi
else
  warn "npm nicht verfügbar. Frontend kann später mit 'cd $INSTALL_DIR/frontend && npm install' installiert werden."
fi

# --- Schritt 6: Konfiguration erstellen ---
info "[6/8] Konfiguration einrichten..."

# REGRESSION-RISK: systemnahe Konfiguration – Runtime liest ausschließlich config.json; hier nicht auf config.yaml zurückwechseln.
# AUDIT-FIX (A-03): Installer erzeugt config.json. Erstelle Standard-Konfiguration
if [ ! -f "$CONFIG_DIR/config.json" ]; then
  cat > "$CONFIG_DIR/config.json" << 'CONFIGEOF'
{
  "install_dir": "/opt/setuphelfer",
  "config_dir": "/etc/setuphelfer",
  "log_dir": "/var/log/setuphelfer",
  "backend": {"host": "0.0.0.0", "port": 8000},
  "frontend": {"port": 3001}
}
CONFIGEOF
  chown "$CURRENT_USER:$CURRENT_USER" "$CONFIG_DIR/config.json"
  ok "Konfigurationsdatei erstellt"
else
  ok "Konfigurationsdatei existiert bereits"
fi

# --- Schritt 7: Symlinks erstellen ---
info "[7/8] Symlinks erstellen..."

# Haupt-Symlinks
# Primärer Starter: start-setuphelfer.sh (start-pi-installer.sh leitet nur weiter, nicht für neue Desktop-Einträge)
ln -sf "$INSTALL_DIR/scripts/start-setuphelfer.sh" "$BIN_DIR/setuphelfer"
ln -sf "$INSTALL_DIR/scripts/start-backend.sh" "$BIN_DIR/setuphelfer-backend"
ln -sf "$INSTALL_DIR/scripts/start-frontend.sh" "$BIN_DIR/setuphelfer-frontend"
ln -sf "$INSTALL_DIR/start.sh" "$BIN_DIR/setuphelfer-start"
ln -sf "$INSTALL_DIR/scripts" "$BIN_DIR/setuphelfer-scripts"

ok "Symlinks erstellt"

# --- Schritt 8: Umgebungsvariablen setzen ---
info "[8/8] Umgebungsvariablen setzen..."

ENV_FILE="$ENV_DIR/setuphelfer.sh"
cat > "$ENV_FILE" << 'ENVEOF'
# Setuphelfer – aktiver Standard (Primär)
export SETUPHELFER_DIR="/opt/setuphelfer"
export SETUPHELFER_CONFIG_DIR="/etc/setuphelfer"
export SETUPHELFER_LOG_DIR="/var/log/setuphelfer"
export SETUPHELFER_STATE_DIR="/var/lib/setuphelfer"
# Legacy-Kompatibilität (ältere Skripte / Umgebungen lesen PI_INSTALLER_*)
export PI_INSTALLER_DIR="$SETUPHELFER_DIR"
export PI_INSTALLER_CONFIG_DIR="$SETUPHELFER_CONFIG_DIR"
export PI_INSTALLER_LOG_DIR="$SETUPHELFER_LOG_DIR"
export PI_INSTALLER_STATE_DIR="$SETUPHELFER_STATE_DIR"
export PATH="$SETUPHELFER_DIR/scripts:$PATH"
ENVEOF

chmod 644 "$ENV_FILE"
ok "Umgebungsvariablen gesetzt"

# --- Schritt 9: systemd Services einrichten (Backend = Owner :8000; Web-UI getrennt) ---
info "[9/9] systemd Services einrichten..."

for _legacy in pi-installer.service pi-installer-backend.service; do
  if systemctl is-active --quiet "$_legacy" 2>/dev/null; then
    info "Legacy $_legacy ist aktiv — wird gestoppt/deaktiviert (archivierte Daten unter /opt werden nicht geloescht)."
  fi
  systemctl stop "$_legacy" 2>/dev/null || true
  systemctl disable "$_legacy" 2>/dev/null || true
done

PRIMARY_GROUP="$(id -gn "$CURRENT_USER")"
SED_SYS=( -e "s|{{INSTALL_DIR}}|$INSTALL_DIR|g" -e "s|{{USER}}|$CURRENT_USER|g"
  -e "s|{{PI_INSTALLER_CONFIG_DIR}}|$CONFIG_DIR|g" -e "s|{{PI_INSTALLER_LOG_DIR}}|$LOG_DIR|g"
  -e "s|{{PI_INSTALLER_STATE_DIR}}|$STATE_DIR|g" )
sed "${SED_SYS[@]}" "$INSTALL_DIR/setuphelfer-backend.service" > "$SYSTEMD_DIR/setuphelfer-backend.service"
sed -i "s/^Group=.*/Group=$PRIMARY_GROUP/" "$SYSTEMD_DIR/setuphelfer-backend.service" 2>/dev/null || true
sed "${SED_SYS[@]}" "$INSTALL_DIR/setuphelfer.service" > "$SYSTEMD_DIR/setuphelfer.service"
sed -i "s/^Group=.*/Group=$PRIMARY_GROUP/" "$SYSTEMD_DIR/setuphelfer.service" 2>/dev/null || true

# Deterministisch: keine lokalen Drop-Ins für Setuphelfer-Units zulassen.
# Zielzustand kommt ausschließlich aus den Unit-Dateien im Installationsbaum.
rm -rf /etc/systemd/system/setuphelfer.service.d
rm -rf /etc/systemd/system/setuphelfer-backend.service.d

systemctl daemon-reexec
systemctl daemon-reload
ok "systemd: setuphelfer-backend.service + setuphelfer.service geschrieben"

echo ""
_enable_systemd_units=""
_start_systemd_now=""
if [[ "${SETUPHELFER_NONINTERACTIVE:-0}" == "1" || "${CI:-}" == "true" ]]; then
  _enable_systemd_units="${SETUPHELFER_SYSTEMD_ENABLE:-yes}"
  _start_systemd_now="${SETUPHELFER_SYSTEMD_START_NOW:-yes}"
  info "Nicht-interaktiv: systemd enable=${_enable_systemd_units} start_now=${_start_systemd_now}"
else
  read -p "Sollen setuphelfer-backend und setuphelfer beim Booten starten? (j/n) " -n 1 -r
  echo ""
  if [[ $REPLY =~ ^[JjYy]$ ]]; then
    _enable_systemd_units="yes"
  else
    _enable_systemd_units="no"
  fi
fi

if [[ "${_enable_systemd_units}" =~ ^(1|[Yy]|[Yy]es|[Jj]a|[Tt]rue)$ ]]; then
  systemctl enable setuphelfer-backend.service
  systemctl enable setuphelfer.service
  ok "Services aktiviert (Backend + Web-UI)"

  if [[ "${SETUPHELFER_NONINTERACTIVE:-0}" != "1" && "${CI:-}" != "true" ]]; then
    read -p "Jetzt starten? (j/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[JjYy]$ ]]; then
      _start_systemd_now="yes"
    else
      _start_systemd_now="no"
    fi
  fi

  if [[ "${_start_systemd_now}" =~ ^(1|[Yy]|[Yy]es|[Jj]a|[Tt]rue)$ ]]; then
    systemctl start setuphelfer-backend.service
    sleep 2
    systemctl start setuphelfer.service
    _ok_backend=0
    _ok_web=0
    for _i in 1 2 3 4 5 6 7 8; do
      systemctl is-active --quiet setuphelfer-backend.service && _ok_backend=1 || true
      systemctl is-active --quiet setuphelfer.service && _ok_web=1 || true
      if [[ "$_ok_backend" -eq 1 && "$_ok_web" -eq 1 ]]; then
        break
      fi
      sleep 2
    done
    if [[ "$_ok_backend" -eq 1 && "$_ok_web" -eq 1 ]]; then
      ok "Beide Services gestartet"
    else
      err "Service-Validierung fehlgeschlagen: setuphelfer-backend oder setuphelfer ist nicht aktiv."
      journalctl -u setuphelfer-backend -u setuphelfer -n 80 --no-pager || true
      exit 1
    fi
  fi
else
  info "Nicht aktiviert. Start: sudo systemctl start setuphelfer-backend setuphelfer"
fi

# --- Schritt 10: Startmenü-Einträge (Anwendungen) ---
info "Startmenü-Einträge anlegen..."
if [ -f "$INSTALL_DIR/scripts/install-desktop-entries.sh" ]; then
  bash "$INSTALL_DIR/scripts/install-desktop-entries.sh" "$INSTALL_DIR"
  ok "SetupHelfer erscheint im Startmenü unter Anwendungen"
else
  warn "install-desktop-entries.sh nicht gefunden. Startmenü-Einträge später: sudo $INSTALL_DIR/scripts/install-desktop-entries.sh"
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
echo -e "${CYAN}Startmenü:${NC}"
echo -e "  Unter ${GREEN}Anwendungen${NC} / Startmenü: ${GREEN}SetupHelfer${NC} und ${GREEN}SetupHelfer (Browser)${NC}"
echo ""
echo -e "${CYAN}Verfügbare Befehle:${NC}"
echo -e "  ${GREEN}setuphelfer${NC}              - Starter (Tauri/Browser/Backend)"
echo -e "  ${GREEN}setuphelfer-backend${NC}     - Nur Backend"
echo -e "  ${GREEN}setuphelfer-frontend${NC}    - Nur Frontend-Skript"
echo -e "  ${GREEN}setuphelfer-start${NC}       - Wie start.sh"
echo ""
echo -e "${CYAN}Service-Verwaltung:${NC}"
echo -e "  Status:        ${GREEN}sudo systemctl status setuphelfer-backend setuphelfer${NC}"
echo -e "  Starten:       ${GREEN}sudo systemctl start setuphelfer-backend setuphelfer${NC}"
echo -e "  Stoppen:       ${GREEN}sudo systemctl stop setuphelfer setuphelfer-backend${NC}"
echo -e "  Aktivieren:    ${GREEN}sudo systemctl enable setuphelfer-backend setuphelfer${NC}"
echo -e "  Logs:          ${GREEN}sudo journalctl -u setuphelfer-backend -u setuphelfer -f${NC}"
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
