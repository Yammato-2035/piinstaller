#!/bin/bash
# PI-RS-ASUS-ROOTCAUSE-006: unattended evidence + CPU/RAM/NVMe baseline on TUI-baseline.
# Read-only / bounded probes only — no NVMe writes, no SMART self-test, no GUI/startx.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh"

STATE_DIR="${SETUPHELFER_RESCUE_STATE_DIR:-/run/setuphelfer}"
MARKER="${STATE_DIR}/tui-baseline-autocapture.json"
SUMMARY="${STATE_DIR}/tui-baseline-autocapture-summary.json"
HW_JSON="${STATE_DIR}/hardware-baseline-quick.json"
OWNER_JSON="${STATE_DIR}/console-ownership.json"
DONE_FLAG="${STATE_DIR}/tui-baseline-autocapture.done"

mkdir -p "$STATE_DIR" 2>/dev/null || true

if [[ -f "$DONE_FLAG" ]]; then
  echo "tui_baseline_autocapture_already_done"
  exit 0
fi

if ! setuphelfer_rescue_tui_baseline_active 2>/dev/null; then
  echo "tui_baseline_autocapture_skipped_not_baseline"
  exit 0
fi

stamp_utc="$(date -u +%Y%m%d_%H%M%S 2>/dev/null || echo unknown)"
boot_id="$(cat /run/setuphelfer/boot_id 2>/dev/null || true)"
[[ -z "$boot_id" ]] && boot_id="$(cat /proc/sys/kernel/random/boot_id 2>/dev/null || echo unknown)"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo unknown)"

setuphelfer_rescue_write_boot_state "tui_baseline_autocapture_start" || true
setuphelfer_rescue_console_owner_transition "tui_owned" "autocapture_start" || true

diag_rc=0
hw_rc=0
runtime_rc=0

echo "[autocapture] boot-diagnostics…"
if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-boot-diagnostics" ]]; then
  "${SCRIPT_DIR}/setuphelfer-rescue-boot-diagnostics" boot || diag_rc=$?
elif [[ -x /usr/local/sbin/setuphelfer-rescue-boot-diagnostics ]]; then
  /usr/local/sbin/setuphelfer-rescue-boot-diagnostics boot || diag_rc=$?
else
  diag_rc=127
fi

echo "[autocapture] runtime-diagnostics…"
if [[ -x "${SCRIPT_DIR}/collect-rescue-runtime-diagnostics.sh" ]]; then
  "${SCRIPT_DIR}/collect-rescue-runtime-diagnostics.sh" || runtime_rc=$?
elif [[ -x /usr/local/sbin/collect-rescue-runtime-diagnostics ]]; then
  /usr/local/sbin/collect-rescue-runtime-diagnostics || runtime_rc=$?
fi

echo "[autocapture] disk/partitions preview (read-only)…"
PART_JSON="${STATE_DIR}/partitions-preview.json"
DISC_JSON="${STATE_DIR}/disk-discovery.json"
if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-disk-discovery" ]]; then
  "${SCRIPT_DIR}/setuphelfer-rescue-disk-discovery" >"$DISC_JSON" 2>/dev/null || true
elif [[ -x /usr/local/sbin/setuphelfer-rescue-disk-discovery ]]; then
  /usr/local/sbin/setuphelfer-rescue-disk-discovery >"$DISC_JSON" 2>/dev/null || true
fi

echo "[autocapture] hardware baseline quick (CPU/RAM/NVMe read-only)…"
PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath 2>/dev/null || echo /opt/setuphelfer-rescue/backend)"
export PYTHONPATH
PYBIN="$(setuphelfer_rescue_backend_python 2>/dev/null || command -v python3 || echo python3)"
echo "[autocapture] python=${PYBIN}"

part_rc=0
"$PYBIN" - "$DISC_JSON" "$PART_JSON" <<'PY' || part_rc=$?
import json, sys
from pathlib import Path
from rescue.rescue_partitions_tui_preview import build_partitions_tui_preview, write_partitions_preview_json
disc = {}
p = Path(sys.argv[1])
if p.is_file():
    try:
        disc = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        disc = {}
preview = build_partitions_tui_preview(disk_discovery=disc if isinstance(disc, dict) else None)
write_partitions_preview_json(Path(sys.argv[2]), preview)
print(f"partitions_preview disks={preview.get('disk_count')} parts={preview.get('partition_count')} write_allowed={preview.get('write_allowed')}")
PY
setuphelfer_rescue_mirror_evidence_file "$PART_JSON" "setuphelfer/evidence/partitions/partitions-preview.json" 2>/dev/null || true
setuphelfer_rescue_mirror_evidence_file "$DISC_JSON" "setuphelfer/evidence/partitions/disk-discovery.json" 2>/dev/null || true

