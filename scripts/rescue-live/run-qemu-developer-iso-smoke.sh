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
    --autopilot) AUTOPILOT=true; TIMEOUT_SECONDS=240; shift ;;
    --remote-vnc-local) REMOTE_VNC=true; shift ;;
    --ssh-forward-local) SSH_FORWARD=true; shift ;;
    --keyboard) KEYBOARD="${2:-de}"; shift 2 ;;
    --host-dev-server-url) HOST_DEV_URL="${2:-}"; USER_SET_HOST_URL=true; shift 2 ;;
    --proxy-port) LAB_PROXY_PORT="${2:-8001}"; shift 2 ;;
    --timeout-seconds) TIMEOUT_SECONDS="${2:-240}"; shift 2 ;;
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

mkdir -p "$EVDIR"

if [[ "$GUESTFWD_PROXY" == true ]]; then
  if [[ "$USER_SET_HOST_URL" != true ]]; then
    HOST_DEV_URL="http://10.0.2.2:${LAB_PROXY_PORT}"
  fi
  export SETUPHELFER_QEMU_LAB_PROXY_PID_FILE="${EVDIR}/qemu_lab_proxy.pid"
  export SETUPHELFER_QEMU_LAB_PROXY_PORT="${LAB_PROXY_PORT}"
  "${SCRIPT_DIR}/start-qemu-lab-dev-server-proxy.sh"
else
  HOST_DEV_URL="${HOST_DEV_URL:-http://10.0.2.2:8000}"
fi

curl -s http://127.0.0.1:8000/api/dev-server/summary >"${EVDIR}/dev_server_summary_before.json" 2>/dev/null || echo '{}' >"${EVDIR}/dev_server_summary_before.json"

NIC_OPTS="user,model=virtio-net-pci"
[[ "$SSH_FORWARD" == true ]] && NIC_OPTS="${NIC_OPTS},hostfwd=tcp:127.0.0.1:2222-:22"

QEMU_ARGS=(
  -m 2048 -smp 2
  -cdrom "$ISO_PATH"
  -boot d -snapshot -no-reboot
  -serial "file:${SERIAL_LOG}"
  -display gtk
  -k "$KEYBOARD"
  -usb -device usb-tablet -device usb-kbd
  -nic "$NIC_OPTS"
)
[[ "$REMOTE_VNC" == true ]] && QEMU_ARGS+=(-vnc 127.0.0.1:1)

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
timeout "$TIMEOUT_SECONDS" qemu-system-x86_64 "${QEMU_ARGS[@]}" \
  >"${EVDIR}/qemu-gtk-stdout.log" 2>"${EVDIR}/qemu-gtk-stderr.log" &
QPID=$!
echo "$QPID" >"$PID_FILE" 2>/dev/null || true
echo "QEMU pid=$QPID — waiting up to ${TIMEOUT_SECONDS}s (autopilot=$AUTOPILOT)"

QEMU_EXIT=0
wait "$QPID" 2>/dev/null || QEMU_EXIT=$?

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

echo "Result: $RESULT_JSON"
cleanup_lab_proxy
exit 0
