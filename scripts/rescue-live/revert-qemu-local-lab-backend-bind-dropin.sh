#!/usr/bin/env bash
# Revert lab-only backend bind drop-in (Option A).
set -euo pipefail

DROPIN_FILE="/etc/systemd/system/setuphelfer-backend.service.d/95-qemu-local-lab-bind.conf"
SERVICE="setuphelfer-backend.service"
CONFIRM=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --operator-confirm) CONFIRM=true; shift ;;
    *) echo "Usage: $0 --operator-confirm" >&2; exit 2 ;;
  esac
done

[[ "$CONFIRM" == true ]] || { echo "DRY-RUN: pass --operator-confirm"; exit 20; }
[[ "$(id -u)" -ne 0 ]] && { echo "root required" >&2; exit 1; }

rm -f "$DROPIN_FILE"
systemctl daemon-reload
systemctl restart "$SERVICE"
echo "OK: reverted lab bind; $SERVICE restarted"
ss -ltnp | grep ':8000' || true
