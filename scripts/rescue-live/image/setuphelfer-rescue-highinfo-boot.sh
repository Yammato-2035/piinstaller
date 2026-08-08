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
FORENSIC_DIR="${SETUPHELFER_STARTX_FORENSIC_DIR:-/run/setuphelfer/startx-forensic}"

_highinfo_mirror_evidence() {
  local src="$1"
  local rel="$2"
  [[ -e "$src" ]] || return 0
  if declare -F setuphelfer_rescue_mirror_evidence_file >/dev/null 2>&1; then
    setuphelfer_rescue_mirror_evidence_file "$src" "$rel" 2>/dev/null || true
  fi
  # Also copy tree into SETUP_LOGS evidence path when available.
  local logs_root=""
  for cand in /run/setuphelfer/esp-rw/setuphelfer/evidence /media/*/SETUP_LOGS*/setuphelfer/evidence; do
    [[ -d "$cand" ]] && logs_root="$cand" && break
  done
  if [[ -n "$logs_root" ]]; then
    mkdir -p "$(dirname "${logs_root}/${rel}")" 2>/dev/null || true
    if [[ -d "$src" ]]; then
      mkdir -p "${logs_root}/${rel}" 2>/dev/null || true
      cp -a "$src"/. "${logs_root}/${rel}/" 2>/dev/null || true
    else
      cp -a "$src" "${logs_root}/${rel}" 2>/dev/null || true
    fi
  fi
}

setuphelfer_rescue_write_boot_state "highinfo_boot_start" || true

XORG_STATUS="skipped"
XORG_READY=0
STARTX_INVOKED=0
STARTX_EXIT_CODE=""
XORG_LOG_PATH=""
XORG_LOG_FOUND=0
if setuphelfer_rescue_xorg_probe_active 2>/dev/null; then
  setuphelfer_rescue_write_boot_state "highinfo_xorg_probe_start" || true
  if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic.sh" ]]; then
    STARTX_INVOKED=1
    "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic.sh"
    STARTX_EXIT_CODE=$?
    if [[ "${STARTX_EXIT_CODE}" -eq 0 ]]; then
      XORG_STATUS="ok"
      XORG_READY=1
    else
      XORG_STATUS="failed"
    fi
  elif [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic" ]]; then
    STARTX_INVOKED=1
    "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic"
    STARTX_EXIT_CODE=$?
    if [[ "${STARTX_EXIT_CODE}" -eq 0 ]]; then
      XORG_STATUS="ok"
      XORG_READY=1
    else
      XORG_STATUS="failed"
    fi
  else
    XORG_STATUS="skipped"
    STARTX_INVOKED=0
  fi
  # Always return console to TUI ownership after probe.
  setuphelfer_rescue_restore_tty1_after_gui_fail 2>/dev/null || true
  setuphelfer_rescue_console_owner_transition "tui_owned" "highinfo_xorg_probe_done" || true
  setuphelfer_rescue_write_boot_state "highinfo_xorg_probe_${XORG_STATUS}" || true
  # Persist forensic artifacts (previously only under /run → lost after reboot).
  _highinfo_mirror_evidence "${FORENSIC_DIR}" "boot/startx-forensic"
  if [[ -f /run/setuphelfer/Xorg.forensic.log ]]; then
    XORG_LOG_PATH="/run/setuphelfer/Xorg.forensic.log"
    XORG_LOG_FOUND=1
    _highinfo_mirror_evidence /run/setuphelfer/Xorg.forensic.log "boot/Xorg.forensic.log"
  elif [[ -f "${FORENSIC_DIR}/Xorg.forensic.log" ]]; then
    XORG_LOG_PATH="${FORENSIC_DIR}/Xorg.forensic.log"
    XORG_LOG_FOUND=1
    _highinfo_mirror_evidence "${FORENSIC_DIR}/Xorg.forensic.log" "boot/Xorg.forensic.log"
  fi
fi

# Persist a compact stage summary + structured Xorg evidence for host-side import.
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
  "startx_invoked": bool(${STARTX_INVOKED}),
  "startx_exit_code": (None if ${STARTX_EXIT_CODE@Q} == "" else int(${STARTX_EXIT_CODE@Q})),
  "xorg_log_found": bool(${XORG_LOG_FOUND}),
  "xorg_log_path": (${XORG_LOG_PATH@Q} or None),
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
# Structured Xorg evidence record + SETUP_LOGS mirror (009).
try:
    import sys
    for p in ("/opt/setuphelfer-rescue/backend", "/usr/local/lib/setuphelfer/backend"):
        if p not in sys.path and os.path.isdir(p):
            sys.path.insert(0, p)
    from rescue.highinfo_xorg_evidence import (
        build_highinfo_xorg_evidence_record,
        write_and_mirror_highinfo_xorg_evidence,
    )
    startx_invoked = bool(${STARTX_INVOKED})
    exit_raw = ${STARTX_EXIT_CODE@Q}
    exit_code = None if exit_raw == "" else int(exit_raw)
    reason = None
    if not startx_invoked:
        reason = "startx_not_invoked"
    elif ${XORG_STATUS@Q} == "failed":
        reason = "xorg_probe_failed"
    rec = build_highinfo_xorg_evidence_record(
        boot_id=${BOOT_ID@Q},
        run_id=${RUN_ID@Q},
        startx_invoked=startx_invoked,
        startx_exit_code=exit_code,
        xorg_log_found=bool(${XORG_LOG_FOUND}),
        xorg_log_path=(${XORG_LOG_PATH@Q} or None),
        xorg_probe_status=${XORG_STATUS@Q},
        reason=reason,
    )
    write_and_mirror_highinfo_xorg_evidence(
        rec,
        local_path=Path(${EVIDENCE_DIR@Q}) / "xorg_probe_evidence.json",
    )
except Exception as exc:
    Path(${EVIDENCE_DIR@Q}, "xorg_probe_evidence_error.txt").write_text(str(exc) + "\n")
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
_highinfo_mirror_evidence "${EVIDENCE_DIR}/highinfo_stage_summary.json" "boot/highinfo/highinfo_stage_summary.json"
_highinfo_mirror_evidence "${EVIDENCE_DIR}/xorg_probe_evidence.json" "boot/highinfo/xorg_probe_evidence.json"
_highinfo_mirror_evidence "${EVIDENCE_DIR}/high_information_boot_result.json" "boot/highinfo/high_information_boot_result.json"
_highinfo_mirror_evidence "${EVIDENCE_DIR}/high_information_boot_error.txt" "boot/highinfo/high_information_boot_error.txt"
_highinfo_mirror_evidence "${EVIDENCE_DIR}" "boot/highinfo"
echo "highinfo_boot_done xorg_probe=${XORG_STATUS} startx_invoked=${STARTX_INVOKED} chromium=false tui_survived=true"
exit 0
