#!/bin/bash
# GUI start with watchdog — returns to TUI on failure (RS-P2C, RS-P2G strict gates).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh"

TIMEOUT_SEC="${SETUPHELFER_GUI_WATCHDOG_SEC:-120}"
STABLE_SEC="${SETUPHELFER_GUI_STABLE_SEC:-5}"
LOG="/run/setuphelfer/gui-start.log"
STATE="${SETUPHELFER_RESCUE_STATE_DIR}/gui-watchdog.json"
HTML="/usr/share/setuphelfer/rescue/ui/rescue.html"
KIOSK="${SCRIPT_DIR}/setuphelfer-rescue-kiosk-start"
UI_STATUS="/run/setuphelfer/rescue-ui-status.json"

export SETUPHELFER_RESCUE_GUI_STRICT=1
export SETUPHELFER_RESCUE_KIOSK_VT=2
export SETUPHELFER_RESCUE_UI_GRAPHICAL_ONLY=1

mkdir -p /run/setuphelfer "$(dirname "$LOG")" 2>/dev/null || true
setuphelfer_rescue_gui_chain_log_init

setuphelfer_rescue_gui_chain_log "START_GUI_CHAIN" "component=gui-watchdog timeout_sec=${TIMEOUT_SEC} stable_sec=${STABLE_SEC}"
setuphelfer_rescue_gui_chain_log_display_ctx

write_state() {
  local code="$1" started="${2:-false}" fallback="${3:-true}"
  setuphelfer_rescue_gui_chain_log "GUI_WATCHDOG_STATE" "gui_started=${started} gui_failed=${fallback} code=${code:-null}"
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
  setuphelfer_rescue_mirror_gui_forensic_logs
}

_write_ui_status_failed() {
  local reason="$1"
  setuphelfer_rescue_write_json "$UI_STATUS" <<EOF
{
  "schema_version": 1,
  "browser_started": false,
  "server_started": false,
  "menu_visible": false,
  "status": "failed",
  "reason": "$reason",
  "display_mode": "failed",
  "secrets_exposed": false
}
EOF
  setuphelfer_rescue_mirror_evidence_file "$UI_STATUS" "setuphelfer/evidence/boot/rescue-ui-status.json" 2>/dev/null || true
}

_fail() {
  local code="$1"
  setuphelfer_rescue_capture_x11_forensics
  _write_ui_status_failed "$code"
  write_state "$code" false true
  setuphelfer_rescue_gui_chain_log "GUI_WATCHDOG_RETURN" "RESULT=1 code=${code}"
  setuphelfer_rescue_mirror_gui_forensic_logs
  return 1
}

[[ -f "$HTML" ]] || {
  setuphelfer_rescue_gui_chain_log "CHECK_FRONTEND" "missing=${HTML}"
  return $(_fail "unknown_gui_failure")
}
setuphelfer_rescue_gui_chain_log "CHECK_FRONTEND" "ok=${HTML}"

# RS-P2O: backend + kiosk in parallel — health loop waits for API.
setuphelfer_rescue_backend_start_async "$LOG"

if ! command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1 \
   && ! command -v firefox >/dev/null 2>&1; then
  setuphelfer_rescue_gui_chain_log "CHECK_BROWSER" "RESULT=missing"
  return $(_fail "chromium_missing")
fi
setuphelfer_rescue_gui_chain_log "CHECK_BROWSER" "RESULT=ok"

if [[ ! -x "$KIOSK" ]]; then
  setuphelfer_rescue_gui_chain_log "CHECK_KIOSK" "RESULT=not_executable path=${KIOSK}"
  return $(_fail "unknown_gui_failure")
fi
setuphelfer_rescue_gui_chain_log "CHECK_KIOSK" "RESULT=ok path=${KIOSK}"

if [[ ! -c /dev/tty1 ]]; then
  setuphelfer_rescue_gui_chain_log "CHECK_TTY" "tty1=missing"
  return $(_fail "tty_unavailable")
fi
setuphelfer_rescue_blank_fb_tty 1
chvt "$SETUPHELFER_RESCUE_KIOSK_VT" 2>/dev/null || true
setuphelfer_rescue_gui_chain_log "CHECK_TTY" "tty1=blanked kiosk_vt=${SETUPHELFER_RESCUE_KIOSK_VT}"

# RS-P2G: kiosk on dedicated VT with controlling terminal (openvt), not background on watchdog shell.
setuphelfer_rescue_gui_chain_log "KIOSK_FOREGROUND_VT" "vt=${SETUPHELFER_RESCUE_KIOSK_VT}"
setuphelfer_rescue_run_on_kiosk_vt "$KIOSK" >>"$LOG" 2>&1 &
_kpid=$!
setuphelfer_rescue_gui_chain_log "KIOSK_STARTED" "pid=${_kpid}"

_elapsed=0
_health_rc=99
while [[ "$_elapsed" -lt "$TIMEOUT_SEC" ]]; do
  if ! kill -0 "$_kpid" 2>/dev/null; then
    setuphelfer_rescue_gui_chain_log "KIOSK_PID_EXIT" "pid=${_kpid} elapsed_sec=${_elapsed}"
    if ! setuphelfer_rescue_x11_ready; then
      return $(_fail "startx_not_started")
    fi
    if ! setuphelfer_rescue_chromium_running; then
      return $(_fail "chromium_crashed")
    fi
    return $(_fail "unknown_gui_failure")
  fi

  if setuphelfer_rescue_gui_health_ok "$STABLE_SEC"; then
    _health_rc=0
    setuphelfer_rescue_gui_chain_log "GUI_HEALTH_OK" "stable_sec=${STABLE_SEC} elapsed_sec=${_elapsed}"
    break
  fi
  _health_rc=$?
  setuphelfer_rescue_gui_chain_log "GUI_HEALTH_WAIT" "rc=${_health_rc} elapsed_sec=${_elapsed}"
  if [[ "$_health_rc" -ne 0 ]]; then
    setuphelfer_rescue_gui_chain_log "GUI_HEALTH_FAIL" "rc=${_health_rc} elapsed_sec=${_elapsed}"
  fi
  sleep 2
  _elapsed=$((_elapsed + 2))
done

if [[ "$_health_rc" -ne 0 ]]; then
  setuphelfer_rescue_gui_chain_log "GUI_WATCHDOG_TIMEOUT" "elapsed_sec=${_elapsed} last_rc=${_health_rc}"
  pkill -f 'chromium.*rescue' 2>/dev/null || true
  pkill -f 'setuphelfer-rescue-ui-launch' 2>/dev/null || true
  kill "$_kpid" 2>/dev/null || true
  chvt 1 2>/dev/null || true
  case "$_health_rc" in
    1) return $(_fail "backend_unreachable") ;;
    2) return $(_fail "display_missing") ;;
    3) return $(_fail "xorg_missing") ;;
    4|5) return $(_fail "chromium_crashed") ;;
    *) return $(_fail "kiosk_timeout") ;;
  esac
fi

write_state "" true false
setuphelfer_rescue_gui_chain_log "GUI_WATCHDOG_SUCCESS" "stable_sec=${STABLE_SEC}"
chvt "$SETUPHELFER_RESCUE_KIOSK_VT" 2>/dev/null || true
wait "$_kpid" 2>/dev/null || true
setuphelfer_rescue_gui_chain_log "GUI_WATCHDOG_RETURN" "RESULT=0"
return 0
