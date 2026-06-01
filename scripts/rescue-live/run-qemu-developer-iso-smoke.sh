#!/usr/bin/env bash
# QEMU developer ISO smoke — optional autopilot (no manual guest typing).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ISO_REL="build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"
ISO_PATH="${REPO_ROOT}/${ISO_REL}"
RUN_ID="${1:-qemu_rescue_developer_iso_$(date -u +%Y%m%d_%H%M%S)}"
EVDIR="${REPO_ROOT}/docs/evidence/runtime-results/rescue/qemu/${RUN_ID}"
PID_FILE="${EVDIR}/qemu_gtk_pid.txt"
SERIAL_LOG="${EVDIR}/qemu-serial.log"
RESULT_JSON="${EVDIR}/qemu_autopilot_result.json"
HOST_DEV_URL="${SETUPHELFER_DEV_AGENT_QEMU_HOST_URL:-}"
CONFIRM=false
REMOTE_VNC=false
HEADLESS=false
SSH_FORWARD=false
GUESTFWD_PROXY=true
AUTOPILOT=false
LAB_PROXY_PORT="${SETUPHELFER_QEMU_LAB_PROXY_PORT:-8001}"
TIMEOUT_SECONDS=900
USER_SET_HOST_URL=false
KEYBOARD="${SETUPHELFER_QEMU_KEYBOARD:-de}"

usage() {
  cat <<EOF
Usage: $0 [RUN_ID] [--operator-confirm-qemu] [--autopilot] [--remote-vnc-local]
       [--host-dev-server-url URL] [--proxy-port N] [--timeout-seconds N]

Autopilot: guest smoke runs via systemd — no manual typing in QEMU window.
EOF
}

die() { echo "ERROR: $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) shift ;;
    --operator-confirm-qemu) CONFIRM=true; shift ;;
    --autopilot) AUTOPILOT=true; TIMEOUT_SECONDS=900; HEADLESS=true; shift ;;
    --remote-vnc-local) REMOTE_VNC=true; shift ;;
    --ssh-forward-local) SSH_FORWARD=true; shift ;;
    --keyboard) KEYBOARD="${2:-de}"; shift 2 ;;
    --host-dev-server-url) HOST_DEV_URL="${2:-}"; USER_SET_HOST_URL=true; shift 2 ;;
    --proxy-port) LAB_PROXY_PORT="${2:-8001}"; shift 2 ;;
    --timeout-seconds) TIMEOUT_SECONDS="${2:-240}"; shift 2 ;;
    --headless) HEADLESS=true; shift ;;
    --no-lab-proxy) GUESTFWD_PROXY=false; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      if [[ "$1" == qemu_rescue_developer_* || "$1" == qemu_host_* || "$1" == qemu_rescue_developer_autopilot_* ]]; then
        RUN_ID="$1"; shift
      else die "unknown arg: $1"; fi
      ;;
  esac
done

[[ -f "$REPO_ROOT/.git/config" || -d "$REPO_ROOT/.git" ]] || die "not repo root"
[[ -f "$ISO_PATH" ]] || die "ISO missing: $ISO_PATH"

# shellcheck source=scripts/rescue-live/fleet-session-api.sh
source "${SCRIPT_DIR}/fleet-session-api.sh"

FLEET_SESSION_ID=""
HAS_KVM=false
KVM_ENABLED=false
ACCELERATION="tcg"
if [[ -r /dev/kvm ]]; then HAS_KVM=true; fi

_fleet_serial_stats() {
  FLEET_SERIAL_SIZE_BYTES=0
  FLEET_SERIAL_EXISTS=false
  if [[ -f "$SERIAL_LOG" ]]; then
    FLEET_SERIAL_EXISTS=true
    FLEET_SERIAL_SIZE_BYTES="$(stat -c%s "$SERIAL_LOG" 2>/dev/null || echo 0)"
  fi
}

