#!/usr/bin/env bash
# Verify rescue background services do not bind/write TTY (001D7).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${REPO_ROOT}/scripts/rescue-live/image/systemd"
FAIL=0

check_unit() {
  local unit="$1"
  local path="${IMAGE}/${unit}"
  [[ -f "$path" ]] || return 0
  if ! grep -q 'StandardInput=null' "$path"; then
    echo "FAIL: ${unit} missing StandardInput=null"
    FAIL=1
  fi
  if ! grep -q 'StandardOutput=journal' "$path"; then
    echo "FAIL: ${unit} missing StandardOutput=journal"
    FAIL=1
  fi
  if ! grep -q 'TTYPath=' "$path"; then
    echo "FAIL: ${unit} missing TTYPath="
    FAIL=1
  fi
}

for unit in \
  setuphelfer-rescue-auto-msi-evidence.service \
  setuphelfer-rescue-auto-physical-e2e.service \
  setuphelfer-rescue-auto-discovery.service \
  setuphelfer-rescue-lab-auto-shutdown-failsafe.service \
  setuphelfer-rescue-lab-auto-shutdown-watchdog.service; do
  check_unit "$unit"
done

tui="${IMAGE}/setuphelfer-rescue-tui.service"
if [[ -f "$tui" ]] && ! grep -q 'TTYPath=/dev/tty1' "$tui"; then
  echo "FAIL: tui service must own tty1"
  FAIL=1
fi

if [[ "$FAIL" -eq 0 ]]; then
  echo "exclusive_tty_owner=setuphelfer-rescue-tui.service"
  echo "background_tty_writers=0"
  exit 0
fi
exit 1
