#!/usr/bin/env bash
# Controlled ISO build wrapper with persistent logging (operator-gated).
# Default: usage + gate preview only (Exit 20). No automatic build.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_ROOT="${REPO_ROOT}/build/rescue/live-build/setuphelfer-rescue-live"
PATH_PREFIX="${REPO_ROOT}/build/rescue/tool-compat/bin"
LOG_DIR="${REPO_ROOT}/build/rescue/logs/controlled-iso-build"
SUMMARY_DIR="${REPO_ROOT}/docs/evidence/runtime-results/rescue"
LATEST_LOG="${LOG_DIR}/latest.log"
SUMMARY_JSON="${SUMMARY_DIR}/controlled_iso_build_latest_summary.json"
POLICY_BLOCK_EXIT=30
POLICY_BLOCK_CODE="blocked_requires_operator_sudo_policy"
POLICY_BLOCK_HINT="Run this command from an operator terminal with sudo privileges or install the documented allowlisted policy."
ISOHYBRID_PREFLIGHT_EXIT=31
ISOHYBRID_PREFLIGHT_CODE="RESCUE-BUILD-ISOHYBRID-001"
ISOHYBRID_PREFLIGHT_HINT="Run scripts/rescue-live/prepare-controlled-live-build-tree.sh (adds config/package-lists/setuphelfer.list.binary with syslinux-utils). Optional host: sudo apt install syslinux-utils."

POLICY_GUARD_STATUS="unknown"
POLICY_EXECUTION_MODE="none"
POLICY_IS_TTY=false
POLICY_ALREADY_ROOT=false
POLICY_SUDO_AVAILABLE=false
POLICY_SUDO_NONINTERACTIVE=false

usage() {
  cat <<EOF
Usage: $0 [--operator-confirm-build]

Without flag: preview gates and log paths only (Exit 20).
With --operator-confirm-build: run the policy guard first, then ./auto/config
and the controlled lb build path with the project-local rsvg wrapper in PATH.

Log paths:
  ${LATEST_LOG}
  ${LOG_DIR}/<timestamp>.log
  ${SUMMARY_JSON}

USB write, dd, mkfs, parted: FORBIDDEN in this script.
EOF
}

binary_stage_preflight_ok() {
  local blist="${BUILD_ROOT}/config/package-lists/setuphelfer.list.binary"
  if [[ ! -f "$blist" ]]; then
    echo "${ISOHYBRID_PREFLIGHT_CODE}: missing ${blist}"
    echo "${ISOHYBRID_PREFLIGHT_HINT}"
    return 1
  fi
  if ! grep -qx 'syslinux-utils' "$blist"; then
    echo "${ISOHYBRID_PREFLIGHT_CODE}: ${blist} must contain syslinux-utils (isohybrid in lb binary chroot)"
    echo "${ISOHYBRID_PREFLIGHT_HINT}"
    return 1
  fi
  if ! command -v isohybrid >/dev/null 2>&1; then
    echo "WARN: host isohybrid not in PATH; binary stage uses chroot package list (syslinux-utils)."
  fi
  return 0
}

preview_gates() {
  echo "=== Rescue ISO build gate preview ==="
  binary_stage_preflight_ok || echo "WARN: binary-stage preflight would block build"
  "${REPO_ROOT}/scripts/check-runtime-deploy-gate.sh" || true
  "${REPO_ROOT}/scripts/rescue-live/validate-temp-runtime-bundle.sh" \
    "${REPO_ROOT}/build/rescue/temp-runtime/setuphelfer-rescue-runtime" 2>/dev/null || echo "WARN: temp bundle validator not ready"
  "${REPO_ROOT}/scripts/rescue-live/validate-controlled-live-build-tree.sh" \
    "${BUILD_ROOT}" 2>/dev/null || echo "WARN: build tree validator not ready"
  echo "Planned log: ${LATEST_LOG}"
  echo "Planned summary: ${SUMMARY_JSON}"
  echo "Required PATH prefix: ${PATH_PREFIX}"
  echo "Policy guard: root OR real TTY operator sudo OR sudo -n allowlist"
  echo "Planned command (root): env PATH=\"${PATH_PREFIX}:\$PATH\" lb build noauto"
  echo "Planned command (sudo): sudo env PATH=\"${PATH_PREFIX}:\$PATH\" lb build noauto"
}

detect_policy_context() {
  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    POLICY_ALREADY_ROOT=true
  fi
  if [[ -t 0 && -t 1 ]]; then
    POLICY_IS_TTY=true
  fi
  if command -v sudo >/dev/null 2>&1; then
    POLICY_SUDO_AVAILABLE=true
    if sudo -n true >/dev/null 2>&1; then
      POLICY_SUDO_NONINTERACTIVE=true
    fi
  fi
}

policy_guard_ok() {
  detect_policy_context
  if [[ "${POLICY_ALREADY_ROOT}" == true ]]; then
    POLICY_GUARD_STATUS="ready"
    POLICY_EXECUTION_MODE="already_root"
    return 0
  fi
  if [[ "${POLICY_IS_TTY}" == true && "${POLICY_SUDO_AVAILABLE}" == true ]]; then
    POLICY_GUARD_STATUS="ready"
    POLICY_EXECUTION_MODE="manual_operator_terminal"
    return 0
  fi
  if [[ "${POLICY_SUDO_NONINTERACTIVE}" == true ]]; then
    POLICY_GUARD_STATUS="ready"
    POLICY_EXECUTION_MODE="sudoers_allowlist_design"
    return 0
  fi
  POLICY_GUARD_STATUS="blocked"
  POLICY_EXECUTION_MODE="blocked_requires_operator_sudo_policy"
  return 1
}

