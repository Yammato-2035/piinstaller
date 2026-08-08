#!/usr/bin/env bash
# PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007 — high-information boot stage runner.
# Runs after TUI-baseline autocapture. Controlled Xorg probe may run; Chromium never.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh" 2>/dev/null || true

if ! setuphelfer_rescue_highinfo_active 2>/dev/null; then
  echo "highinfo_boot_skipped_not_active"
  exit 0
fi

RUN_ID="${SETUPHELFER_RUN_ID:-unknown}"
BOOT_ID="$(cat /proc/sys/kernel/random/boot_id 2>/dev/null || echo unknown)"
EVIDENCE_DIR="${SETUPHELFER_RESCUE_EVIDENCE_DIR:-/run/setuphelfer/evidence}/highinfo"
mkdir -p "${EVIDENCE_DIR}" 2>/dev/null || true

setuphelfer_rescue_write_boot_state "highinfo_boot_start" || true

XORG_STATUS="skipped"
XORG_READY=0
if setuphelfer_rescue_xorg_probe_active 2>/dev/null; then
  setuphelfer_rescue_write_boot_state "highinfo_xorg_probe_start" || true
  if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic.sh" ]]; then
    if "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic.sh"; then
      XORG_STATUS="ok"
      XORG_READY=1
    else
      XORG_STATUS="failed"
    fi
  elif [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic" ]]; then
    if "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic"; then
      XORG_STATUS="ok"
      XORG_READY=1
    else
      XORG_STATUS="failed"
    fi
  else
    XORG_STATUS="skipped"
  fi
  # Always return console to TUI ownership after probe.
  setuphelfer_rescue_restore_tty1_after_gui_fail 2>/dev/null || true
  setuphelfer_rescue_console_owner_transition "tui_owned" "highinfo_xorg_probe_done" || true
  setuphelfer_rescue_write_boot_state "highinfo_xorg_probe_${XORG_STATUS}" || true
fi

# Persist a compact stage summary for host-side evidence import.
python3 - <<PY 2>/dev/null || true
import json, os, time
from pathlib import Path
out = Path(${EVIDENCE_DIR@Q}) / "highinfo_stage_summary.json"
payload = {
  "schema_version": 1,
  "campaign": "PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007",
  "profile": "ASUS-TUI-BASELINE-HIGHINFO",
  "run_id": ${RUN_ID@Q},
  "boot_id": ${BOOT_ID@Q},
  "xorg_probe": ${XORG_STATUS@Q},
  "xorg_ready": bool(${XORG_READY}),
  "chromium_started": False,
  "tui_survived": True,
  "writes_to_internal_nvme": False,
  "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
try:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
except OSError:
    pass
# Best-effort orchestrator record (injectable runners omitted → skip network/xorg in-process).
try:
    import sys
    for p in ("/opt/setuphelfer-rescue/backend", "/usr/local/lib/setuphelfer/backend"):
        if p not in sys.path and os.path.isdir(p):
            sys.path.insert(0, p)
    from rescue.high_information_boot_orchestrator import run_high_information_boot
    def _xorg():
        return {"status": ${XORG_STATUS@Q}, "exit_code": 0 if ${XORG_READY} else 1, "xorg_ready": bool(${XORG_READY}), "evidence": {}}
    result = run_high_information_boot(
        run_id=${RUN_ID@Q},
        boot_id=${BOOT_ID@Q},
        boot_profile="ASUS-TUI-BASELINE-HIGHINFO",
        stage_runners={"controlled_drm_xorg_probe": _xorg},
        context={"xorg_ready": bool(${XORG_READY})},
    )
    Path(${EVIDENCE_DIR@Q}, "high_information_boot_result.json").write_text(json.dumps(result, indent=2) + "\n")
except Exception as exc:
    Path(${EVIDENCE_DIR@Q}, "high_information_boot_error.txt").write_text(str(exc) + "\n")
PY

setuphelfer_rescue_write_boot_state "highinfo_boot_done" || true
echo "highinfo_boot_done xorg_probe=${XORG_STATUS} chromium=false tui_survived=true"
exit 0