"$PYBIN" - "$HW_JSON" <<'PY' || hw_rc=$?
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
payload = {
    "schema_version": 1,
    "campaign": "PI-RS-ASUS-ROOTCAUSE-TELEMETRY-006",
    "mode": "quick",
    "writes_allowed": False,
    "nvme_writes": False,
    "smart_self_test_started": False,
    "status": "failed",
    "error": None,
    "result": None,
}
try:
    from core.hardware_inventory import collect_pci_devices
    from rescue.hardware_baseline_orchestrator import run_hardware_baseline
    from rescue.hardware_baseline_storage_discovery import discover_storage_devices_for_baseline

    pci_devices, _missing = collect_pci_devices()
    try:
        cmdline = Path("/proc/cmdline").read_text(encoding="utf-8", errors="ignore")
    except OSError:
        cmdline = ""
    storage = discover_storage_devices_for_baseline()
    result = run_hardware_baseline(
        mode="quick",
        pci_devices=pci_devices,
        cmdline_raw=cmdline,
        storage_devices=storage,
    )
    payload["status"] = "ok"
    payload["result"] = result.to_dict()
    # Compact subsystem summary for operator glance
    payload["subsystem_summary"] = [
        {
            "subsystem": s.subsystem,
            "status": s.status,
            "severity": s.severity,
            "device_id": getattr(s, "device_id", None),
        }
        for s in result.subsystems
    ]
    payload["gate"] = result.gate.to_dict()
except Exception as exc:  # noqa: BLE001 — stick must continue to TUI
    payload["status"] = "failed"
    payload["error"] = f"{type(exc).__name__}: {exc}"
    print(payload["error"], file=sys.stderr)
    sys.exit(1)
finally:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY

# Persist console ownership snapshot if present in state dir after transitions
if [[ -f "$OWNER_JSON" ]]; then
  setuphelfer_rescue_mirror_evidence_file "$OWNER_JSON" "setuphelfer/evidence/boot/console-ownership.json" 2>/dev/null || true
fi

setuphelfer_rescue_mirror_evidence_file "$HW_JSON" "setuphelfer/evidence/hardware/baseline-quick.json" 2>/dev/null || true
setuphelfer_rescue_mirror_evidence_file "$HW_JSON" "setuphelfer/evidence/hardware/baseline-quick-${stamp_utc}.json" 2>/dev/null || true

finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo unknown)"
hw_status="unknown"
if [[ -f "$HW_JSON" ]]; then
  hw_status="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status","unknown"))' "$HW_JSON" 2>/dev/null || echo unknown)"
fi

cat >"$SUMMARY" <<EOF
{
  "schema_version": 1,
  "campaign": "PI-RS-ASUS-ROOTCAUSE-TELEMETRY-006",
  "profile": "ASUS-TUI-BASELINE",
  "stamp_utc": "${stamp_utc}",
  "boot_id": "${boot_id}",
  "started_at": "${started_at}",
  "finished_at": "${finished_at}",
  "boot_diagnostics_rc": ${diag_rc},
  "runtime_diagnostics_rc": ${runtime_rc},
  "partitions_preview_rc": ${part_rc},
  "hardware_baseline_rc": ${hw_rc},
  "hardware_baseline_status": "${hw_status}",
  "gui_started": false,
  "startx_started": false,
  "chromium_started": false,
  "nvme_writes": false,
  "smart_self_test_started": false,
  "partitions_write_allowed": false,
  "console_owner": "tui_owned",
  "secrets_exposed": false
}
EOF

cp -f "$SUMMARY" "$MARKER" 2>/dev/null || true
setuphelfer_rescue_mirror_evidence_file "$SUMMARY" "setuphelfer/evidence/boot/tui-baseline-autocapture.json" 2>/dev/null || true
setuphelfer_rescue_mirror_evidence_file "$SUMMARY" "setuphelfer/evidence/boot/tui-baseline-autocapture-${stamp_utc}.json" 2>/dev/null || true

# Persist boot_state after capture
setuphelfer_rescue_write_boot_state "tui_baseline_hw_capture_done" || true
setuphelfer_rescue_console_owner_transition "tui_owned" "autocapture_done" || true
if [[ -f "$OWNER_JSON" ]]; then
  setuphelfer_rescue_mirror_evidence_file "$OWNER_JSON" "setuphelfer/evidence/boot/console-ownership.json" 2>/dev/null || true
fi

touch "$DONE_FLAG" 2>/dev/null || true
sync 2>/dev/null || true
echo "tui_baseline_autocapture_done diag_rc=${diag_rc} hw_rc=${hw_rc} hw_status=${hw_status}"
exit 0
