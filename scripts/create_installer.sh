#!/bin/bash
# PI-Installer – Single-Script-Installer (One-Click Experience)
# Nutzung:
#   Aus dem Repository:  ./scripts/create_installer.sh
#   Oder (wenn gehostet): curl -sSL https://get.pi-installer.io | bash
#
# Umgebungsvariablen:
#   PI_INSTALLER_REPO   – Git-URL zum Klonen (nur bei curl | bash nötig)
#   PI_INSTALLER_DIR   – Installationsverzeichnis (Default: $HOME/PI-Installer bei Klon)

set -e
set -u

# Farben für Status (optional, funktioniert auch ohne)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()   { echo -e "${RED}[FEHLER]${NC} $*"; }

# Prüfen ob wir innerhalb eines PI-Installer-Repos sind (start.sh + backend vorhanden)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if [ -f "$REPO_ROOT/start.sh" ] && [ -d "$REPO_ROOT/backend" ] && [ -d "$REPO_ROOT/frontend" ]; then
  INSTALL_DIR="$REPO_ROOT"
  FROM_REPO=1
else
  INSTALL_DIR="${PI_INSTALLER_DIR:-$HOME/PI-Installer}"
  FROM_REPO=0
fi

# Standard-Repo beim Aufruf per "curl | bash" (ersetzen Sie OWNER durch Ihren GitHub-Benutzernamen)
DEFAULT_REPO_URL="${PI_INSTALLER_DEFAULT_REPO:-https://github.com/pi-installer/PI-Installer.git}"
REPO_URL="${PI_INSTALLER_REPO:-$DEFAULT_REPO_URL}"
TOTAL_STEPS=6
STEP=0

step() {
  STEP=$((STEP + 1))
  echo ""
  echo -e "${CYAN}[$STEP/$TOTAL_STEPS]${NC} $*"
}

# ---------- Schritt 1: Python erkennen / installieren ----------
step "Python prüfen..."
PYTHON=""
for py in python3.12 python3.11 python3.10 python3.9 python3; do
  if command -v "$py" >/dev/null 2>&1; then
    ver=$("$py" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || true)
    if [ -n "$ver" ]; then
      PYTHON="$py"
      ok "Gefunden: $py ($ver)"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  warn "Kein passendes Python gefunden. Versuche Installation..."
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq
    sudo apt-get install -y python3 python3-venv python3-pip 2>/dev/null || true
    PYTHON="python3"
  fi
fi

if [ -z "$PYTHON" ] || ! $PYTHON -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
  err "Python 3.9 oder neuer wird benötigt. Bitte installieren Sie Python und starten Sie das Skript erneut."
  err "Anleitung: siehe PYTHON_SETUP.md oder https://www.python.org/downloads/"
  exit 1
fi

# ---------- Schritt 2: Node.js prüfen (für Frontend) ----------
step "Node.js prüfen..."
NODE_OK=0
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
  NODE_OK=1
  ok "Node.js $(node -v 2>/dev/null), npm $(npm -v 2>/dev/null)"
fi

if [ $NODE_OK -eq 0 ] && command -v apt-get >/dev/null 2>&1; then
  warn "Node.js/npm nicht gefunden. Versuche Installation..."
  sudo apt-get update -qq
  sudo apt-get install -y nodejs npm 2>/dev/null || true
  command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1 && NODE_OK=1
fi

if [ $NODE_OK -eq 0 ]; then
  warn "Node.js/npm nicht verfügbar. Frontend kann später mit: sudo apt install nodejs npm  nachinstalliert werden."
  warn "Installation wird trotzdem fortgesetzt (Backend funktioniert)."
fi

# ---------- Schritt 3: Repository klonen (falls nicht aus Repo) ----------
step "Repository vorbereiten..."
if [ $FROM_REPO -eq 1 ]; then
  ok "Bestehendes Repository genutzt: $INSTALL_DIR"
else
  if [ -z "$REPO_URL" ]; then
    err "Nicht im PI-Installer-Repository und keine Repo-URL gesetzt."
    err "So nutzen: PI_INSTALLER_REPO=https://github.com/IHR-USER/PI-Installer.git $0"
    err "Oder Skript aus dem geklonten Ordner ausführen: ./scripts/create_installer.sh"
    exit 1
  fi
  if [ -d "$INSTALL_DIR/.git" ]; then
    ok "Verzeichnis existiert bereits: $INSTALL_DIR (git pull)"
    git -C "$INSTALL_DIR" pull --rebase 2>/dev/null || true
  else
    info "Klone $REPO_URL nach $INSTALL_DIR ..."
    git clone "$REPO_URL" "$INSTALL_DIR" 2>/dev/null || {
      err "Klonen fehlgeschlagen. Prüfen Sie Internet und URL: $REPO_URL"
      exit 1
    }
    ok "Repository geklont."
  fi
