#!/usr/bin/env bash
# Start allowlisted rescue telemetry LAN proxy (health + ingest only).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/backend:${REPO_ROOT}:${PYTHONPATH:-}"

PORT="${SETUPHELFER_RESCUE_TELEMETRY_PORT:-8001}"
UPSTREAM="${SETUPHELFER_RESCUE_TELEMETRY_UPSTREAM:-http://127.0.0.1:8000}"
PID_FILE="/tmp/setuphelfer-rescue-telemetry-lan-proxy.pid"
LOG_FILE="${REPO_ROOT}/docs/evidence/runtime-results/rescue/rescue_telemetry_lan_proxy_latest.log"
STATUS_FILE="${REPO_ROOT}/docs/evidence/runtime-results/rescue/rescue_telemetry_lan_proxy_status_latest.json"

BIND="${SETUPHELFER_RESCUE_TELEMETRY_BIND:-}"
if [[ -z "$BIND" ]]; then
  BIND="$(python3 - <<'PY'
from core.rescue_telemetry_lan_proxy import detect_lan_ip
print(detect_lan_ip() or "")
PY
)"
fi

if [[ -z "$BIND" ]]; then
  echo "ERROR: LAN_BIND_BLOCKED — could not detect LAN IP; set SETUPHELFER_RESCUE_TELEMETRY_BIND" >&2
  exit 11
fi

if [[ -f "$PID_FILE" ]]; then
  _pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$_pid" ]] && kill -0 "$_pid" 2>/dev/null; then
    echo "OK: proxy already running pid=${_pid}"
    exec "$SCRIPT_DIR/status-rescue-telemetry-lan-proxy.sh"
  fi
  rm -f "$PID_FILE"
fi

if ss -tln "sport = :${PORT}" 2>/dev/null | grep -q LISTEN; then
  echo "ERROR: PORT_8001_BLOCKED — port ${PORT} already in use" >&2
  exit 12
fi

if ! curl -sf --max-time 3 "${UPSTREAM%/}/api/rescue/telemetry/health" >/dev/null; then
  echo "ERROR: BACKEND_HEALTH_FAILED — ${UPSTREAM}/api/rescue/telemetry/health" >&2
  exit 13
fi

mkdir -p "$(dirname "$LOG_FILE")" "$(dirname "$STATUS_FILE")"
: >>"$LOG_FILE"

nohup python3 "$SCRIPT_DIR/rescue_telemetry_lan_proxy.py" \
  --bind "$BIND" \
  --port "$PORT" \
  --upstream "$UPSTREAM" >>"$LOG_FILE" 2>&1 &
_proxy_pid=$!
sleep 0.8

if ! kill -0 "$_proxy_pid" 2>/dev/null; then
  echo "ERROR: proxy failed to start — see $LOG_FILE" >&2
  tail -20 "$LOG_FILE" >&2 || true
  exit 14
fi

echo "$_proxy_pid" >"$PID_FILE"

_health_url="http://${BIND}:${PORT}/api/rescue/telemetry/health"
if ! curl -sf --max-time 5 "$_health_url" >/dev/null; then
  echo "ERROR: LAN_HEALTH_FAILED — $_health_url" >&2
  "$SCRIPT_DIR/stop-rescue-telemetry-lan-proxy.sh" || true
  exit 15
fi

python3 - <<PY
import json
from pathlib import Path
from core.rescue_telemetry_lan_proxy import build_status_payload, health_url, ingest_url
payload = build_status_payload(
    running=True,
    pid=${_proxy_pid},
    bind_host="${BIND}",
    port=${PORT},
    upstream="${UPSTREAM}",
    backend_health_ok=True,
    lan_health_ok=True,
)
Path("${STATUS_FILE}").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
print("health_url=" + health_url("${BIND}", ${PORT}))
print("ingest_url=" + ingest_url("${BIND}", ${PORT}))
PY

echo "OK: rescue telemetry LAN proxy started pid=${_proxy_pid} bind=${BIND}:${PORT}"
