#!/usr/bin/env bash
# Controlled ISO build wrapper with persistent logging (operator-gated).
# Default: usage + gate preview only (Exit 20). No automatic build.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_ROOT="${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live"
LOG_DIR="${REPO_ROOT}/build/rescue/logs/controlled-iso-build"
SUMMARY_DIR="${REPO_ROOT}/docs/evidence/runtime-results/rescue"
LATEST_LOG="${LOG_DIR}/latest.log"
SUMMARY_JSON="${SUMMARY_DIR}/controlled_iso_build_latest_summary.json"

usage() {
  cat <<EOF
Usage: $0 [--operator-confirm-build]

Without flag: preview gates and log paths only (Exit 20).
With --operator-confirm-build: run ./auto/config and sudo lb build noauto.

Log paths:
  ${LATEST_LOG}
  ${LOG_DIR}/<timestamp>.log
  ${SUMMARY_JSON}

USB write, dd, mkfs, parted: FORBIDDEN in this script.
EOF
}

preview_gates() {
  echo "=== Rescue ISO build gate preview ==="
  "${REPO_ROOT}/scripts/check-runtime-deploy-gate.sh" || true
  "${REPO_ROOT}/scripts/rescue-live/validate-temp-runtime-bundle.sh" \
    "${REPO_ROOT}/build/rescue/temp-runtime/setuphelfer-rescue-runtime" 2>/dev/null || echo "WARN: temp bundle validator not ready"
  "${REPO_ROOT}/scripts/rescue-live/validate-controlled-live-build-tree.sh" \
    "${BUILD_ROOT}" 2>/dev/null || echo "WARN: build tree validator not ready"
  echo "Planned log: ${LATEST_LOG}"
  echo "Planned summary: ${SUMMARY_JSON}"
}

write_summary() {
  local started_at="$1" ended_at="$2" exit_code="$3" log_file="$4"
  mkdir -p "${SUMMARY_DIR}"
  local iso_found=false iso_path="" iso_size="" sha256=""
  if iso="$(find "${BUILD_ROOT}" -maxdepth 3 -type f -name '*.iso' 2>/dev/null | head -1)"; then
    if [[ -n "$iso" && -f "$iso" ]]; then
      iso_found=true
      iso_path="$iso"
      iso_size="$(stat -c '%s' "$iso" 2>/dev/null || echo "")"
      sha256="$(sha256sum "$iso" 2>/dev/null | awk '{print $1}' || echo "")"
    fi
  fi
  local status="failed"
  if [[ "$exit_code" -eq 0 && "$iso_found" == true ]]; then
    status="success"
  elif [[ "$exit_code" -eq 0 ]]; then
    status="review_required"
  fi
  python3 - "$SUMMARY_JSON" "$started_at" "$ended_at" "$exit_code" "$iso_found" "$iso_path" "$iso_size" "$sha256" "$status" "$log_file" <<'PY'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
started, ended = sys.argv[2], sys.argv[3]
exit_code = int(sys.argv[4])
iso_found = sys.argv[5] == "true"
iso_path, iso_size, sha256, status, log_file = sys.argv[6:11]
log_path = Path(log_file)
lines = []
if log_path.is_file():
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-120:]
body = {
    "controlled_iso_build_summary_schema_version": 1,
    "started_at": started,
    "ended_at": ended,
    "exit_code": exit_code,
    "status": status,
    "iso_found": iso_found,
    "iso_path": iso_path or None,
    "iso_size": int(iso_size) if iso_size.isdigit() else None,
    "sha256": sha256 or None,
    "last_120_lines": lines,
    "usb_write_allowed": False,
    "dd_executed": False,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"OK: summary written to {out}")
PY
}

if [[ "${1:-}" != "--operator-confirm-build" ]]; then
  usage
  preview_gates
  echo "Build not started — pass --operator-confirm-build for operator-gated build."
  exit 20
fi

mkdir -p "${LOG_DIR}"
TS="$(date -Is | tr ':' '-')"
STAMPED_LOG="${LOG_DIR}/${TS}.log"
STARTED_AT="$(date -Is)"

echo "START ${STARTED_AT}" | tee "${LATEST_LOG}" | tee "${STAMPED_LOG}"
cd "${BUILD_ROOT}"
./auto/config 2>&1 | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
set +e
sudo lb build noauto 2>&1 | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
LB_EXIT=$?
set -e
ENDED_AT="$(date -Is)"
echo "LB_EXIT=${LB_EXIT}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
write_summary "${STARTED_AT}" "${ENDED_AT}" "${LB_EXIT}" "${LATEST_LOG}"
exit "${LB_EXIT}"
