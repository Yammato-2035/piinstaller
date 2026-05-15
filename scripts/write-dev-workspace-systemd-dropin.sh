#!/usr/bin/env bash
# Legt systemd-Drop-in an: SETUPHELFER_DEV_WORKSPACE_ROOT + ReadOnlyPaths fuer Deploy-Drift
# unter ProtectHome=yes. Benoetigt sudo.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ROOT="${SETUPHELFER_DIR:-/opt/setuphelfer}"
ENV_FILE="${SETUPHELFER_RUNTIME_ENV:-$RUNTIME_ROOT/.env}"
DROPIN_DIR="/etc/systemd/system/setuphelfer-backend.service.d"
DROPIN_FILE="$DROPIN_DIR/dev-workspace.conf"
SERVICE="${SETUPHELFER_BACKEND_SERVICE:-setuphelfer-backend.service}"

read_ws_from_env_file() {
  local f="$1"
  [[ -f "$f" ]] || return 1
  local line key val
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%%#*}"
    line="$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -n "$line" && "$line" == *"="* ]] || continue
    key="${line%%=*}"
    val="${line#*=}"
    key="$(echo "$key" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    val="$(echo "$val" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")"
    if [[ "$key" == "SETUPHELFER_DEV_WORKSPACE_ROOT" && -n "$val" ]]; then
      printf '%s' "$val"
      return 0
    fi
  done <"$f"
  return 1
}

WS_ROOT="${SETUPHELFER_DEV_WORKSPACE_ROOT:-}"
if [[ -z "$WS_ROOT" ]]; then
  WS_ROOT="$(read_ws_from_env_file "$ENV_FILE" || true)"
fi
if [[ -z "$WS_ROOT" ]]; then
  echo "write-dev-workspace-systemd-dropin: SETUPHELFER_DEV_WORKSPACE_ROOT nicht in $ENV_FILE" >&2
  exit 1
fi
if [[ ! "$WS_ROOT" = /* ]]; then
  echo "write-dev-workspace-systemd-dropin: Workspace muss absoluter Pfad sein: $WS_ROOT" >&2
  exit 1
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
cat >"$TMP" <<EOF
# Auto: scripts/write-dev-workspace-systemd-dropin.sh — Deploy-Drift / Phase-0-Gate
[Service]
Environment="SETUPHELFER_DEV_WORKSPACE_ROOT=$WS_ROOT"
ReadOnlyPaths=$WS_ROOT
# Checkout-Dateien sind oft Gruppe workspace (664) — ohne diese Gruppe bleibt deploy_drift gelb.
SupplementaryGroups=setuphelfer workspace
EOF

echo "Drop-in: $DROPIN_FILE"
echo "  SETUPHELFER_DEV_WORKSPACE_ROOT=$WS_ROOT"
echo "  ReadOnlyPaths + SupplementaryGroups=setuphelfer workspace"
sudo mkdir -p "$DROPIN_DIR"
sudo cp "$TMP" "$DROPIN_FILE"
sudo systemctl daemon-reload
if systemctl is-active --quiet "$SERVICE" 2>/dev/null; then
  sudo systemctl restart "$SERVICE"
  echo "Dienst $SERVICE neu gestartet."
else
  echo "Hinweis: $SERVICE war nicht aktiv — nach Start greift das Drop-in."
fi