write_summary() {
  local started_at="$1" ended_at="$2" exit_code="$3" log_file="$4" error_code="$5" next_action="$6" build_started="$7"
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
  elif [[ "$exit_code" -eq "${POLICY_BLOCK_EXIT}" ]]; then
    status="blocked"
  elif [[ "$exit_code" -eq 0 ]]; then
    status="review_required"
  fi
  python3 - "$SUMMARY_JSON" "$started_at" "$ended_at" "$exit_code" "$iso_found" "$iso_path" "$iso_size" "$sha256" "$status" "$log_file" "$error_code" "$next_action" "$build_started" "$POLICY_GUARD_STATUS" "$POLICY_EXECUTION_MODE" "$POLICY_IS_TTY" "$POLICY_ALREADY_ROOT" "$POLICY_SUDO_NONINTERACTIVE" <<'PY'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
started, ended = sys.argv[2], sys.argv[3]
exit_code = int(sys.argv[4])
iso_found = sys.argv[5] == "true"
iso_path, iso_size, sha256, status, log_file = sys.argv[6:11]
error_code, next_action, build_started = sys.argv[11:14]
policy_guard_status, execution_mode, is_tty, already_root, sudo_noninteractive = sys.argv[14:19]
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
    "error_code": error_code or None,
    "next_action": next_action or None,
    "policy_guard_status": policy_guard_status,
    "execution_mode": execution_mode,
    "build_started": build_started == "true",
    "no_build_executed": build_started != "true",
    "policy_context": {
        "is_tty": is_tty == "true",
        "already_root": already_root == "true",
        "sudo_noninteractive": sudo_noninteractive == "true",
    },
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
ERROR_CODE=""
NEXT_ACTION=""
BUILD_STARTED=false

echo "START ${STARTED_AT}" | tee "${LATEST_LOG}" | tee "${STAMPED_LOG}"
if ! policy_guard_ok; then
  echo "POLICY_GUARD_STATUS=${POLICY_GUARD_STATUS}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  echo "POLICY_EXECUTION_MODE=${POLICY_EXECUTION_MODE}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  echo "POLICY_IS_TTY=${POLICY_IS_TTY}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  echo "POLICY_ALREADY_ROOT=${POLICY_ALREADY_ROOT}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  echo "POLICY_SUDO_NONINTERACTIVE=${POLICY_SUDO_NONINTERACTIVE}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  echo "${POLICY_BLOCK_CODE}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  echo "${POLICY_BLOCK_HINT}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  LB_EXIT="${POLICY_BLOCK_EXIT}"
  ERROR_CODE="${POLICY_BLOCK_CODE}"
  NEXT_ACTION="manual_operator_terminal_required"
  ENDED_AT="$(date -Is)"
  echo "LB_EXIT=${LB_EXIT}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  write_summary "${STARTED_AT}" "${ENDED_AT}" "${LB_EXIT}" "${LATEST_LOG}" "${ERROR_CODE}" "${NEXT_ACTION}" "${BUILD_STARTED}"
  exit "${LB_EXIT}"
fi
echo "POLICY_GUARD_STATUS=${POLICY_GUARD_STATUS}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
echo "POLICY_EXECUTION_MODE=${POLICY_EXECUTION_MODE}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
if ! binary_stage_preflight_ok; then
  echo "${ISOHYBRID_PREFLIGHT_HINT}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  LB_EXIT="${ISOHYBRID_PREFLIGHT_EXIT}"
  ERROR_CODE="${ISOHYBRID_PREFLIGHT_CODE}"
  NEXT_ACTION="prepare_binary_package_list_and_retry"
  ENDED_AT="$(date -Is)"
  echo "LB_EXIT=${LB_EXIT}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  write_summary "${STARTED_AT}" "${ENDED_AT}" "${LB_EXIT}" "${LATEST_LOG}" "${ERROR_CODE}" "${NEXT_ACTION}" "${BUILD_STARTED}"
  exit "${LB_EXIT}"
fi
cd "${BUILD_ROOT}"
env PATH="${PATH_PREFIX}:${PATH}" ./auto/config 2>&1 | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
BUILD_STARTED=true
set +e
if [[ "${POLICY_ALREADY_ROOT}" == true ]]; then
  env PATH="${PATH_PREFIX}:${PATH}" lb build noauto 2>&1 | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
else
  sudo env PATH="${PATH_PREFIX}:${PATH}" lb build noauto 2>&1 | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
fi
LB_EXIT=$?
set -e
ENDED_AT="$(date -Is)"
if [[ -z "$ERROR_CODE" ]] && grep -q 'isohybrid: not found' "${LATEST_LOG}" 2>/dev/null; then
  ERROR_CODE="${ISOHYBRID_PREFLIGHT_CODE}"
  NEXT_ACTION="prepare_binary_package_list_and_retry"
fi
echo "LB_EXIT=${LB_EXIT}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
write_summary "${STARTED_AT}" "${ENDED_AT}" "${LB_EXIT}" "${LATEST_LOG}" "${ERROR_CODE}" "${NEXT_ACTION}" "${BUILD_STARTED}"
exit "${LB_EXIT}"
