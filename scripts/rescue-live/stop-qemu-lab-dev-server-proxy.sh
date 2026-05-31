#!/usr/bin/env bash
set -euo pipefail
PID_FILE="${SETUPHELFER_QEMU_LAB_PROXY_PID_FILE:-/tmp/setuphelfer-qemu-lab-proxy.pid}"
if [[ -f "$PID_FILE" ]]; then
  kill "$(cat "$PID_FILE")" 2>/dev/null || true
  rm -f "$PID_FILE"
  echo "OK: proxy stopped"
else
  echo "OK: no proxy pid file"
fi
