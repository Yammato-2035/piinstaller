#!/bin/bash
# Setuphelfer – Deploy aus aktuellem Repo nach /opt/setuphelfer
# Legt Service-User setuphelfer an, kopiert Dateien, richtet Venv/Frontend ein, startet setuphelfer-backend + setuphelfer.
# Kann vom Backend (Deploy-Aktion) per sudo aufgerufen werden oder manuell.
#
# Verwendung:
#   sudo ./scripts/deploy-to-opt.sh [--profile runtime-opt] [QUELLVERZEICHNIS]
#   ./scripts/deploy-to-opt.sh --profile runtime-opt --plan
#   sudo ./scripts/deploy-to-opt.sh --profile runtime-opt --with-tauri
#   sudo ./scripts/deploy-to-opt.sh --skip-tauri
# Profile: runtime-opt (Default, ohne Tauri), desktop-development, desktop-release,
#          rescue-payload, package-release
# Legacy: SETUPHELFER_SKIP_TAURI_BUILD=1 erzwingt Tauri-Skip.

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

run_deploy_runtime_verify() {
  local phase="$1"
  local verify_py="$SOURCE_DIR/backend/tools/verify_deploy_to_opt.py"
  local py="python3"
  if [ -x "$SOURCE_DIR/backend/venv/bin/python3" ]; then
    py="$SOURCE_DIR/backend/venv/bin/python3"
  elif [ -x "$INSTALL_DIR/backend/venv/bin/python3" ]; then
    py="$INSTALL_DIR/backend/venv/bin/python3"
  fi
  if [ ! -f "$verify_py" ]; then
    warn "Deploy-Verifikation übersprungen (verify_deploy_to_opt.py fehlt in Quelle)."
    return 0
  fi
  info "Deploy-Verifikation ($phase): kritische Backend-Dateien und Routen…"
  if "$py" "$verify_py" --workspace "$SOURCE_DIR" --runtime "$INSTALL_DIR" --phase "$phase" --base-url "http://127.0.0.1:8000"; then
    ok "Deploy-Verifikation ($phase) bestanden"
    return 0
  fi
  err "Deploy-Verifikation ($phase) fehlgeschlagen — neue Backend-Module oder OpenAPI-Routen fehlen in /opt."
  err "Prüfe Quelle: $SOURCE_DIR (git HEAD, uncommitted Dateien) und journalctl -u setuphelfer-backend.service"
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
DEFAULT_SOURCE="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_DIR="/opt/setuphelfer"
CONFIG_DIR="/etc/setuphelfer"
LOG_DIR="/var/log/setuphelfer"
STATE_DIR="/var/lib/setuphelfer"
SYSTEMD_DIR="/etc/systemd/system"
SERVICE_USER_NAME="setuphelfer"

DEPLOY_PROFILE="runtime-opt"
WITH_TAURI=0
PLAN_ONLY=0
SKIP_TAURI_FLAG=0
SOURCE_DIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --profile) DEPLOY_PROFILE="${2:-}"; shift 2 ;;
    --with-tauri) WITH_TAURI=1; shift ;;
    --skip-tauri) SKIP_TAURI_FLAG=1; DEPLOY_PROFILE="runtime-opt"; shift ;;
    --plan|--dry-run|--print-plan) PLAN_ONLY=1; shift ;;
    -h|--help)
      echo "Usage: sudo $0 [--profile runtime-opt] [--with-tauri|--skip-tauri] [--plan] [SOURCE_DIR]"
      exit 0
      ;;
    -*)
      err "Unbekanntes Argument: $1"
      exit 2
      ;;
    *)
      if [ -z "$SOURCE_DIR" ]; then SOURCE_DIR="$1"; else err "Zu viele Positionsargumente"; exit 2; fi
      shift
      ;;
  esac
done
SOURCE_DIR="${SOURCE_DIR:-$DEFAULT_SOURCE}"

case "$DEPLOY_PROFILE" in
  runtime-opt|desktop-development|desktop-release|rescue-payload|package-release|runtime|opt|desktop|desktop-dev|rescue|package) ;;
  *)
    err "Unbekanntes Deploy-Profil: $DEPLOY_PROFILE"
    exit 2
    ;;
