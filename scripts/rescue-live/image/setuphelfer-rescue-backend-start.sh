#!/bin/bash
# Ensure rescue backend is running (read-only rescue mode).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh"

setuphelfer_rescue_ensure_state_dir
STATUS="${SETUPHELFER_RESCUE_STATE_DIR}/backend-start.json"

if curl -fsS --max-time 3 http://127.0.0.1:8000/api/version >/dev/null 2>&1; then
  setuphelfer_rescue_write_json "$STATUS" <<EOF
{"status":"running","reason":"api_version_ok","execute_allowed":false,"secrets_exposed":false}
EOF
  exit 0
fi

if systemctl is-active --quiet setuphelfer-backend.service 2>/dev/null; then
  sleep 2
  if curl -fsS --max-time 5 http://127.0.0.1:8000/api/version >/dev/null 2>&1; then
    setuphelfer_rescue_write_json "$STATUS" <<EOF
{"status":"running","reason":"systemd_active","execute_allowed":false,"secrets_exposed":false}
EOF
    exit 0
  fi
fi

systemctl start setuphelfer-backend.service 2>/dev/null || true
for _ in $(seq 1 20); do
  if curl -fsS --max-time 3 http://127.0.0.1:8000/api/version >/dev/null 2>&1; then
    setuphelfer_rescue_write_json "$STATUS" <<EOF
{"status":"running","reason":"started_by_script","execute_allowed":false,"secrets_exposed":false}
EOF
    exit 0
  fi
  sleep 1
done

setuphelfer_rescue_write_json "$STATUS" <<EOF
{"status":"failed","reason":"backend_not_running","error_code":"backend_not_running","execute_allowed":false,"secrets_exposed":false}
EOF
exit 1
