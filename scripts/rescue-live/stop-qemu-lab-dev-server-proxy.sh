#!/usr/bin/env bash
set -euo pipefail
PID_FILE="${SETUPHELFER_QEMU_LAB_PROXY_PID_FILE:-/tmp/setuphelfer-qemu-lab-proxy.pid}"
PROXY_PORT="${SETUPHELFER_QEMU_LAB_PROXY_PORT:-8001}"

_stopped=false
if [[ -f "$PID_FILE" ]]; then
  if kill "$(cat "$PID_FILE")" 2>/dev/null; then
    _stopped=true
  fi
  rm -f "$PID_FILE"
fi

_line="$(ss -tlnp "sport = :${PROXY_PORT}" 2>/dev/null | awk '/LISTEN/ {print; exit}')" || true
if [[ -n "$_line" ]] && [[ "$_line" =~ pid=([0-9]+) ]]; then
  _pid="${BASH_REMATCH[1]}"
  if kill "$_pid" 2>/dev/null; then
    _stopped=true
    echo "OK: stopped socat on port ${PROXY_PORT} pid=${_pid}"
  fi
fi

if [[ "$_stopped" == true ]]; then
  echo "OK: proxy stopped"
else
  echo "OK: no proxy running (port ${PROXY_PORT})"
fi