esac
case "$DEPLOY_PROFILE" in
  runtime|opt) DEPLOY_PROFILE="runtime-opt" ;;
  desktop-dev) DEPLOY_PROFILE="desktop-development" ;;
  desktop) DEPLOY_PROFILE="desktop-release" ;;
  rescue) DEPLOY_PROFILE="rescue-payload" ;;
  package) DEPLOY_PROFILE="package-release" ;;
esac

if [ "$PLAN_ONLY" = "1" ]; then
  export PYTHONPATH="${SOURCE_DIR}/backend${PYTHONPATH:+:$PYTHONPATH}"
  python3 -c "
from pathlib import Path
import json, sys
sys.path.insert(0, str(Path(r'''$SOURCE_DIR''') / 'backend'))
from core.deploy_build_profiles import build_deploy_plan
plan = build_deploy_plan(
    repo_root=Path(r'''$SOURCE_DIR'''),
    profile=r'''$DEPLOY_PROFILE''',
    target='/opt/setuphelfer',
    with_tauri=($WITH_TAURI == 1),
)
print(json.dumps(plan, indent=2, ensure_ascii=False))
"
  exit $?
fi

if [ "$(id -u)" -ne 0 ]; then
  err "Dieses Skript muss mit sudo ausgeführt werden: sudo $0 [--profile runtime-opt] [QUELLVERZEICHNIS]"
  exit 1
fi

if [ ! -f "$SOURCE_DIR/start.sh" ] || [ ! -d "$SOURCE_DIR/backend" ] || [ ! -d "$SOURCE_DIR/frontend" ]; then
  err "Kein gültiges PI-Installer-Repo unter: $SOURCE_DIR"
  exit 1
fi

DO_TAURI=0
TAURI_SKIP_REASON="not_required_for_runtime_opt"
case "$DEPLOY_PROFILE" in
  desktop-development|desktop-release|package-release) DO_TAURI=1; TAURI_SKIP_REASON="" ;;
esac
if [ "$WITH_TAURI" = "1" ]; then DO_TAURI=1; TAURI_SKIP_REASON=""; fi
if [ "$SKIP_TAURI_FLAG" = "1" ] || [ "${SETUPHELFER_SKIP_TAURI_BUILD:-0}" = "1" ]; then
  DO_TAURI=0
  TAURI_SKIP_REASON="explicit_skip_tauri"
fi

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  PI-Installer → /opt installieren/aktualisieren${NC}"
echo -e "${CYAN}============================================${NC}"
echo -e "  Quelle:  ${SOURCE_DIR}"
echo -e "  Ziel:    ${INSTALL_DIR}"
echo -e "  User:    ${SERVICE_USER_NAME}"
echo -e "  Profil:  ${DEPLOY_PROFILE}"
echo ""
info "Deployment profile: $DEPLOY_PROFILE"
info "Web frontend build: yes"
if [ "$DO_TAURI" = "1" ]; then
  info "Tauri build: yes"
else
  info "Tauri build: skipped"
  info "Tauri skip reason: $TAURI_SKIP_REASON"
