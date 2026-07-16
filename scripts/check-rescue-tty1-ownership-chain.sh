#!/usr/bin/env bash
# Validate tty1 ownership chain for rescue boot (001D7D).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SYSTEMD_DIR="${REPO_ROOT}/scripts/rescue-live/image/systemd"
FAIL=0

_has() {
  local file="$1" pattern="$2"
  grep -q "$pattern" "$file"
}

boot_progress="${SYSTEMD_DIR}/setuphelfer-rescue-boot-progress.service"
tui="${SYSTEMD_DIR}/setuphelfer-rescue-tui.service"
hold="${SYSTEMD_DIR}/setuphelfer-rescue-tui-hold.service"

boot_progress_owner_valid=false
tui_owner_valid=false
hold_owner_valid=false
shutdown_owner_valid=false
bare_tty_path_possible=true

if [[ -f "$boot_progress" ]] && _has "$boot_progress" 'Environment=SETUPHELFER_BOOT_TTY=/dev/tty1'; then
  boot_progress_owner_valid=true
fi
if [[ -f "$tui" ]] && _has "$tui" 'TTYPath=/dev/tty1' && _has "$tui" 'StandardInput=tty'; then
  tui_owner_valid=true
fi
if [[ -f "$hold" ]] && _has "$hold" 'TTYPath=/dev/tty1' && _has "$hold" 'StandardInput=tty'; then
  hold_owner_valid=true
fi

shutdown_owner_valid=true

if [[ "$boot_progress_owner_valid" == true && "$tui_owner_valid" == true && "$hold_owner_valid" == true && "$shutdown_owner_valid" == true ]]; then
  bare_tty_path_possible=false
fi

echo "boot_progress_owner_valid=${boot_progress_owner_valid}"
echo "tui_owner_valid=${tui_owner_valid}"
echo "hold_owner_valid=${hold_owner_valid}"
echo "shutdown_owner_valid=${shutdown_owner_valid}"
echo "bare_tty_path_possible=${bare_tty_path_possible}"

[[ "$boot_progress_owner_valid" == true ]] || FAIL=1
[[ "$tui_owner_valid" == true ]] || FAIL=1
[[ "$hold_owner_valid" == true ]] || FAIL=1
[[ "$shutdown_owner_valid" == true ]] || FAIL=1
[[ "$bare_tty_path_possible" == false ]] || FAIL=1

exit "$FAIL"
