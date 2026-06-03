#!/bin/bash
# Setuphelfer – Deploy aus aktuellem Repo nach /opt/setuphelfer
# Legt Service-User setuphelfer an, kopiert Dateien, richtet Venv/Frontend ein, startet setuphelfer-backend + setuphelfer.
# Kann vom Backend (Deploy-Aktion) per sudo aufgerufen werden oder manuell.
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

safe_chown_tree() {
  local target="$1"
  if ! chown -R "$SERVICE_USER_NAME:$SERVICE_USER_NAME" "$target" 2>/dev/null; then
    warn "chown übersprungen für $target (z. B. read-only systemd namespace oder geschützte Runtime-Dateien)."
  fi
}

wait_for_backend_api() {
  if ! command -v curl >/dev/null 2>&1; then
    warn "curl fehlt — Backend-API-Verifikation übersprungen."
    return 0
  fi
  local code="000"
  local attempt
  info "Warte auf /api/version (max. 15×2s)…"
  for attempt in $(seq 1 15); do
    code="$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 2 --max-time 5 http://127.0.0.1:8000/api/version 2>/dev/null || echo 000)"
    if [ "$code" = "200" ]; then
      ok "Backend-API antwortet wieder auf /api/version (Versuch $attempt/15)"
      return 0
    fi
    sleep 2
  done
  err "Backend-API antwortet nach Service-Restart nicht (letzter HTTP-Code: $code)."
  warn "Prüfe: journalctl -u setuphelfer-backend.service -n 200 --no-pager"
  warn "Hinweis: nach Unit-/Drop-in-Änderungen immer systemctl daemon-reload vor restart."
  return 1
}

