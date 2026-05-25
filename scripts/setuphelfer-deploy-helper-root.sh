#!/usr/bin/env bash
set -euo pipefail

ALLOWED_WORKSPACE="/home/volker/piinstaller"
RUNTIME_PATH="/opt/setuphelfer"
LOCK_FILE="/run/setuphelfer-deploy.lock"
JOB_DIR="/var/lib/setuphelfer/deploy-jobs"
LOG_FILE="${JOB_DIR}/latest.log"
STATE_FILE="${JOB_DIR}/latest.json"
HELPER_UNIT="setuphelfer-deploy-helper.service"

WORKSPACE=""
JOB_ID="deploy-$(date -u +%Y%m%dT%H%M%SZ)-$$"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ENDED_AT=""
HEAD_BEFORE=""
DEPLOY_EXIT=""
GATE_BEFORE=""
GATE_AFTER=""
BACKEND_SERVICE_STATE=""
FRONTEND_SERVICE_STATE=""
FINAL_STATUS="failed"
FINAL_SUMMARY="helper_not_started"

usage() {
  echo "Usage: $0 --workspace ${ALLOWED_WORKSPACE}" >&2
  exit 2
}

git_workspace() {
  git -c "safe.directory=${WORKSPACE}" -C "$WORKSPACE" "$@"
}

write_state() {
  local status="$1"
  local summary="$2"
  python3 - "$STATE_FILE" "$JOB_ID" "$status" "$STARTED_AT" "${ENDED_AT:-}" "$WORKSPACE" "$RUNTIME_PATH" \
    "$HEAD_BEFORE" "${DEPLOY_EXIT:-}" "${GATE_BEFORE:-}" "${GATE_AFTER:-}" \
    "${BACKEND_SERVICE_STATE:-}" "${FRONTEND_SERVICE_STATE:-}" "$summary" "$HELPER_UNIT" <<'PY'
import json
import sys
from pathlib import Path

(
    state_file,
    job_id,
    status,
    started_at,
    ended_at,
    workspace,
    runtime_path,
    head_before,
    deploy_exit,
    gate_before,
    gate_after,
    backend_state,
    frontend_state,
    summary,
    helper_unit,
) = sys.argv[1:]

def to_int(value: str):
    text = (value or "").strip()
    if not text:
        return None
    if text.startswith("-") and text[1:].isdigit():
        return int(text)
    if text.isdigit():
        return int(text)
    return None

payload = {
    "id": job_id,
    "status": status,
    "started_at": started_at or None,
    "ended_at": ended_at or None,
    "workspace": workspace,
    "runtime_path": runtime_path,
    "head_before": head_before or None,
    "deploy_exit_code": to_int(deploy_exit),
    "exit_code": to_int(deploy_exit),
    "runtime_gate_exit_before": to_int(gate_before),
    "runtime_gate_exit_after": to_int(gate_after),
    "services": {
        "setuphelfer-backend.service": backend_state or None,
        "setuphelfer.service": frontend_state or None,
    },
    "summary": summary,
    "helper_unit": helper_unit,
}

path = Path(state_file)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
PY
}

finish() {
  local rc="${1:-1}"
  ENDED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [[ -z "${FINAL_SUMMARY:-}" ]]; then
    FINAL_SUMMARY="helper_finished"
  fi
  if [[ -z "${DEPLOY_EXIT:-}" ]]; then
    DEPLOY_EXIT="$rc"
  fi
  write_state "$FINAL_STATUS" "$FINAL_SUMMARY" || true
  rm -f "$LOCK_FILE"
  exit "$rc"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      shift
      [[ $# -gt 0 ]] || usage
      WORKSPACE="$1"
      ;;
    *)
      usage
      ;;
  esac
  shift
done

[[ -n "$WORKSPACE" ]] || usage

if [[ "$(id -u)" -ne 0 ]]; then
  echo "setuphelfer-deploy-helper-root: must run as root" >&2
  exit 1
fi

if [[ "$WORKSPACE" != "$ALLOWED_WORKSPACE" ]]; then
  echo "setuphelfer-deploy-helper-root: workspace not allowlisted" >&2
  exit 3
fi

mkdir -p "$JOB_DIR"
touch "$LOG_FILE"

[[ -d "$WORKSPACE" ]] || { echo "setuphelfer-deploy-helper-root: workspace missing" >&2; exit 3; }
git_workspace rev-parse --show-toplevel >/dev/null 2>&1 || {
  echo "setuphelfer-deploy-helper-root: workspace is not a git repo" >&2
  exit 3
}
[[ -f "$WORKSPACE/scripts/deploy-to-opt.sh" ]] || {
  echo "setuphelfer-deploy-helper-root: deploy-to-opt.sh missing" >&2
  exit 3
}

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  FINAL_STATUS="blocked"
  FINAL_SUMMARY="parallel_deploy_locked"
  write_state "$FINAL_STATUS" "$FINAL_SUMMARY"
  echo "setuphelfer-deploy-helper-root: another deploy is already running" >&2
  exit 4
fi

trap 'finish $?' EXIT
exec > >(tee -a "$LOG_FILE") 2>&1

echo "[deploy-helper] job_id=${JOB_ID}"
echo "[deploy-helper] workspace=${WORKSPACE}"
echo "[deploy-helper] runtime_path=${RUNTIME_PATH}"

HEAD_BEFORE="$(git_workspace rev-parse --short HEAD 2>/dev/null || true)"
set +e
(cd "$WORKSPACE" && ./scripts/check-runtime-deploy-gate.sh)
GATE_BEFORE="$?"
set -e

FINAL_STATUS="running"
FINAL_SUMMARY="deploy_started"
write_state "$FINAL_STATUS" "$FINAL_SUMMARY"

echo "[deploy-helper] head_before=${HEAD_BEFORE:-unknown}"
echo "[deploy-helper] runtime_gate_before=${GATE_BEFORE}"

set +e
"$WORKSPACE/scripts/deploy-to-opt.sh" "$WORKSPACE"
DEPLOY_EXIT="$?"
set -e

BACKEND_SERVICE_STATE="$(systemctl is-active setuphelfer-backend.service || true)"
FRONTEND_SERVICE_STATE="$(systemctl is-active setuphelfer.service || true)"

set +e
(cd "$WORKSPACE" && ./scripts/check-runtime-deploy-gate.sh)
GATE_AFTER="$?"
set -e

if [[ "$DEPLOY_EXIT" == "0" && "$GATE_AFTER" == "0" ]]; then
  FINAL_STATUS="success"
  FINAL_SUMMARY="deploy_completed_and_runtime_gate_green"
else
  FINAL_STATUS="failed"
  FINAL_SUMMARY="deploy_or_runtime_gate_failed"
fi

echo "[deploy-helper] deploy_exit=${DEPLOY_EXIT}"
echo "[deploy-helper] backend_service=${BACKEND_SERVICE_STATE:-unknown}"
echo "[deploy-helper] frontend_service=${FRONTEND_SERVICE_STATE:-unknown}"
echo "[deploy-helper] runtime_gate_after=${GATE_AFTER}"
echo "[deploy-helper] final_status=${FINAL_STATUS}"
