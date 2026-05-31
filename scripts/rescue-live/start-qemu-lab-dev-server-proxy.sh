#!/usr/bin/env bash
# Lab-only: forward 0.0.0.0:PROXY_PORT → 127.0.0.1:8000 for QEMU guest (10.0.2.2:PROXY_PORT).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROXY_PORT="${SETUPHELFER_QEMU_LAB_PROXY_PORT:-8001}"
TARGET="${SETUPHELFER_QEMU_LAB_PROXY_TARGET:-127.0.0.1:8000}"
PID_FILE="${SETUPHELFER_QEMU_LAB_PROXY_PID_FILE:-/tmp/setuphelfer-qemu-lab-proxy.pid}"
LOG_FILE="${SETUPHELFER_QEMU_LAB_PROXY_LOG:-/tmp/setuphelfer-qemu-lab-proxy.log}"

command -v socat >/dev/null || { echo "socat required" >&2; exit 1; }

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "OK: proxy already running pid=$(cat "$PID_FILE") port=${PROXY_PORT}"
  exit 0
fi

socat "TCP-LISTEN:${PROXY_PORT},bind=0.0.0.0,reuseaddr,fork" "TCP:${TARGET}" >>"$LOG_FILE" 2>&1 &
echo $! >"$PID_FILE"
sleep 0.5
if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
  echo "ERROR: proxy failed to start — see $LOG_FILE" >&2
  exit 1
fi
echo "OK: QEMU lab proxy pid=$(cat "$PID_FILE") listen=0.0.0.0:${PROXY_PORT} target=${TARGET}"
echo "Guest URL: http://10.0.2.2:${PROXY_PORT}"
