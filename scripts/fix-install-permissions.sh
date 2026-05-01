#!/bin/bash
# Repariert Berechtigungen und richtet Backend/Frontend ein (nach fehlerhafter Installation)
# Aufruf: sudo ./scripts/fix-install-permissions.sh

set -e

if [ "$(id -u)" -ne 0 ]; then
  echo "Dieses Skript muss mit sudo ausgeführt werden." >&2
  exit 1
fi

INSTALL_DIR="/opt/setuphelfer"
SERVICE_USER="setuphelfer"
SERVICE_GROUP=$(id -gn "$SERVICE_USER" 2>/dev/null || echo "$SERVICE_USER")

echo "Repariere Installation unter $INSTALL_DIR..."
echo "User: $SERVICE_USER, Gruppe: $SERVICE_GROUP"
echo ""

# Alles temporär auf root setzen
chown -R root:root "$INSTALL_DIR" 2>/dev/null || true

# Backend-Venv
if [ -d "$INSTALL_DIR/backend" ] && [ ! -d "$INSTALL_DIR/backend/venv" ]; then
  echo "Backend-Venv erstellen..."
  cd "$INSTALL_DIR/backend"
  PYTHON=$(command -v python3.12 python3.11 python3.10 python3.9 python3 2>/dev/null | head -1)
  if [ -n "$PYTHON" ]; then
    mkdir -p "$INSTALL_DIR/.pip-cache"
    "$PYTHON" -m venv venv
    export PIP_CACHE_DIR="$INSTALL_DIR/.pip-cache"
    ./venv/bin/pip install --upgrade pip -q 2>/dev/null || true
    ./venv/bin/pip install -q -r requirements.txt 2>&1 | grep -v "already satisfied" || true
  fi
fi

# Frontend npm
if [ -d "$INSTALL_DIR/frontend" ] && [ ! -d "$INSTALL_DIR/frontend/node_modules" ]; then
  echo "Frontend npm install..."
  cd "$INSTALL_DIR/frontend"
  if command -v npm >/dev/null 2>&1; then
    export npm_config_cache="$INSTALL_DIR/.npm-cache"
    mkdir -p "$npm_config_cache"
    npm install --silent 2>&1 | grep -v "npm WARN" || true
  fi
fi

# Alles an setuphelfer übergeben
chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR" \
  /etc/setuphelfer /var/log/setuphelfer /var/lib/setuphelfer 2>/dev/null || true

echo ""
echo "Fertig. Service neu starten: sudo systemctl restart setuphelfer-backend.service"