fi

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
run_deploy_runtime_verify post-rsync || exit 1

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
    err "vite build fehlgeschlagen – Deploy abgebrochen (Webfrontend erforderlich)."
    exit 1
  fi
  # Tauri nur bei Desktop-/Package-Profil oder --with-tauri (DO_TAURI=1).
  if [ "${DO_TAURI:-0}" != "1" ]; then
    info "Tauri-Build übersprungen ($TAURI_SKIP_REASON) — vorhandenes Binary unter /opt bleibt erhalten."
  else
    BUILD_USER="${SUDO_USER:-}"
    if [ -n "$BUILD_USER" ] && su - "$BUILD_USER" -c "command -v cargo" >/dev/null 2>&1; then
      info "Tauri-App bauen als User $BUILD_USER (kann einige Minuten dauern)..."
      chown -R "$BUILD_USER:$BUILD_USER" "$INSTALL_DIR/frontend"
      if su - "$BUILD_USER" -c "cd $INSTALL_DIR/frontend && export GDK_BACKEND=x11 && npm run tauri:build" 2>&1; then
        ok "Tauri-Binary erstellt (App-Fenster verfügbar)"
      else
        err "Tauri-Build fehlgeschlagen (Profil erfordert Tauri)."
        exit 1
      fi
      chown -R root:root "$INSTALL_DIR/frontend"
    elif command -v cargo >/dev/null 2>&1; then
      info "Tauri-App bauen (kann einige Minuten dauern)..."
      if ( export GDK_BACKEND=x11; npm run tauri:build 2>&1 ); then
        ok "Tauri-Binary erstellt (App-Fenster verfügbar)"
      else
        err "Tauri-Build fehlgeschlagen (Profil erfordert Tauri)."
        exit 1
      fi
    else
      err "Rust/Cargo nicht verfügbar — Desktop-/Tauri-Profil kann nicht gebaut werden."
      exit 1
    fi
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
run_deploy_runtime_verify post-restart || exit 1

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
info "Erzeuge Deploy-Manifest..."
export SOURCE_DIR DEPLOY_PROFILE
TAURI_INCLUDED=0; [ "${DO_TAURI:-0}" = "1" ] && TAURI_INCLUDED=1
export TAURI_INCLUDED
export TAURI_REASON="${TAURI_SKIP_REASON:-not_required_for_runtime_opt}"
if PYTHONPATH="$SOURCE_DIR/backend${PYTHONPATH:+:$PYTHONPATH}" \
  SOURCE_DIR="$SOURCE_DIR" DEPLOY_PROFILE="$DEPLOY_PROFILE" \
  TAURI_INCLUDED="$TAURI_INCLUDED" TAURI_REASON="$TAURI_REASON" \
  python3 -c '
from pathlib import Path
import json, os, subprocess, sys
sys.path.insert(0, str(Path(os.environ["SOURCE_DIR"]) / "backend"))
from core.deploy_manifest import build_manifest_data, workspace_manifest_path
from core.profile_deploy_manifest import build_profile_manifest_data, manifest_sha256
repo = Path(os.environ["SOURCE_DIR"])
dirty = False
try:
    p = subprocess.run(["git","-C",str(repo),"status","--porcelain"], capture_output=True, text=True, timeout=3)
    dirty = bool((p.stdout or "").strip())
except Exception:
    pass
data = build_manifest_data(
    repo,
    deployment_profile=os.environ.get("DEPLOY_PROFILE","runtime-opt"),
    tauri_included=os.environ.get("TAURI_INCLUDED")=="1",
    tauri_skip_reason=os.environ.get("TAURI_REASON","not_required_for_runtime_opt"),
    dirty=dirty,
)
pm = build_profile_manifest_data("release", repo)
data["install_profile"] = "release"
data["manifest_profile"] = "release"
data["profile_manifest"] = pm
out = workspace_manifest_path(repo)
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
data["file_manifest_sha256"] = manifest_sha256(out)
data["manifest_sha256"] = data["file_manifest_sha256"]
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(out)
'; then
  MANIFEST_OUT="$SOURCE_DIR/build/deploy/setuphelfer-deploy-manifest.json"
  mkdir -p "$INSTALL_DIR/build/deploy" "$INSTALL_DIR/deploy"
  cp -a "$MANIFEST_OUT" "$INSTALL_DIR/build/deploy/setuphelfer-deploy-manifest.json"
  cp -a "$MANIFEST_OUT" "$INSTALL_DIR/deploy/setuphelfer-deploy-manifest.json"
  safe_chown_tree "$INSTALL_DIR/build/deploy" || true
  safe_chown_tree "$INSTALL_DIR/deploy" || true
  ok "Deploy-Manifest geschrieben"
else
  warn "Deploy-Manifest konnte nicht erzeugt werden"
fi

ok "Deploy abgeschlossen. Setuphelfer läuft unter $INSTALL_DIR als User $SERVICE_USER_NAME."
echo ""
