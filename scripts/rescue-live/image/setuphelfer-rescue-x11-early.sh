#!/bin/bash
# Start Xorg early on kiosk VT — parallel to backend boot (RS-P2O).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh"

KIOSK_VT="${SETUPHELFER_RESCUE_KIOSK_VT:-2}"
HOLD="${SCRIPT_DIR}/setuphelfer-rescue-x11-hold"
STATUS="/run/setuphelfer/x11-early.json"

mkdir -p /run/setuphelfer 2>/dev/null || true
setuphelfer_rescue_gui_chain_log_init 2>/dev/null || true

_write_status() {
  local st="$1" reason="$2"
  setuphelfer_rescue_write_json "$STATUS" <<EOF
{"schema_version":1,"status":"$st","reason":"$reason","execute_allowed":false,"secrets_exposed":false}
EOF
}

if ! setuphelfer_rescue_should_start_gui; then
  _write_status "skipped" "text_mode"
  exit 0
fi

if setuphelfer_rescue_x11_ready; then
  setuphelfer_rescue_gui_chain_log "X11_EARLY_SKIP" "reason=display_already_ready"
  _write_status "running" "already_ready"
  exit 0
fi

setuphelfer_rescue_log_x11_binaries
setuphelfer_rescue_xauthority_prepare || true

if ! command -v startx >/dev/null 2>&1; then
  setuphelfer_rescue_gui_chain_log "X11_EARLY_SKIP" "reason=startx_missing"
  _write_status "skipped" "startx_missing"
  exit 0
fi

if [[ ! -x "$HOLD" ]]; then
  _write_status "failed" "hold_script_missing"
  exit 1
fi

setuphelfer_rescue_gui_chain_log "X11_EARLY_START" "vt=${KIOSK_VT} hold=${HOLD}"
setuphelfer_rescue_x11_log "X11_EARLY_START" "vt=${KIOSK_VT}"

if command -v openvt >/dev/null 2>&1; then
  openvt -f -c "$KIOSK_VT" -- startx "$HOLD" -- ":0" "vt${KIOSK_VT}" >>"${SETUPHELFER_X11_LAUNCH_LOG:-/run/setuphelfer/x11-launch.log}" 2>&1 &
else
  startx "$HOLD" -- ":0" "vt${KIOSK_VT}" >>"${SETUPHELFER_X11_LAUNCH_LOG:-/run/setuphelfer/x11-launch.log}" 2>&1 &
fi
_xpid=$!
setuphelfer_rescue_gui_chain_log "X11_EARLY_FORKED" "pid=${_xpid}"

for _ in $(seq 1 45); do
  if setuphelfer_rescue_x11_ready; then
    setuphelfer_rescue_x11_log_xorg_pid || true
    setuphelfer_rescue_gui_chain_log "X11_EARLY_READY" "wait_sec=${_}"
    setuphelfer_rescue_blank_fb_tty 1
    chvt "$KIOSK_VT" 2>/dev/null || true
    _write_status "running" "x11_ready"
    exit 0
  fi
  if ! kill -0 "$_xpid" 2>/dev/null; then
    wait "$_xpid" 2>/dev/null || true
    break
  fi
  sleep 1
done

setuphelfer_rescue_gui_chain_log "X11_EARLY_TIMEOUT" "pid=${_xpid}"
setuphelfer_rescue_capture_x11_forensics
_write_status "deferred" "x11_not_ready_timeout"
exit 0