_fleet_heartbeat_loop() {
  [[ -n "$FLEET_SESSION_ID" ]] || return 0
  while kill -0 "${QPID:-0}" 2>/dev/null; do
    _fleet_serial_stats
    local hb_payload
    hb_payload="$(fleet_session_heartbeat_payload "" "$SERIAL_LOG" "$FLEET_SERIAL_EXISTS" "$FLEET_SERIAL_SIZE_BYTES" "${QPID:-}" "" "" "" "[]")" || continue
    fleet_session_patch "$FLEET_SESSION_ID" heartbeat "$hb_payload" >/dev/null || true
    sleep 20
  done
}

_fleet_finish_session() {
  local final_status="$1"
  [[ -n "$FLEET_SESSION_ID" ]] || return 0
  _fleet_serial_stats
  local guest_seen=false
  [[ "${DEV_SERVER_REPORT_NEW:-false}" == "true" ]] && guest_seen=true
  local findings_json="[]"
  if [[ "${FLEET_SERIAL_SIZE_BYTES:-0}" -eq 0 ]]; then
    findings_json='["serial_empty","classification_hint_serial_empty_boot_unknown"]'
  fi
  export FLEET_SERIAL_PATH="${SERIAL_LOG}"
  export FLEET_SERIAL_EXISTS="${FLEET_SERIAL_EXISTS}"
  export FLEET_ACCELERATION="${ACCELERATION}"
  export FLEET_KVM_ENABLED="${KVM_ENABLED}"
  export FLEET_HAS_KVM="${HAS_KVM}"
  local payload
  payload="$(fleet_session_finish_payload "$final_status" "$QEMU_EXIT" "$guest_seen" "$DEV_SERVER_REPORT_NEW" "$FLEET_SERIAL_SIZE_BYTES" "$findings_json")" || return 1
  fleet_session_patch "$FLEET_SESSION_ID" finish "$payload" >/dev/null || true
}

mkdir -p "$EVDIR"
export SETUPHELFER_FLEET_JSON_ERROR_LOG="${EVDIR}/fleet_session_json_errors.log"

ISO_REL_EVIDENCE="${ISO_REL}"
FLEET_CREATE_PAYLOAD="$(fleet_session_create_payload "$RUN_ID" "$ISO_REL_EVIDENCE" "$LAB_PROXY_PORT" "$TIMEOUT_SECONDS" "$HAS_KVM" "local_qemu_smoke" "QEMU Developer ISO Smoke" "docs/evidence/runtime-results/rescue/qemu/${RUN_ID}")"
FLEET_CREATE_RESP="$(fleet_session_create "$FLEET_CREATE_PAYLOAD" || true)"
FLEET_SESSION_ID="$(fleet_session_parse_id "$FLEET_CREATE_RESP")"
[[ -n "$FLEET_SESSION_ID" ]] || FLEET_SESSION_ID="fleet-${RUN_ID}"
echo "Fleet session: ${FLEET_SESSION_ID}"

if [[ "$GUESTFWD_PROXY" == true ]]; then
  fleet_session_patch "$FLEET_SESSION_ID" heartbeat "$(fleet_session_patch_simple "proxy_starting")" >/dev/null || true
  if [[ "$USER_SET_HOST_URL" != true ]]; then
    HOST_DEV_URL="http://10.0.2.2:${LAB_PROXY_PORT}"
  fi
  export SETUPHELFER_QEMU_LAB_PROXY_PID_FILE="${EVDIR}/qemu_lab_proxy.pid"
  export SETUPHELFER_QEMU_LAB_PROXY_PORT="${LAB_PROXY_PORT}"
  # QEMU slirp guest (10.0.2.2) requires host listener not bound to 127.0.0.1 only — lab LAN bind.
  export SETUPHELFER_QEMU_LAB_PROXY_BIND="0.0.0.0"
  export SETUPHELFER_QEMU_LAB_PROXY_OPERATOR_CONFIRM_LAN_BIND="true"
  "${SCRIPT_DIR}/start-qemu-lab-dev-server-proxy.sh"
  fleet_session_patch "$FLEET_SESSION_ID" heartbeat "$(fleet_session_patch_simple "proxy_ready")" >/dev/null || true
else
  HOST_DEV_URL="${HOST_DEV_URL:-http://10.0.2.2:8000}"
fi

