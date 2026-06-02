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
RESCUE_BUILD_PROFILE="${SETUPHELFER_RESCUE_BUILD_PROFILE:-standard}"
RUN_ID=""
POLICY_BLOCK_EXIT=30
POLICY_BLOCK_CODE="blocked_requires_operator_sudo_policy"
POLICY_BLOCK_HINT="Run this command from an operator terminal with sudo privileges or install the documented allowlisted policy."
ISOHYBRID_PREFLIGHT_EXIT=31
ISOHYBRID_PREFLIGHT_CODE="RESCUE-BUILD-ISOHYBRID-001"
ISOHYBRID_PREFLIGHT_HINT="Run prepare-controlled-live-build-tree.sh (syslinux-utils in setuphelfer.list.chroot). Then full clean (chroot+cache) and rebuild — list.binary alone does not install into the chroot."
ZSYNC_STALE_EXIT=32
ZSYNC_STALE_CODE="RESCUE-BUILD-ZSYNC-STALE-001"
ZSYNC_STALE_HINT="Remove stale binary.hybrid.iso.zsync* in BUILD_TREE or run prepare + ./auto/clean; rescue uses --zsync false."
PERMISSION_PREFLIGHT_EXIT=34
PERMISSION_PREFLIGHT_CODE="rescue_iso_build.permission_denied_dot_build"
PERMISSION_PREFLIGHT_HINT="Run ./scripts/rescue-live/clean-controlled-live-build-tree.sh --dry-run then sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean"
RESCUE_ISO_BASENAMES=(binary.hybrid.iso binary.iso)

POLICY_GUARD_STATUS="unknown"
POLICY_EXECUTION_MODE="none"
POLICY_IS_TTY=false
POLICY_ALREADY_ROOT=false
POLICY_SUDO_AVAILABLE=false
POLICY_SUDO_NONINTERACTIVE=false

usage() {
  cat <<EOF
Usage: $0 [--operator-confirm-build] [--profile standard|developer|developer-qemu] [--run-id ID]

Without flag: preview gates and log paths only (Exit 20).
With --operator-confirm-build: run the policy guard first, then ./auto/config
and the controlled lb build path with the project-local rsvg wrapper in PATH.

Profiles:
  standard       — release rescue ISO (defensive bootappend)
  developer      — dev agent enabled in tree
  developer-qemu — serial ttyS0 + QEMU autopilot hook (prepare with same profile first)

Set profile via --profile or SETUPHELFER_RESCUE_BUILD_PROFILE before invoking.
If build log shows profile=standard but you need developer-qemu: STOP and re-run with --profile developer-qemu.

Log paths:
  ${LATEST_LOG}
  ${LOG_DIR}/<timestamp>.log
  ${SUMMARY_JSON}

USB write, dd, mkfs, parted: FORBIDDEN in this script.
EOF
}

permission_preflight_ok() {
  local perm_json
  perm_json="$(cd "$REPO_ROOT" && BUILD_ROOT="$BUILD_ROOT" PYTHONPATH="${REPO_ROOT}/backend:${REPO_ROOT}" python3 - <<'PY'
import json
import os
from pathlib import Path
from core.rescue_iso_build_permission_policy import assess_build_tree_permissions
build_root = Path(os.environ["BUILD_ROOT"])
print(json.dumps(assess_build_tree_permissions(build_root)))
PY
)"
  local blocked
  blocked="$(python3 -c "import json,sys; p=json.loads(sys.argv[1]); print('yes' if p.get('operator_fix_required') else 'no')" "$perm_json")"
  if [[ "$blocked" == "yes" ]]; then
    echo "${PERMISSION_PREFLIGHT_CODE}: build tree permission preflight blocked"
    echo "$perm_json" | python3 -m json.tool 2>/dev/null || echo "$perm_json"
    echo "${PERMISSION_PREFLIGHT_HINT}"
    return 1
  fi
  return 0
}

