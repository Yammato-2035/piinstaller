#!/bin/bash
# Optional graphical Rescue GUI — only when explicitly requested (RS-P2C).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh"

GUI_STATUS="${SETUPHELFER_RESCUE_STATE_DIR}/gui-autostart.json"
HTML="/usr/share/setuphelfer/rescue/ui/rescue.html"
KIOSK="/usr/local/sbin/setuphelfer-rescue-kiosk-start"

write_gui_status() {
  local status="$1" reason="$2" mode="${3:-}"
  setuphelfer_rescue_write_json "$GUI_STATUS" <<EOF
{
  "schema_version": 1,
  "gui_enabled_by_default": false,
  "status": "$status",
  "reason": "$reason",
  "display_mode": "$mode",
  "text_fallback_only_on_failure": true,
  "execute_allowed": false,
  "secrets_exposed": false
}
EOF
  setuphelfer_rescue_mirror_evidence_file "$GUI_STATUS" "setuphelfer/evidence/boot/gui-autostart.json" 2>/dev/null || true
}

if ! setuphelfer_rescue_should_start_gui; then
  write_gui_status "skipped" "text_mode_default" "text"
  exit 5
fi

if [[ ! -f "$HTML" ]]; then
  write_gui_status "failed" "frontend_missing" "text_fallback"
  exit 2
fi

if ! "${SCRIPT_DIR}/setuphelfer-rescue-backend-start.sh"; then
  write_gui_status "failed" "backend_not_running" "text_fallback"
  exit 3
fi

if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-gui-watchdog" ]]; then
  write_gui_status "starting" "delegating_to_gui_watchdog" "graphical"
  exec "${SCRIPT_DIR}/setuphelfer-rescue-gui-watchdog"
fi

if [[ -x "$KIOSK" ]]; then
  write_gui_status "starting" "delegating_to_kiosk_start" "graphical"
  exec "$KIOSK"
fi

write_gui_status "failed" "kiosk_launcher_missing" "text_fallback"
exit 4