curl -s http://127.0.0.1:8000/api/dev-server/summary >"${EVDIR}/dev_server_summary_before.json" 2>/dev/null || echo '{}' >"${EVDIR}/dev_server_summary_before.json"

NIC_OPTS="user,model=virtio-net-pci"
[[ "$SSH_FORWARD" == true ]] && NIC_OPTS="${NIC_OPTS},hostfwd=tcp:127.0.0.1:2222-:22"

QEMU_MACHINE_ARGS=()
if [[ -r /dev/kvm ]] && [[ "$(uname -m)" == "x86_64" ]]; then
  QEMU_MACHINE_ARGS=(-enable-kvm -cpu host)
  KVM_ENABLED=true
  ACCELERATION="kvm"
  echo "QEMU: KVM enabled (/dev/kvm)"
else
  echo "QEMU: KVM not available — TCG only (boot may exceed timeout)"
fi

fleet_session_patch "$FLEET_SESSION_ID" heartbeat "$(fleet_session_heartbeat_payload "qemu_starting" "" "false" "0" "" "$ACCELERATION" "$HAS_KVM" "$KVM_ENABLED" "[]")" >/dev/null || true

QEMU_ARGS=(
  "${QEMU_MACHINE_ARGS[@]}"
  -m 2048 -smp 2
  -cdrom "$ISO_PATH"
  -boot d -snapshot -no-reboot
  -serial "file:${SERIAL_LOG}"
  -monitor none
  -nic "$NIC_OPTS"
)

if [[ "$AUTOPILOT" == true ]] || [[ "$HEADLESS" == true ]]; then
  # No GTK window — avoids keyboard grab / input freeze; operator must not type.
  QEMU_ARGS+=(-display none)
else
  QEMU_ARGS+=(-display gtk -k "$KEYBOARD" -usb -device usb-tablet)
fi

[[ "$REMOTE_VNC" == true && "$HEADLESS" != true ]] && QEMU_ARGS+=(-vnc 127.0.0.1:1)

echo "=== QEMU Developer ISO Smoke ==="
echo "RUN_ID=$RUN_ID AUTOPILOT=$AUTOPILOT TIMEOUT=${TIMEOUT_SECONDS}s"
echo "HOST_DEV_URL=$HOST_DEV_URL PROXY=$GUESTFWD_PROXY"
printf 'CMD: '; printf '%q ' timeout "$TIMEOUT_SECONDS" qemu-system-x86_64 "${QEMU_ARGS[@]}"; echo

if [[ "$CONFIRM" != true ]]; then
  echo "DRY-RUN: pass --operator-confirm-qemu"
  exit 20
fi

command -v qemu-system-x86_64 >/dev/null || die "qemu-system-x86_64 missing"

cleanup_lab_proxy() {
  [[ "$GUESTFWD_PROXY" == true ]] || return 0
  SETUPHELFER_QEMU_LAB_PROXY_PID_FILE="${EVDIR}/qemu_lab_proxy.pid" \
    "${SCRIPT_DIR}/stop-qemu-lab-dev-server-proxy.sh" || true
}
trap cleanup_lab_proxy EXIT

: >"$SERIAL_LOG"
fleet_session_patch "$FLEET_SESSION_ID" heartbeat "$(fleet_session_heartbeat_payload "booting" "$SERIAL_LOG" "false" "0" "" "" "" "" "[]")" >/dev/null || true
timeout "$TIMEOUT_SECONDS" qemu-system-x86_64 "${QEMU_ARGS[@]}" \
  >"${EVDIR}/qemu-gtk-stdout.log" 2>"${EVDIR}/qemu-gtk-stderr.log" &
QPID=$!
echo "$QPID" >"$PID_FILE" 2>/dev/null || true
if [[ "$AUTOPILOT" == true ]]; then
  fleet_session_patch "$FLEET_SESSION_ID" heartbeat "$(fleet_session_patch_simple "autopilot_waiting")" >/dev/null || true
