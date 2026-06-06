#!/usr/bin/env bash
set -euo pipefail

PID_FILE="/tmp/setuphelfer-rescue-telemetry-lan-proxy.pid"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/backend:${REPO_ROOT}:${PYTHONPATH:-}"
STATUS_FILE="${REPO_ROOT}/docs/evidence/runtime-results/rescue/rescue_telemetry_lan_proxy_status_latest.json"

_stopped=false
if [[ -f "$PID_FILE" ]]; then
  _pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$_pid" ]] && kill "$_pid" 2>/dev/null; then
    _stopped=true
    echo "OK: stopped rescue telemetry LAN proxy pid=${_pid}"
  fi
  rm -f "$PID_FILE"
fi

if [[ "$_stopped" != true ]]; then
  echo "OK: no rescue telemetry LAN proxy running"
fi

python3 - <<PY || true
import json
from pathlib import Path
from core.rescue_telemetry_lan_proxy import build_status_payload, detect_lan_ip, DEFAULT_PORT, DEFAULT_UPSTREAM
port = DEFAULT_PORT
bind = detect_lan_ip()
payload = build_status_payload(
    running=False,
    pid=None,
    bind_host=bind,
    port=port,
    upstream=DEFAULT_UPSTREAM,
    backend_health_ok=False,
    lan_health_ok=False,
)
Path("${STATUS_FILE}").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
