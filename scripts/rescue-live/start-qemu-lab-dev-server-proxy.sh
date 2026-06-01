#!/usr/bin/env bash
# Lab-only: forward 0.0.0.0:PROXY_PORT → 127.0.0.1:8000 for QEMU guest (10.0.2.2:PROXY_PORT).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROXY_PORT="${SETUPHELFER_QEMU_LAB_PROXY_PORT:-8001}"
PROXY_BIND="${SETUPHELFER_QEMU_LAB_PROXY_BIND:-127.0.0.1}"
TARGET="${SETUPHELFER_QEMU_LAB_PROXY_TARGET:-127.0.0.1:8000}"
PID_FILE="${SETUPHELFER_QEMU_LAB_PROXY_PID_FILE:-/tmp/setuphelfer-qemu-lab-proxy.pid}"
LOG_FILE="${SETUPHELFER_QEMU_LAB_PROXY_LOG:-/tmp/setuphelfer-qemu-lab-proxy.log}"

command -v socat >/dev/null || { echo "socat required" >&2; exit 1; }

_proxy_listen_pid() {
  local port="$1"
  local line pid
  line="$(ss -tlnp "sport = :${port}" 2>/dev/null | awk '/LISTEN/ {print; exit}')" || true
  [[ -n "$line" ]] || return 1
  if [[ "$line" =~ pid=([0-9]+) ]]; then
    pid="${BASH_REMATCH[1]}"
    kill -0 "$pid" 2>/dev/null || return 1
    echo "$pid"
    return 0
  fi
  return 1
}

_proxy_ok_message() {
  local pid="$1"
  echo "OK: QEMU lab proxy pid=${pid} listen=${PROXY_BIND}:${PROXY_PORT} target=${TARGET}"
  echo "Guest URL: http://10.0.2.2:${PROXY_PORT}"
  if [[ "$PROXY_BIND" == "0.0.0.0" ]]; then
    echo "WARN: proxy binds 0.0.0.0 (LAN-visible) — lab only; use firewall; not for public exposure"
  fi
}

if [[ -f "$PID_FILE" ]]; then
  _pid="$(cat "$PID_FILE")"
  if kill -0 "$_pid" 2>/dev/null; then
    echo "OK: proxy already running pid=${_pid} port=${PROXY_PORT}"
    _proxy_ok_message "$_pid"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

if _existing="$(_proxy_listen_pid "$PROXY_PORT")"; then
  echo "$_existing" >"$PID_FILE"
  echo "OK: reusing proxy already listening on port ${PROXY_PORT} pid=${_existing}"
  _proxy_ok_message "$_existing"
  exit 0
fi

if [[ "$PROXY_BIND" == "0.0.0.0" ]] && [[ "${SETUPHELFER_QEMU_LAB_PROXY_OPERATOR_CONFIRM_LAN_BIND:-}" != "true" ]]; then
  echo "ERROR: bind 0.0.0.0 requires SETUPHELFER_QEMU_LAB_PROXY_OPERATOR_CONFIRM_LAN_BIND=true" >&2
  echo "  For QEMU slirp guest access, run-qemu-developer-iso-smoke.sh sets this automatically." >&2
  echo "  Manual start: export SETUPHELFER_QEMU_LAB_PROXY_BIND=127.0.0.1 (guest may not reach host)" >&2
  exit 1
fi

: >>"$LOG_FILE"
socat "TCP-LISTEN:${PROXY_PORT},bind=${PROXY_BIND},reuseaddr,fork" "TCP:${TARGET}" >>"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"
sleep 0.5
if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  if _existing="$(_proxy_listen_pid "$PROXY_PORT")"; then
    echo "$_existing" >"$PID_FILE"
    echo "OK: reusing proxy on port ${PROXY_PORT} pid=${_existing} (race with parallel start)"
    _proxy_ok_message "$_existing"
    exit 0
  fi
  if grep -q "Address already in use" "$LOG_FILE" 2>/dev/null; then
    echo "ERROR: port ${PROXY_PORT} is in use but not tracked in ${PID_FILE}" >&2
    echo "  Stop it: scripts/rescue-live/stop-qemu-lab-dev-server-proxy.sh" >&2
    echo "  Or: ss -tlnp | grep :${PROXY_PORT}" >&2
  else
    echo "ERROR: proxy failed to start — see $LOG_FILE" >&2
  fi
  rm -f "$PID_FILE"
  exit 1
fi
_proxy_ok_message "$(cat "$PID_FILE")"
