#!/bin/bash
# Setuphelfer — Rescue Telemetrie LAN-Proxy als systemd-Service (Port 8001, Start bei Boot).
# Aufruf: ./scripts/install-rescue-telemetry-lan-proxy-service.sh
#   oder: SETUPHELFER_DIR=/opt/setuphelfer ./scripts/install-rescue-telemetry-lan-proxy-service.sh
#
# Danach: setuphelfer-rescue-telemetry-lan-proxy.service
# Status: sudo systemctl status setuphelfer-rescue-telemetry-lan-proxy

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$REPO_ROOT/scripts/rescue-live/rescue_telemetry_lan_proxy.py" ]; then
  INSTALL_DIR="${SETUPHELFER_DIR:-${PI_INSTALLER_DIR:-$REPO_ROOT}}"
else
  INSTALL_DIR="${SETUPHELFER_DIR:-${PI_INSTALLER_DIR:-}}"
  if [ -z "$INSTALL_DIR" ] || [ ! -f "$INSTALL_DIR/scripts/rescue-live/rescue_telemetry_lan_proxy.py" ]; then
    echo "Fehler: Rescue-Telemetrie-Proxy nicht gefunden. SETUPHELFER_DIR setzen oder aus dem Projektordner starten." >&2
    exit 1
  fi
fi

CURRENT_USER="${SUDO_USER:-$USER}"
[ -z "$CURRENT_USER" ] && CURRENT_USER="$(whoami)"

if [ "$INSTALL_DIR" = "/opt/setuphelfer" ] && getent passwd setuphelfer >/dev/null 2>&1; then
  CURRENT_USER="setuphelfer"
fi

SERVICE_NAME="setuphelfer-rescue-telemetry-lan-proxy"
SERVICE_TEMPLATE="$REPO_ROOT/setuphelfer-rescue-telemetry-lan-proxy.service"
SYSTEMD_DIR="/etc/systemd/system"
ENV_DST="/etc/setuphelfer/rescue-telemetry-lan-proxy.env"
ENV_EXAMPLE="$REPO_ROOT/packaging/systemd/setuphelfer-rescue-telemetry-lan-proxy.env.example"

if [ ! -f "$SERVICE_TEMPLATE" ]; then
  echo "Fehler: Service-Vorlage fehlt: $SERVICE_TEMPLATE" >&2
  exit 1
fi

if ! systemctl is-active --quiet setuphelfer-backend.service 2>/dev/null; then
  echo "WARN: setuphelfer-backend.service ist nicht aktiv — Proxy startet erst wenn Backend health ok ist." >&2
fi

echo "Rescue-Telemetrie-LAN-Proxy als systemd-Service einrichten..."
echo "  Installationsverzeichnis: $INSTALL_DIR"
echo "  Benutzer: $CURRENT_USER"
echo ""

sudo mkdir -p /etc/setuphelfer "$(dirname "$INSTALL_DIR/docs/evidence/runtime-results/rescue")" 2>/dev/null || true

if [ ! -f "$ENV_DST" ] && [ -f "$ENV_EXAMPLE" ]; then
  sudo cp "$ENV_EXAMPLE" "$ENV_DST"
  echo "  Env-Datei angelegt: $ENV_DST"
fi

# Pin LAN bind IP at install time — auto-detect fails under the setuphelfer
# systemd sandbox (hostname/ip subprocess restrictions).
_DETECTED_BIND=""
if command -v python3 >/dev/null 2>&1; then
  _DETECTED_BIND="$(PYTHONPATH="${REPO_ROOT}/backend:${REPO_ROOT}" python3 - <<'PY' 2>/dev/null || true
from core.rescue_telemetry_lan_proxy import detect_lan_ip
print(detect_lan_ip() or "")
PY
)"
fi
if [ -z "$_DETECTED_BIND" ]; then
  _DETECTED_BIND="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}' || true)"
fi
if [ -n "$_DETECTED_BIND" ] && ! sudo grep -q '^SETUPHELFER_RESCUE_TELEMETRY_BIND=' "$ENV_DST" 2>/dev/null; then
  echo "SETUPHELFER_RESCUE_TELEMETRY_BIND=${_DETECTED_BIND}" | sudo tee -a "$ENV_DST" >/dev/null
  echo "  LAN-Bind gesetzt: SETUPHELFER_RESCUE_TELEMETRY_BIND=${_DETECTED_BIND}"
elif sudo grep -q '^SETUPHELFER_RESCUE_TELEMETRY_BIND=' "$ENV_DST" 2>/dev/null; then
  echo "  LAN-Bind bereits in $ENV_DST (unverändert)"
else
  echo "WARN: LAN-IP nicht erkannt — bitte SETUPHELFER_RESCUE_TELEMETRY_BIND in $ENV_DST setzen." >&2
fi

TMP_UNIT="$(mktemp)"
trap 'rm -f "$TMP_UNIT"' EXIT
sed -e "s|{{INSTALL_DIR}}|$INSTALL_DIR|g" -e "s|{{USER}}|$CURRENT_USER|g" \
  "$SERVICE_TEMPLATE" > "$TMP_UNIT"
if grep -q '{{' "$TMP_UNIT"; then
  echo "FEHLER: Service-Vorlage enthält unersetzte Platzhalter — Abbruch." >&2
  grep '{{' "$TMP_UNIT" >&2 || true
  exit 1
fi
sudo cp "$TMP_UNIT" "$SYSTEMD_DIR/${SERVICE_NAME}.service"

# Stop legacy nohup instance if still running (port conflict).
if [ -x "$INSTALL_DIR/scripts/rescue-live/stop-rescue-telemetry-lan-proxy.sh" ]; then
  "$INSTALL_DIR/scripts/rescue-live/stop-rescue-telemetry-lan-proxy.sh" || true
fi

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

sleep 1
if systemctl is-active --quiet "$SERVICE_NAME"; then
  echo "OK: ${SERVICE_NAME} aktiv."
  if [ -x "$INSTALL_DIR/scripts/rescue-live/status-rescue-telemetry-lan-proxy.sh" ]; then
    "$INSTALL_DIR/scripts/rescue-live/status-rescue-telemetry-lan-proxy.sh" | python3 -c \
      'import json,sys; d=json.load(sys.stdin); print("  health_url:", d.get("health_url")); print("  lan_health_ok:", d.get("lan_health_ok"))'
  fi
  echo "  Status: sudo systemctl status $SERVICE_NAME"
  echo "  Logs:   sudo journalctl -u $SERVICE_NAME -f"
else
  echo "FEHLER: Service nicht aktiv. Log:" >&2
  sudo journalctl -u "$SERVICE_NAME" -n 40 --no-pager >&2 || true
  exit 1
fi
