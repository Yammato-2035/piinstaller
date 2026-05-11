#!/usr/bin/env bash
# Setuphelfer / PI-Installer – einmalige oder wiederholbare Entwicklungsumgebung im Repo.
# Installiert Backend-Venv + Frontend node_modules, legt .env an (nur wenn fehlend).
#
# Aufruf (als Entwickler-User, z. B. gabriel):
#   ./scripts/dev-setup.sh
# Optional: Playwright-Browser (groß, langsam):
#   DEV_SETUP_PLAYWRIGHT=1 ./scripts/dev-setup.sh
#
# Siehe: .env.example, docs/BETRIEB_REPO_VS_SERVICE.md, docs/user/QUICKSTART.md

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$REPO_ROOT/backend"
FRONTEND="$REPO_ROOT/frontend"

info() { echo "[dev-setup] $*"; }
warn() { echo "[dev-setup] WARNUNG: $*" >&2; }
err() { echo "[dev-setup] FEHLER: $*" >&2; exit 1; }

cd "$REPO_ROOT"

command -v python3 >/dev/null 2>&1 || err "python3 fehlt (z. B. sudo apt install python3 python3-venv)"
command -v node >/dev/null 2>&1 || err "node fehlt (z. B. Node 18+ LTS)"
command -v npm >/dev/null 2>&1 || err "npm fehlt"
command -v curl >/dev/null 2>&1 || err "curl fehlt (z. B. sudo apt install curl)"

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null || err "Python 3.9+ erforderlich (python3 --version)"

node -e 'const m=+process.version.slice(1).split(".")[0]; process.exit(m>=18?0:1)' 2>/dev/null || err "Node.js 18+ erforderlich (node --version)"

if [ ! -f "$REPO_ROOT/.env.example" ]; then
  err ".env.example fehlt im Repo-Root."
fi

if [ ! -f "$REPO_ROOT/.env" ]; then
  info "Lege .env an (Kopie von .env.example + Dev-Ergänzungen)…"
  cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
  {
    echo ""
    echo "# --- von scripts/dev-setup.sh ergänzt: lokale Entwicklung ---"
    echo "APP_EDITION=repo"
    echo "PI_INSTALLER_DEV=1"
    echo "# Parallel zu systemd (setuphelfer-backend auf :8000): anderen Port + Konflikt-Guard aus"
    echo "# PI_INSTALLER_BACKEND_PORT=8010"
    echo "# PI_INSTALLER_SKIP_SERVICE_CONFLICT_GUARD=1"
    echo "# SETUPHELFER_SKIP_SERVICE_CONFLICT_GUARD=1"
    echo "# Dann im Frontend ggf. frontend/.env.development mit VITE_PROXY_TARGET=http://127.0.0.1:8010"
  } >> "$REPO_ROOT/.env"
else
  info ".env existiert bereits – nicht überschrieben (APP_EDITION / PI_INSTALLER_DEV prüfen)."
fi

if [ ! -f "$FRONTEND/.env.development" ] && [ -f "$FRONTEND/.env.development.example" ]; then
  info "Lege frontend/.env.development aus .env.development.example an…"
  cp "$FRONTEND/.env.development.example" "$FRONTEND/.env.development"
elif [ -f "$FRONTEND/.env.development" ]; then
  info "frontend/.env.development existiert bereits."
fi

PYTHON="$BACKEND/venv/bin/python3"
_need_new_venv=0
if [ ! -d "$BACKEND/venv" ] || [ ! -e "$BACKEND/venv/bin/python3" ]; then
  _need_new_venv=1
elif ! "$PYTHON" -c "import sys" 2>/dev/null; then
  _need_new_venv=1
fi
if [ "$_need_new_venv" = "1" ]; then
  info "Erstelle backend/venv …"
  rm -rf "$BACKEND/venv"
  python3 -m venv "$BACKEND/venv"
  PYTHON="$BACKEND/venv/bin/python3"
fi

info "pip: requirements.txt …"
"$PYTHON" -m pip install -q --upgrade pip
if ! "$PYTHON" -m pip install -q -r "$BACKEND/requirements.txt" --only-binary :all: 2>/dev/null; then
  "$PYTHON" -m pip install -q -r "$BACKEND/requirements.txt"
fi

REQ_HASH="$("$PYTHON" -c "import hashlib, pathlib; b=pathlib.Path(r'''$BACKEND/requirements.txt''').read_bytes(); print(hashlib.sha256(b).hexdigest())")"
echo "$REQ_HASH" > "$BACKEND/venv/.pi-installer-req.sha256"

if [ ! -f "$FRONTEND/package-lock.json" ]; then
  err "frontend/package-lock.json fehlt – npm ci nicht möglich."
fi
info "npm ci (frontend) …"
(cd "$FRONTEND" && npm ci)

if [ "${DEV_SETUP_PLAYWRIGHT:-0}" = "1" ]; then
  info "Playwright: Browser installieren (DEV_SETUP_PLAYWRIGHT=1) …"
  (cd "$FRONTEND" && npx playwright install --with-deps chromium)
else
  info "Playwright übersprungen. Bei Bedarf: DEV_SETUP_PLAYWRIGHT=1 $0"
fi

if command -v rustc >/dev/null 2>&1; then
  info "Rust: $(rustc --version)"
else
  warn "Rust nicht im PATH – Tauri lokal: https://rustup.rs/ (oder nur Browser-UI mit ./start.sh)"
fi

info "Smoke: Python import fastapi …"
"$PYTHON" -c "import fastapi; import uvicorn"

info "Fertig."
echo ""
echo "Umgebungsvariablen: siehe $REPO_ROOT/.env.example und $REPO_ROOT/.env"
echo "Parallel zu systemd: siehe Kommentare in .env (Port + *_SKIP_SERVICE_CONFLICT_GUARD)."
echo "Start:  ./start.sh   oder   ./scripts/start-backend.sh  und  cd frontend && npm run dev"
echo ""
