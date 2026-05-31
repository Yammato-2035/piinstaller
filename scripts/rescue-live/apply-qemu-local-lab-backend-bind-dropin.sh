#!/usr/bin/env bash
# Apply lab-only backend bind for QEMU (Option A). Requires operator confirm + root.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EXAMPLE="${REPO_ROOT}/packaging/systemd/dropins/qemu-local-lab-bind.conf.example"
DROPIN_DIR="/etc/systemd/system/setuphelfer-backend.service.d"
DROPIN_FILE="${DROPIN_DIR}/95-qemu-local-lab-bind.conf"
SERVICE="setuphelfer-backend.service"
CONFIRM=false

usage() {
  cat <<EOF
Usage: $0 [--dry-run] [--operator-confirm]

Applies lab-only ALLOW_REMOTE_ACCESS=true drop-in for QEMU host ingest.
Public uploads and SSH are NOT changed by this script.

Revert: scripts/rescue-live/revert-qemu-local-lab-backend-bind-dropin.sh
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) shift ;;
    --operator-confirm) CONFIRM=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown: $1" >&2; exit 2 ;;
  esac
done

[[ -f "$EXAMPLE" ]] || { echo "Missing example: $EXAMPLE" >&2; exit 1; }

echo "=== QEMU Lab Backend Bind (Option A) ==="
echo "Drop-in: $DROPIN_FILE"
echo "Effect: ALLOW_REMOTE_ACCESS=true → bind 0.0.0.0:8000 via start-backend.sh"
echo "Scope: LAB ONLY — document in evidence"

if [[ "$CONFIRM" != true ]]; then
  echo "DRY-RUN: pass --operator-confirm to apply (not applied)."
  exit 20
fi

if [[ "$(id -u)" -ne 0 ]]; then
  echo "ERROR: root required" >&2
  exit 1
fi

mkdir -p "$DROPIN_DIR"
install -m 0644 "$EXAMPLE" "$DROPIN_FILE"
systemctl daemon-reload
systemctl restart "$SERVICE"
echo "OK: applied and restarted $SERVICE"
ss -ltnp | grep ':8000' || true