fi

# ---------- Schritt 4: Backend (venv + pip) ----------
step "Backend einrichten..."
cd "$INSTALL_DIR/backend"
if [ ! -d "venv" ]; then
  $PYTHON -m venv venv
  ok "Virtuelle Umgebung erstellt."
fi
# shellcheck source=/dev/null
source venv/bin/activate
if ! python3 -c "import fastapi" 2>/dev/null; then
  info "Installiere Python-Abhängigkeiten..."
  pip install -q --upgrade pip
  pip install -r requirements.txt --only-binary :all: 2>/dev/null || pip install -r requirements.txt
  ok "Backend-Abhängigkeiten installiert."
else
  ok "Backend-Abhängigkeiten bereits vorhanden."
fi
deactivate 2>/dev/null || true

# ---------- Schritt 5: Frontend (npm) ----------
step "Frontend einrichten..."
cd "$INSTALL_DIR/frontend"
if [ $NODE_OK -eq 1 ]; then
  if [ ! -d "node_modules" ]; then
    info "Installiere Node-Abhängigkeiten (kann etwas dauern)..."
    npm install
    ok "Frontend-Abhängigkeiten installiert."
  else
    ok "Frontend-Abhängigkeiten bereits vorhanden."
  fi
else
  warn "Node.js fehlt – Frontend-Build übersprungen. Bitte später: cd $INSTALL_DIR/frontend && npm install"
fi

# ---------- Schritt 6: systemd-Service (optional) ----------
step "Systemd-Service einrichten..."
CURRENT_USER="${SUDO_USER:-$USER}"
if [ -z "$CURRENT_USER" ]; then
  CURRENT_USER="$(whoami)"
fi

SERVICE_FILE="$INSTALL_DIR/pi-installer.service"
SYSTEMD_DIR="/etc/systemd/system"
if [ -f "$SERVICE_FILE" ]; then
  if [ -w "$SYSTEMD_DIR" ] || sudo -n true 2>/dev/null; then
    TMP_SVC="$(mktemp)"
    sed -e "s|{{INSTALL_DIR}}|$INSTALL_DIR|g" -e "s|{{USER}}|$CURRENT_USER|g" "$SERVICE_FILE" > "$TMP_SVC"
    sudo cp "$TMP_SVC" "$SYSTEMD_DIR/pi-installer.service"
    rm -f "$TMP_SVC"
    sudo systemctl daemon-reload
    sudo systemctl enable pi-installer 2>/dev/null || true
    sudo systemctl start pi-installer 2>/dev/null || true
    ok "Service aktiviert und gestartet: pi-installer (Start bei Boot)."
  else
    warn "Keine Schreibrechte für $SYSTEMD_DIR. Service manuell einrichten:"
    echo "  sudo cp $SERVICE_FILE $SYSTEMD_DIR/"
    echo "  sudo sed -i 's|{{INSTALL_DIR}}|$INSTALL_DIR|g;s|{{USER}}|$CURRENT_USER|g' $SYSTEMD_DIR/pi-installer.service"
    echo "  sudo systemctl daemon-reload && sudo systemctl enable --now pi-installer"
  fi
else
  warn "Service-Vorlage nicht gefunden: $SERVICE_FILE – Start bitte manuell mit: $INSTALL_DIR/start.sh"
fi

# ---------- Abschluss ----------
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PI-Installer Installation abgeschlossen${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# URL ermitteln (mDNS oder IP)
LAN_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
if [ -n "$LAN_IP" ] && [ "$LAN_IP" != "127.0.0.1" ]; then
  echo "  Öffnen Sie im Browser:"
  echo ""
  echo "    http://${LAN_IP}:3001"
  echo ""
  echo "  Falls mDNS funktioniert (z. B. von anderem Gerät im Netz):"
  echo "    http://pi-installer.local:3001"
else
  echo "  Öffnen Sie im Browser:"
  echo ""
  echo "    http://localhost:3001"
  echo ""
fi

echo "  Falls der Service gestartet wurde, läuft PI-Installer bereits."
echo "  Sonst starten mit:  $INSTALL_DIR/start.sh"
echo "  Oder als Dienst:    sudo systemctl start pi-installer"
echo ""
