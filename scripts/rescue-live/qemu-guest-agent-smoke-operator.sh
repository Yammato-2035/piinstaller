#!/usr/bin/env bash
# QEMU Guest Agent Smoke — Operator only (requires sudo + local_lab + release trap).
# Requires developer-qemu prepared build tree + rebuilt ISO before autopilot smoke.
# Usage: sudo -v && ./scripts/rescue-live/qemu-guest-agent-smoke-operator.sh
set -euo pipefail

cd "$(dirname "$0")/../.."
# shellcheck source=../lib/runtime-ports.sh
source "$(dirname "$0")/../lib/runtime-ports.sh"
API_BASE="$(runtime_ports_read api_base)"
LAB_PROXY_PORT="$(runtime_ports_read lab_proxy_port)"

RUN_ID="qemu_rescue_developer_autopilot_$(date -u +%Y%m%d_%H%M%S)"
ISO_PATH="build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"
MANIFEST="build/rescue/live-build/setuphelfer-rescue-live/evidence/build-tree-manifest.json"
LOG="docs/evidence/runtime-results/rescue/qemu/${RUN_ID}/operator_smoke.log"

restore_release() {
  echo "=== TRAP: restore release profile ===" | tee -a "$LOG"
  sudo install -m 0644 \
    packaging/systemd/dropins/92-install-profile-release.conf.example \
    /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
  sudo systemctl daemon-reload
  sudo systemctl restart setuphelfer-backend.service
  ./scripts/check-runtime-profile-deploy-gate.sh | tee -a "$LOG" || true
  curl -sS "${API_BASE}/api/version" \
    | jq '{install_profile, profile_gate_status, dev_control_enabled, backend_runtime_path}' \
    | tee -a "$LOG" || true
}

trap restore_release EXIT

abort_preflight() {
  echo "ABORT: $1" | tee -a "$LOG"
  exit "${2:-21}"
}

assert_devserver_preflight_ok() {
  local version_json profile dev_ctrl fleet_code dash_code
  if ! version_json="$(curl -sS -f "${API_BASE}/api/version" 2>/dev/null)"; then
    abort_preflight "blocked_devserver_not_enabled: GET /api/version failed" 21
  fi
  profile="$(echo "$version_json" | jq -r '.install_profile // empty')"
  dev_ctrl="$(echo "$version_json" | jq -r '.dev_control_enabled // false')"
  if [[ "$profile" == "release" ]]; then
    abort_preflight "blocked_profile_route_blocked: install_profile=release (need local_lab before QEMU smoke)" 21
  fi
  if [[ "$profile" != "local_lab" ]]; then
    abort_preflight "blocked_devserver_not_enabled: install_profile=${profile:-unknown}" 21
  fi
  if [[ "$dev_ctrl" != "true" ]]; then
    abort_preflight "blocked_devserver_not_enabled: dev_control_enabled=${dev_ctrl}" 21
  fi
  fleet_code="$(curl -sS -o /dev/null -w '%{http_code}' "${API_BASE}/api/fleet/sessions")"
  if [[ "$fleet_code" != "200" ]]; then
    abort_preflight "blocked_fleet_api_unavailable: GET /api/fleet/sessions HTTP ${fleet_code}" 21
  fi
  dash_code="$(curl -sS -o /dev/null -w '%{http_code}' "${API_BASE}/api/dev-dashboard/status")"
  if [[ "$dash_code" != "200" ]]; then
    abort_preflight "blocked_fleet_api_unavailable: GET /api/dev-dashboard/status HTTP ${dash_code}" 21
  fi
  if command -v ss >/dev/null 2>&1 && ss -ltn 2>/dev/null | grep -q ":${LAB_PROXY_PORT} "; then
    echo "WARN: port ${LAB_PROXY_PORT} already listening — smoke proxy must reuse or free it" | tee -a "$LOG"
  fi
  echo "DEVSERVER_PREFLIGHT_OK profile=local_lab dev_control=true fleet_http=200 dashboard_http=200" | tee -a "$LOG"
}

mkdir -p "$(dirname "$LOG")"
{
  echo "task=qemu_guest_agent_smoke_operator_guarded"
  echo "run_id=$RUN_ID"
  echo "started_at=$(date -u --iso-8601=seconds)"
  echo "head=$(git rev-parse --short HEAD)"
} | tee "$LOG"

if [[ ! -f "$ISO_PATH" ]]; then
  echo "ABORT: ISO missing: $ISO_PATH" | tee -a "$LOG"
  exit 21
fi

python3 - "$MANIFEST" <<'PY' | tee -a "$LOG" || exit 32
import json
import sys
from pathlib import Path

p = Path(sys.argv[1])
if not p.is_file():
    print("ABORT: build-tree manifest missing — run SETUPHELFER_RESCUE_BUILD_PROFILE=developer-qemu prepare + ISO rebuild")
    sys.exit(1)
data = json.loads(p.read_text(encoding="utf-8"))
profile = data.get("rescue_build_profile")
if profile != "developer-qemu":
    print(f"ABORT: rescue_build_profile={profile!r} — QEMU autopilot requires developer-qemu ISO rebuild")
    sys.exit(1)
if not data.get("qemu_serial_console_configured") or not data.get("qemu_smoke_autopilot_hook"):
    print("ABORT: manifest missing qemu_serial_console_configured or qemu_smoke_autopilot_hook")
    sys.exit(1)
print(f"OK: manifest profile={profile} qemu_serial=yes autopilot_hook=yes")
PY

echo "=== ENABLE LOCAL_LAB ===" | tee -a "$LOG"
sudo install -d -m 0755 /etc/systemd/system/setuphelfer-backend.service.d
sudo install -m 0644 \
  packaging/systemd/dropins/92-install-profile-local-lab.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
sleep 2

PROFILE="$(curl -sS "${API_BASE}/api/version" | jq -r '.install_profile // "unknown"')"
if [[ "$PROFILE" != "local_lab" ]]; then
  echo "ABORT: install_profile=$PROFILE (need local_lab)" | tee -a "$LOG"
  exit 11
fi
assert_devserver_preflight_ok

echo "=== QEMU SMOKE (autopilot, no host disk, no USB) ===" | tee -a "$LOG"
scripts/rescue-live/run-qemu-developer-iso-smoke.sh "$RUN_ID" \
  --operator-confirm-qemu \
  --autopilot \
  --timeout-seconds 1200 \
  2>&1 | tee -a "$LOG"

echo "SMOKE_DONE run_id=$RUN_ID evidence=docs/evidence/runtime-results/rescue/qemu/${RUN_ID}" | tee -a "$LOG"
echo "trap will restore release on exit"
