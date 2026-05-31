#!/usr/bin/env bash
# Plan/preview QEMU developer ISO smoke — does NOT start QEMU unless --operator-confirm-qemu.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ISO_REL="build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"
ISO_PATH="${REPO_ROOT}/${ISO_REL}"
RUN_ID="${1:-qemu_rescue_developer_iso_$(date -u +%Y%m%d_%H%M%S)}"
EVDIR="${REPO_ROOT}/docs/evidence/runtime-results/rescue/qemu/${RUN_ID}"
PID_FILE="${EVDIR}/qemu_gtk_pid.txt"
SERIAL_LOG="${EVDIR}/qemu-serial.log"
HOST_DEV_URL="${SETUPHELFER_DEV_AGENT_QEMU_HOST_URL:-http://10.0.2.2:8000}"
CONFIRM=false
REMOTE_VNC=false
SSH_FORWARD=false
KEYBOARD="${SETUPHELFER_QEMU_KEYBOARD:-de}"

usage() {
  cat <<EOF
Usage: $0 [RUN_ID] [--dry-run] [--operator-confirm-qemu] [--remote-vnc-local] [--ssh-forward-local]

Preview or start controlled QEMU developer ISO smoke (no USB, no host disk).

PID file: ${EVDIR}/qemu_gtk_pid.txt (never /qemu_gtk_pid.txt)
Host Dev Server URL for guest: ${HOST_DEV_URL}

Without --operator-confirm-qemu: print planned command only (exit 20).
EOF
}

die() { echo "ERROR: $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      shift
      ;;
    --operator-confirm-qemu)
      CONFIRM=true
      shift
      ;;
    --remote-vnc-local) REMOTE_VNC=true; shift ;;
    --ssh-forward-local) SSH_FORWARD=true; shift ;;
    --keyboard) KEYBOARD="${2:-de}"; shift 2 ;;
    --host-dev-server-url) HOST_DEV_URL="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *)
      if [[ "$1" == qemu_rescue_developer_iso_* ]]; then RUN_ID="$1"; shift
      else die "unknown arg: $1"; fi
      ;;
  esac
done

[[ -f "$REPO_ROOT/.git/config" || -d "$REPO_ROOT/.git" ]] || die "not repo root"
[[ -f "$ISO_PATH" ]] || die "ISO missing: $ISO_PATH"

mkdir -p "$EVDIR"

QEMU_ARGS=(
  -m 2048 -smp 2
  -cdrom "$ISO_PATH"
  -boot d -snapshot -no-reboot
  -serial "file:${SERIAL_LOG}"
  -display gtk
  -k "$KEYBOARD"
  -usb -device usb-tablet
  -nic "user,model=virtio-net-pci"
)

if [[ "$REMOTE_VNC" == true ]]; then
  QEMU_ARGS+=(-vnc 127.0.0.1:1)
fi
if [[ "$SSH_FORWARD" == true ]]; then
  QEMU_ARGS+=(-nic "user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:2222-:22")
fi

PLANNED=(timeout 900 qemu-system-x86_64 "${QEMU_ARGS[@]}")

echo "=== QEMU Developer ISO Smoke Plan ==="
echo "RUN_ID=$RUN_ID"
echo "EVDIR=$EVDIR"
echo "ISO=$ISO_PATH"
echo "PID_FILE=$PID_FILE"
echo "HOST_DEV_URL=$HOST_DEV_URL"
printf 'PLANNED: '; printf '%q ' "${PLANNED[@]}"; echo

write_pid_safe() {
  local pid="$1"
  if ! echo "$pid" >"$PID_FILE" 2>/dev/null; then
    echo "WRAPPER_WARNING: cannot write PID file $PID_FILE (boot not failed)" >&2
    return 1
  fi
  return 0
}

if [[ "$CONFIRM" != true ]]; then
  echo "DRY-RUN: pass --operator-confirm-qemu to start (not started)."
  exit 20
fi

command -v qemu-system-x86_64 >/dev/null || die "qemu-system-x86_64 missing"

: >"$SERIAL_LOG"
"${PLANNED[@]}" >"${EVDIR}/qemu-gtk-stdout.log" 2>"${EVDIR}/qemu-gtk-stderr.log" &
QPID=$!
write_pid_safe "$QPID" || true
echo "QEMU started pid=$QPID"
echo "wrapper_warning_pid_file=$([[ -f $PID_FILE ]] && echo false || echo true)" >"${EVDIR}/qemu_wrapper_meta.json"
exit 0
