#!/usr/bin/env bash
# Start public-repo lab mock servers (8100 beta, 8101 telemetry, 8102 diagnostics).
# No secrets, no persistence. Stop with: kill $(cat /tmp/setuphelfer-lab-mocks.pid)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PIDFILE="/tmp/setuphelfer-lab-mocks.pid"
LOGDIR="${TMPDIR:-/tmp}/setuphelfer-lab-mocks"
mkdir -p "$LOGDIR"

start_one() {
  local name="$1"
  local script="$2"
  local port="$3"
  python3 "$script" >"$LOGDIR/${name}.log" 2>&1 &
  echo $! >>"$PIDFILE"
  echo "started $name on :$port (log: $LOGDIR/${name}.log)"
}

: >"$PIDFILE"
start_one beta "$ROOT/backend/dev/beta_registration_mock_server_v1.py" 8100
start_one telemetry "$ROOT/backend/dev/telemetry_mock_server_v2.py" 8101
start_one diagnostics "$ROOT/backend/dev/diagnostics_mock_server_v1.py" 8102

sleep 1
for port in 8100 8101 8102; do
  if curl -sf "http://127.0.0.1:${port}/health" >/dev/null; then
    echo "OK health :$port"
  else
    echo "WARN health :$port not ready — see $LOGDIR"
  fi
done
echo "PID file: $PIDFILE"
