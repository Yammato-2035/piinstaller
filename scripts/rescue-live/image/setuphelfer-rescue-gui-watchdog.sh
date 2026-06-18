#!/bin/bash
# GUI start with watchdog — returns to TUI on failure (RS-P2C).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh"

TIMEOUT_SEC="${SETUPHELFER_GUI_WATCHDOG_SEC:-25}"
LOG="/run/setuphelfer/gui-start.log"
STATE="${SETUPHELFER_RESCUE_STATE_DIR}/gui-watchdog.json"
HTML="/usr/share/setuphelfer/rescue/ui/rescue.html"
KIOSK="${SCRIPT_DIR}/setuphelfer-rescue-kiosk-start"

mkdir -p /run/setuphelfer "$(dirname "$LOG")" 2>/dev/null || true

write_state() {
  local code="$1" started="${2:-false}" fallback="${3:-true}"
  setuphelfer_rescue_write_json "$STATE" <<EOF
{
  "schema_version": 1,
  "gui_started": $started,
  "gui_failed": $fallback,
  "gui_error_code": $( [[ -n "$code" ]] && printf '"%s"' "$code" || printf 'null' ),
  "fallback_to_tui": $fallback,
  "execute_allowed": false,
  "secrets_exposed": false
}
EOF
  setuphelfer_rescue_mirror_evidence_file "$STATE" "setuphelfer/evidence/boot/gui-watchdog.json" 2>/dev/null || true
  setuphelfer_rescue_mirror_evidence_file "$LOG" "setuphelfer/logs/boot/gui-start.log" 2>/dev/null || true
}

[[ -f "$HTML" ]] || { write_state "gui_frontend_missing"; return 1; }

if ! "${SCRIPT_DIR}/setuphelfer-rescue-backend-start.sh" >>"$LOG" 2>&1; then
  write_state "gui_backend_unreachable"
  return 1
fi

if ! command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1 \
   && ! command -v firefox >/dev/null 2>&1; then
  write_state "gui_browser_missing"
  return 1
fi

if [[ ! -x "$KIOSK" ]]; then
  write_state "gui_unknown_failure"
  return 1
fi

# Start kiosk in background; watchdog waits for browser process or times out.
"$KIOSK" >>"$LOG" 2>&1 &
_kpid=$!
_elapsed=0
while [[ "$_elapsed" -lt "$TIMEOUT_SEC" ]]; do
  if ! kill -0 "$_kpid" 2>/dev/null; then
    write_state "gui_unknown_failure"
    return 1
  fi
  if pgrep -f 'chromium.*rescue\.html' >/dev/null 2>&1 || pgrep -f 'firefox.*127\.0\.0\.1' >/dev/null 2>&1; then
    write_state "" true false
    wait "$_kpid" 2>/dev/null || true
    return 0
  fi
  sleep 2
  _elapsed=$((_elapsed + 2))
done

pkill -f 'chromium.*rescue' 2>/dev/null || true
pkill -f 'setuphelfer-rescue-ui-launch' 2>/dev/null || true
kill "$_kpid" 2>/dev/null || true
chvt 1 2>/dev/null || true
write_state "gui_start_timeout"
return 1