fi
_fleet_heartbeat_loop &
FLEET_HB_PID=$!
echo "QEMU pid=$QPID — waiting up to ${TIMEOUT_SECONDS}s (autopilot=$AUTOPILOT headless=$HEADLESS)"
if [[ "$AUTOPILOT" == true ]]; then
  echo "AUTOPILOT: do not use the QEMU window — smoke runs via systemd; read ${SERIAL_LOG} and ${RESULT_JSON}"
fi

QEMU_EXIT=0
wait "$QPID" 2>/dev/null || QEMU_EXIT=$?
kill "$FLEET_HB_PID" 2>/dev/null || true
wait "$FLEET_HB_PID" 2>/dev/null || true

curl -s http://127.0.0.1:8000/api/dev-server/summary >"${EVDIR}/dev_server_summary_after.json" 2>/dev/null || echo '{}' >"${EVDIR}/dev_server_summary_after.json"
curl -s http://127.0.0.1:8000/api/dev-server/reports >"${EVDIR}/dev_server_reports_after.json" 2>/dev/null || true

GUEST_JSON=""
if [[ -f "$SERIAL_LOG" ]]; then
  GUEST_JSON="$(python3 "${SCRIPT_DIR}/parse-qemu-serial-smoke-result.py" "$SERIAL_LOG" 2>/dev/null || true)"
fi

printf '%s\n' "$GUEST_JSON" | python3 - "$RESULT_JSON" "$RUN_ID" "$AUTOPILOT" "$QEMU_EXIT" "$HOST_DEV_URL" "$GUESTFWD_PROXY" \
  "${EVDIR}/dev_server_summary_before.json" "${EVDIR}/dev_server_summary_after.json" <<'PY'
import json, sys
from pathlib import Path

out_path, run_id, autopilot, qemu_exit, host_url, proxy = sys.argv[1:7]
before = json.loads(Path(sys.argv[7]).read_text(encoding="utf-8") or "{}")
after = json.loads(Path(sys.argv[8]).read_text(encoding="utf-8") or "{}")
guest_raw = sys.stdin.read().strip()
guest = None
if guest_raw:
    try:
        guest = json.loads(guest_raw)
    except json.JSONDecodeError:
        guest = {"parse_error": True}

reports_before = before.get("reports_last_24h")
reports_after = after.get("reports_last_24h")
report_new = (
    isinstance(reports_before, int) and isinstance(reports_after, int) and reports_after > reports_before
)

status = "review_required"
if guest and guest.get("status") == "success" and report_new:
    status = "success"
elif guest and guest.get("status") == "failed":
    status = "failed"
elif int(qemu_exit) == 124:
    status = "review_required" if guest else "failed"

payload = {
    "run_id": run_id,
    "status": status,
    "autopilot": autopilot == "true",
    "manual_guest_input_required": False if autopilot == "true" else True,
    "qemu_exit_code": int(qemu_exit),
    "host_dev_server_url": host_url,
    "lab_proxy_enabled": proxy == "true",
    "guest_smoke_from_serial": guest,
    "dev_server_reports_before": reports_before,
    "dev_server_reports_after": reports_after,
    "dev_server_report_new": report_new,
    "usb_write_started": False,
    "dd_executed": False,
    "backup_started": False,
    "restore_started": False,
}
Path(out_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"status": status, "report_new": report_new, "guest_found": guest is not None}))
PY

DEV_SERVER_REPORT_NEW="$(python3 -c "import json; print('true' if json.load(open('${RESULT_JSON}')).get('dev_server_report_new') else 'false')" 2>/dev/null || echo false)"

FINAL_FLEET_STATUS="failed"
if [[ "$QEMU_EXIT" -eq 0 ]] && [[ "$DEV_SERVER_REPORT_NEW" == true ]]; then
  FINAL_FLEET_STATUS="success"
elif [[ "$QEMU_EXIT" -eq 124 ]]; then
  FINAL_FLEET_STATUS="timeout"
elif [[ "$QEMU_EXIT" -eq 0 ]]; then
  FINAL_FLEET_STATUS="failed"
fi
_fleet_finish_session "$FINAL_FLEET_STATUS"

echo "Result: $RESULT_JSON"
cleanup_lab_proxy
exit 0
