#!/usr/bin/env bash
# QEMU Guest Agent Smoke — Operator only (requires sudo + local_lab + release trap).
# Requires developer-qemu prepared build tree + rebuilt ISO before autopilot smoke.
# Usage: sudo -v && ./scripts/rescue-live/qemu-guest-agent-smoke-operator.sh
set -euo pipefail

cd "$(dirname "$0")/../.."

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
  curl -sS http://127.0.0.1:8000/api/version \
    | jq '{install_profile, profile_gate_status, dev_control_enabled, backend_runtime_path}' \
    | tee -a "$LOG" || true
}

trap restore_release EXIT

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

PROFILE="$(curl -sS http://127.0.0.1:8000/api/version | jq -r '.install_profile // "unknown"')"
if [[ "$PROFILE" != "local_lab" ]]; then
  echo "ABORT: install_profile=$PROFILE (need local_lab)" | tee -a "$LOG"
  exit 11
fi
echo "PROFILE_GUARD_OK local_lab" | tee -a "$LOG"

echo "=== QEMU SMOKE (autopilot, no host disk, no USB) ===" | tee -a "$LOG"
scripts/rescue-live/run-qemu-developer-iso-smoke.sh "$RUN_ID" \
  --operator-confirm-qemu \
  --autopilot \
  --timeout-seconds 1200 \
  2>&1 | tee -a "$LOG"

echo "SMOKE_DONE run_id=$RUN_ID evidence=docs/evidence/runtime-results/rescue/qemu/${RUN_ID}" | tee -a "$LOG"
echo "trap will restore release on exit"