binary_stage_preflight_ok() {
  local clist="${BUILD_ROOT}/config/package-lists/setuphelfer.list.chroot"
  if [[ ! -f "$clist" ]]; then
    echo "${ISOHYBRID_PREFLIGHT_CODE}: missing ${clist}"
    echo "${ISOHYBRID_PREFLIGHT_HINT}"
    return 1
  fi
  if ! grep -qx 'syslinux-utils' "$clist"; then
    echo "${ISOHYBRID_PREFLIGHT_CODE}: ${clist} must contain syslinux-utils (lb_binary_iso runs isohybrid in chroot; list.binary is ISO pool only)"
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
  local candidate base
  for base in "${RESCUE_ISO_BASENAMES[@]}"; do
    candidate="${BUILD_ROOT}/${base}"
    if [[ -f "$candidate" ]]; then
      iso_found=true
      iso_path="$candidate"
      iso_size="$(stat -c '%s' "$candidate" 2>/dev/null || echo "")"
      sha256="$(sha256sum "$candidate" 2>/dev/null | awk '{print $1}' || echo "")"
      break
    fi
  done
  if [[ "$iso_found" != true ]]; then
    if iso="$(find "${BUILD_ROOT}" -maxdepth 3 -type f \( -name '*.iso' -o -name '*.hybrid.iso' \) 2>/dev/null | head -1)"; then
      if [[ -n "$iso" && -f "$iso" ]]; then
        iso_found=true
        iso_path="$iso"
        iso_size="$(stat -c '%s' "$iso" 2>/dev/null || echo "")"
        sha256="$(sha256sum "$iso" 2>/dev/null | awk '{print $1}' || echo "")"
      fi
    fi
  fi
  local status="failed"
  if [[ "$exit_code" -eq 0 && "$iso_found" == true ]]; then
    status="success"
  elif [[ "$exit_code" -ne 0 && "$iso_found" == true ]]; then
    status="review_required"
  elif [[ "$exit_code" -eq "${POLICY_BLOCK_EXIT}" ]]; then
    status="blocked"
  elif [[ "$exit_code" -eq 0 ]]; then
    status="review_required"
  fi
  python3 - "$SUMMARY_JSON" "$started_at" "$ended_at" "$exit_code" "$iso_found" "$iso_path" "$iso_size" "$sha256" "$status" "$log_file" "$error_code" "$next_action" "$build_started" "$POLICY_GUARD_STATUS" "$POLICY_EXECUTION_MODE" "$POLICY_IS_TTY" "$POLICY_ALREADY_ROOT" "$POLICY_SUDO_NONINTERACTIVE" "$RESCUE_BUILD_PROFILE" "$RUN_ID" <<'PY'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
started, ended = sys.argv[2], sys.argv[3]
exit_code = int(sys.argv[4])
iso_found = sys.argv[5] == "true"
iso_path, iso_size, sha256, status, log_file = sys.argv[6:11]
error_code, next_action, build_started = sys.argv[11:14]
policy_guard_status, execution_mode, is_tty, already_root, sudo_noninteractive = sys.argv[14:19]
rescue_build_profile = sys.argv[19] if len(sys.argv) > 19 else None
run_id = sys.argv[20] if len(sys.argv) > 20 else None
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
    "rescue_build_profile": rescue_build_profile,
    "run_id": run_id,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"OK: summary written to {out}")
PY
}

if [[ "${1:-}" != "--operator-confirm-build" ]]; then
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --profile)
        RESCUE_BUILD_PROFILE="${2:-standard}"
        shift 2
        ;;
      --run-id)
        RUN_ID="${2:-}"
        shift 2
        ;;
      *)
        shift
        ;;
    esac
  done
  usage
  preview_gates
  echo "Build not started — pass --operator-confirm-build for operator-gated build."
  echo "Profile: ${RESCUE_BUILD_PROFILE}"
  exit 20
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --operator-confirm-build)
      shift
      ;;
    --profile)
      RESCUE_BUILD_PROFILE="${2:-standard}"
      shift 2
      ;;
    --run-id)
      RUN_ID="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

export SETUPHELFER_RESCUE_BUILD_PROFILE="${RESCUE_BUILD_PROFILE}"
if [[ -z "$RUN_ID" ]]; then
  RUN_ID="rescue_developer_iso_$(date -u +%Y%m%d_%H%M%S)"
fi

if [[ "${RESCUE_BUILD_PROFILE}" == "developer" || "${RESCUE_BUILD_PROFILE}" == "developer-qemu" ]]; then
  if [[ ! -f "${BUILD_ROOT}/config/includes.chroot/etc/setuphelfer/setuphelfer-dev-agent.env" ]]; then
    echo "ERROR: ${RESCUE_BUILD_PROFILE} profile not in build tree — run SETUPHELFER_RESCUE_BUILD_PROFILE=${RESCUE_BUILD_PROFILE} prepare-controlled-live-build-tree.sh first" | tee -a "${LATEST_LOG}" 2>/dev/null || true
    exit 33
  fi
fi

mkdir -p "${LOG_DIR}"
TS="$(date -Is | tr ':' '-')"
STAMPED_LOG="${LOG_DIR}/${TS}.log"
STARTED_AT="$(date -Is)"
ERROR_CODE=""
NEXT_ACTION=""
BUILD_STARTED=false

echo "START ${STARTED_AT} profile=${RESCUE_BUILD_PROFILE} run_id=${RUN_ID}" | tee "${LATEST_LOG}" | tee "${STAMPED_LOG}"
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
if ! permission_preflight_ok; then
  echo "${PERMISSION_PREFLIGHT_HINT}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  LB_EXIT="${PERMISSION_PREFLIGHT_EXIT}"
  ERROR_CODE="${PERMISSION_PREFLIGHT_CODE}"
  NEXT_ACTION="run_clean_controlled_live_build_tree"
  ENDED_AT="$(date -Is)"
  echo "LB_EXIT=${LB_EXIT}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
  write_summary "${STARTED_AT}" "${ENDED_AT}" "${LB_EXIT}" "${LATEST_LOG}" "${ERROR_CODE}" "${NEXT_ACTION}" "${BUILD_STARTED}"
  exit "${LB_EXIT}"
fi
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
if [[ -z "$ERROR_CODE" ]] && grep -qE 'xz:.*\.zsync\.xz:.*(existiert bereits|File exists)' "${LATEST_LOG}" 2>/dev/null; then
  ERROR_CODE="${ZSYNC_STALE_CODE}"
  NEXT_ACTION="remove_stale_zsync_artifacts_and_retry"
fi
echo "LB_EXIT=${LB_EXIT}" | tee -a "${LATEST_LOG}" | tee -a "${STAMPED_LOG}"
write_summary "${STARTED_AT}" "${ENDED_AT}" "${LB_EXIT}" "${LATEST_LOG}" "${ERROR_CODE}" "${NEXT_ACTION}" "${BUILD_STARTED}"
exit "${LB_EXIT}"