write_backend_workspace_dropin() {
  local ws_root="$1"
  local dropin_dir="$SYSTEMD_DIR/setuphelfer-backend.service.d"
  local dropin_file="$dropin_dir/dev-workspace.conf"
  local tmp_dropin

  if [[ -z "$ws_root" || ! "$ws_root" = /* ]]; then
    warn "Backend-Workspace-Drop-in übersprungen (kein absoluter Workspace-Pfad): $ws_root"
    return 0
  fi
  if [[ ! "$ws_root" = /home/* ]]; then
    warn "Backend-Workspace-Drop-in nur für /home-Workspaces vorgesehen; übersprungen: $ws_root"
    return 0
  fi
  if [[ ! -w "$SYSTEMD_DIR" ]]; then
    warn "Backend-Workspace-Drop-in konnte in diesem Kontext nicht geschrieben werden."
    return 0
  fi

  mkdir -p "$ws_root/build/rescue" "$ws_root/docs/evidence/runtime-results/rescue"
  mkdir -p "$dropin_dir"
  tmp_dropin="$(mktemp)"
  cat >"$tmp_dropin" <<EOF
# Auto: deploy-to-opt.sh — Dev-Workspace für Deploy-Drift / Rescue-Executor
[Service]
Environment="SETUPHELFER_DEV_WORKSPACE_ROOT=$ws_root"
ProtectHome=read-only
ReadOnlyPaths=$ws_root
ReadWritePaths=$ws_root/build/rescue
ReadWritePaths=$ws_root/docs/evidence/runtime-results/rescue
SupplementaryGroups=setuphelfer workspace
EOF
  install -m 0644 "$tmp_dropin" "$dropin_file"
  rm -f "$tmp_dropin"
  ok "systemd: backend dev-workspace drop-in aktualisiert"
}

if [ "$(id -u)" -ne 0 ]; then
  err "Dieses Skript muss mit sudo ausgeführt werden: sudo $0 [QUELLVERZEICHNIS]"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
DEFAULT_SOURCE="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_DIR="${1:-$DEFAULT_SOURCE}"
INSTALL_DIR="/opt/setuphelfer"
CONFIG_DIR="/etc/setuphelfer"
LOG_DIR="/var/log/setuphelfer"
STATE_DIR="/var/lib/setuphelfer"
SYSTEMD_DIR="/etc/systemd/system"
SERVICE_USER_NAME="setuphelfer"

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

# Service-User und Gruppe anlegen
if ! getent passwd "$SERVICE_USER_NAME" >/dev/null 2>&1; then
  info "Lege Service-User an: $SERVICE_USER_NAME"
  # Gruppe mit gleichem Namen anlegen, falls nicht vorhanden
  if ! getent group "$SERVICE_USER_NAME" >/dev/null 2>&1; then
    groupadd --system "$SERVICE_USER_NAME" 2>/dev/null || true
  fi
  useradd --system --no-create-home --comment "Setuphelfer Service" --gid "$SERVICE_USER_NAME" "$SERVICE_USER_NAME" 2>/dev/null || \
  useradd --system --no-create-home --comment "Setuphelfer Service" "$SERVICE_USER_NAME" 2>/dev/null || true
  ok "User $SERVICE_USER_NAME erstellt"
else
  ok "Service-User $SERVICE_USER_NAME existiert bereits"
fi

# Tatsächliche Gruppe ermitteln (könnte nogroup sein)
SERVICE_GROUP=$(id -gn "$SERVICE_USER_NAME" 2>/dev/null || echo "$SERVICE_USER_NAME")

# Verzeichnisse (STATE_DIR vor chown anlegen – sonst schlägt chown fehl / Service ohne Pfad)
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$STATE_DIR"

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
find "$INSTALL_DIR/scripts" -maxdepth 1 -type f -name "serve-frontend-production.py" -exec chmod +x {} \; 2>/dev/null || true
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
  info "Frontend Produktions-Build (dist/)..."
  if npm run build 2>&1; then
    ok "frontend/dist erzeugt (vite build)"
  else
    warn "vite build fehlgeschlagen – ohne frontend/dist/index.html startet setuphelfer.service nicht (Exit 1)."
  fi
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
safe_chown_tree "$INSTALL_DIR"
safe_chown_tree "$CONFIG_DIR"
safe_chown_tree "$LOG_DIR"
safe_chown_tree "$STATE_DIR"

# Alte Units stilllegen (Migration)
for old in pi-installer.service pi-installer-backend.service; do
  systemctl stop "$old" 2>/dev/null || true
  systemctl disable "$old" 2>/dev/null || true
done

# systemd: Backend (Owner :8000) + Web-UI aus Repo-Vorlagen
info "Systemd-Services aus Vorlagen schreiben (Backend + Web-UI)..."
# Platzhalter {{PI_INSTALLER_*}} in Unit-Vorlagen = technische Ersetzung (gleiche Werte wie SETUPHELFER_*)
SED_ENV=( -e "s|{{INSTALL_DIR}}|$INSTALL_DIR|g" -e "s|{{USER}}|$SERVICE_USER_NAME|g"
  -e "s|{{PI_INSTALLER_CONFIG_DIR}}|$CONFIG_DIR|g" -e "s|{{PI_INSTALLER_LOG_DIR}}|$LOG_DIR|g"
  -e "s|{{PI_INSTALLER_STATE_DIR}}|$STATE_DIR|g" )
if [ -w "$SYSTEMD_DIR" ]; then
  sed "${SED_ENV[@]}" "$INSTALL_DIR/setuphelfer-backend.service" > "$SYSTEMD_DIR/setuphelfer-backend.service"
  sed -i "s/^Group=.*/Group=$SERVICE_GROUP/" "$SYSTEMD_DIR/setuphelfer-backend.service" 2>/dev/null || true
  sed "${SED_ENV[@]}" "$INSTALL_DIR/setuphelfer.service" > "$SYSTEMD_DIR/setuphelfer.service"
  sed -i "s/^Group=.*/Group=$SERVICE_GROUP/" "$SYSTEMD_DIR/setuphelfer.service" 2>/dev/null || true
  ok "systemd: setuphelfer-backend.service + setuphelfer.service"
  write_backend_workspace_dropin "$SOURCE_DIR"
else
  warn "systemd-Unit-Dateien werden in diesem Kontext nicht neu geschrieben; vorhandene Units werden nur neu geladen/restarted."
fi

# AUDIT-FIX (A-03): Runtime liest config.json; erzeuge config.json statt config.yaml.
# Konfiguration (nur anlegen wenn nicht vorhanden)
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
  chown "$SERVICE_USER_NAME:$SERVICE_USER_NAME" "$CONFIG_DIR/config.json"
  ok "Konfiguration erstellt"
fi

# Services: zuerst Backend (Port 8000), dann Web-UI
systemctl daemon-reload
systemctl enable setuphelfer-backend.service 2>/dev/null || true
systemctl enable setuphelfer.service 2>/dev/null || true
if systemctl is-active --quiet setuphelfer-backend.service 2>/dev/null; then
  info "Starte setuphelfer-backend neu..."
  systemctl restart setuphelfer-backend.service
else
  info "Starte setuphelfer-backend..."
  systemctl start setuphelfer-backend.service
fi
if systemctl is-active --quiet setuphelfer.service 2>/dev/null; then
  info "Starte setuphelfer (Web-UI) neu..."
  systemctl restart setuphelfer.service
else
  info "Starte setuphelfer (Web-UI)..."
  systemctl start setuphelfer.service
fi
ok "Services gestartet (setuphelfer-backend, setuphelfer)"
wait_for_backend_api || exit 1

# Startmenü-Einträge (Anwendungen)
if [ -f "$INSTALL_DIR/scripts/install-desktop-entries.sh" ]; then
  info "Startmenü-Einträge anlegen..."
  if bash "$INSTALL_DIR/scripts/install-desktop-entries.sh" "$INSTALL_DIR"; then
    ok "SetupHelfer erscheint im Startmenü"
  else
    warn "Startmenü-Einträge konnten in diesem Kontext nicht aktualisiert werden."
  fi
fi

echo ""
ok "Deploy abgeschlossen. Setuphelfer läuft unter $INSTALL_DIR als User $SERVICE_USER_NAME."
echo ""
