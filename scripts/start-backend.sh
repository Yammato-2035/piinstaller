#!/bin/bash
# PI-Installer Backend Startskript
# Startet Backend auf http://localhost:8000 (nutzt immer die Venv im backend/, nie System-Python)
# Siehe: docs/START_APPS.md, docs/user/QUICKSTART.md (Venv nach git pull)
# Venv-Sync: Wenn sich backend/requirements.txt ändert, wird pip install -r … automatisch ausgeführt
# (Stamp: venv/.pi-installer-req.sha256). Überspringen: PI_INSTALLER_SKIP_VENV_SYNC=1

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
cd "$BACKEND_DIR"

# Optionale .env aus Repo-Root (z. B. APP_EDITION=repo für Entwicklung)
if [ -f "$REPO_ROOT/.env" ]; then
  set -a
  . "$REPO_ROOT/.env"
  set +a
fi

echo "🚀 Starte PI-Installer Backend..."
echo "📁 Arbeitsverzeichnis: $BACKEND_DIR"

PYTHON="$BACKEND_DIR/venv/bin/python3"

# Venv anlegen oder neu anlegen, wenn der Interpreter ungültig ist (typisch: Repo kopiert/verschoben —
# venv/bin/* zeigt noch auf den alten absoluten Pfad).
_need_new_venv=0
if [ ! -d "venv" ] || [ ! -e "venv/bin/python3" ]; then
    _need_new_venv=1
elif ! "$PYTHON" -c "import sys" 2>/dev/null; then
    _need_new_venv=1
fi
if [ "$_need_new_venv" = "1" ]; then
    if [ -d "venv" ]; then
        echo "📦 Virtuelle Umgebung ungültig (z. B. nach Verschieben/Kopieren des Projekts) – erstelle neu…"
        rm -rf venv
    else
        echo "📦 Erstelle Virtual Environment…"
    fi
    python3 -m venv venv
    PYTHON="$BACKEND_DIR/venv/bin/python3"
fi
# Hash der requirements.txt – bei Änderung (z. B. nach git pull) Venv synchronisieren
VENV_REQ_STAMP="$BACKEND_DIR/venv/.pi-installer-req.sha256"

_req_hash() {
    "$PYTHON" -c "import hashlib;print(hashlib.sha256(open('requirements.txt','rb').read()).hexdigest())" 2>/dev/null
}

# Dependencies in der Venv installieren (niemals system-weit – PEP 668).
# Wichtig: Nach Updates von FastAPI/Starlette muss die Venv zu requirements.txt passen (CI/Security).
# Mit PI_INSTALLER_SKIP_VENV_SYNC=1 nur den manuellen Pfad (pip install -r …) nutzen.
REQ_HASH=""
if [ -f "requirements.txt" ]; then
    REQ_HASH="$(_req_hash)"
fi
NEED_INSTALL=0
if ! "$PYTHON" -c "import fastapi" 2>/dev/null; then
    NEED_INSTALL=1
elif [ -z "${PI_INSTALLER_SKIP_VENV_SYNC:-}" ] && [ -n "$REQ_HASH" ]; then
    if [ ! -f "$VENV_REQ_STAMP" ] || [ "$(cat "$VENV_REQ_STAMP" 2>/dev/null)" != "$REQ_HASH" ]; then
        NEED_INSTALL=1
    fi
fi
if [ "$NEED_INSTALL" = "1" ]; then
    echo "📦 Installiere/aktualisiere Dependencies in der Venv (requirements.txt)…"
    # python -m pip: funktioniert auch wenn venv/bin/pip einen veralteten Shebang hat
    "$PYTHON" -m pip install --upgrade pip
    "$PYTHON" -m pip install -r requirements.txt --only-binary :all: 2>/dev/null || "$PYTHON" -m pip install -r requirements.txt
    if [ -n "$REQ_HASH" ]; then
        echo "$REQ_HASH" > "$VENV_REQ_STAMP"
    fi
fi

# Port: Standard 8000, überschreibbar mit PI_INSTALLER_BACKEND_PORT (z. B. wenn 8000 belegt)
PORT="${PI_INSTALLER_BACKEND_PORT:-8000}"

# Nur TCP-LISTEN prüfen (Browser/WebKit mit ESTABLISHED → :8000 sind Clients, blockieren den Port nicht)
_tcp_port_listen_busy() {
  local p="$1"
  if command -v ss >/dev/null 2>&1; then
    if ss -tln 2>/dev/null | grep -qE ":${p}([[:space:]]|$)"; then
      return 0
    fi
  fi
  if command -v lsof >/dev/null 2>&1; then
    if lsof -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then
      return 0
    fi
  fi
  return 1
}

if _tcp_port_listen_busy "$PORT"; then
  echo "⚠️  Port $PORT wird bereits für TCP (LISTEN) verwendet – meist läuft schon ein Backend (uvicorn) oder ein anderer Dienst."
  echo "   Hinweis: lsof -i :$PORT zeigt oft auch Browser-Verbindungen (ESTABLISHED); entscheidend ist nur LISTEN."
  echo ""
  if command -v ss >/dev/null 2>&1; then
    echo "   ss (Listener):"
    ss -tlnp 2>/dev/null | grep -E ":${PORT}([[:space:]]|$)" | sed 's/^/   /' || true
  fi
  if command -v lsof >/dev/null 2>&1; then
    echo "   lsof nur LISTEN:"
    lsof -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | sed 's/^/   /' || true
  fi
  echo ""
  echo "   Optionen:"
  echo "   - Listener beenden, z. B.: kill \$(lsof -t -iTCP:$PORT -sTCP:LISTEN)  (PID prüfen!)"
  echo "   - Oder anderen Port: PI_INSTALLER_BACKEND_PORT=8001 $REPO_ROOT/scripts/start-backend.sh"
  echo "   - In der App ggf. Backend-URL auf http://127.0.0.1:8001 setzen."
  echo ""
  exit 1
fi

# Backend starten – immer mit Venv-Python, genau ein Worker (wichtig für Sudo-Passwort-Speicherung)
# Standard: nur localhost (127.0.0.1). LAN-Zugriff nur wenn ALLOW_REMOTE_ACCESS=true gesetzt.
BIND_HOST="${ALLOW_REMOTE_ACCESS:-false}"
if [ "$BIND_HOST" = "true" ] || [ "$BIND_HOST" = "1" ]; then
  BIND_HOST="0.0.0.0"
  echo "✅ Starte Backend auf http://0.0.0.0:$PORT (LAN-Zugriff aktiv)"
else
  BIND_HOST="127.0.0.1"
  echo "✅ Starte Backend auf http://127.0.0.1:$PORT (nur localhost)"
fi
echo "📝 API Docs: http://127.0.0.1:$PORT/docs"
echo ""
RELOAD_ARGS=""
if [ "$PI_INSTALLER_DEV" = "1" ]; then
  RELOAD_ARGS="--reload --timeout-keep-alive 1"
fi
exec "$PYTHON" -m uvicorn app:app --host "$BIND_HOST" --port "$PORT" --workers 1 $RELOAD_ARGS
