#!/usr/bin/env bash
# Profile-aware runtime deploy gate (read-only). Runs base gate then profile checks.
#
# Exit codes:
#   0  OK
#   17 install_profile_missing
#   18 profile_manifest_mismatch
#   19 forbidden_api_path_visible / profile_gate_red
#   20 required_api_path_missing
#   21 public_exposure_blocked
#   30 unknown
#   (inherits 10-16 from check-runtime-deploy-gate.sh)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_GATE="$REPO_ROOT/scripts/check-runtime-deploy-gate.sh"
EVAL_PY="$REPO_ROOT/scripts/runtime_profile_deploy_gate_eval.py"
BASE_URL="${SETUPHELFER_VERSION_URL:-http://127.0.0.1:8000}"

log() { printf '%s\n' "$*" >&2; }

if [[ ! -x "$BASE_GATE" ]]; then
  log "check-runtime-profile-deploy-gate: missing $BASE_GATE"
  exit 30
fi

"$BASE_GATE" || ec=$?
ec=${ec:-0}
if [[ "$ec" -ne 0 ]]; then
  log "check-runtime-profile-deploy-gate: base gate failed exit=$ec"
  exit "$ec"
fi

tmp_api="$(mktemp)"
tmp_oa="$(mktemp)"
trap 'rm -f "$tmp_api" "$tmp_oa"' EXIT

curl -fsS "${BASE_URL}/api/version" -o "$tmp_api" 2>/dev/null || {
  log "check-runtime-profile-deploy-gate: /api/version unreachable"
  exit 11
}

curl -fsS "${BASE_URL}/openapi.json" -o "$tmp_oa" 2>/dev/null || true

bind="${SETUPHELFER_BIND_ADDRESS:-127.0.0.1}"
set +e
python3 "$EVAL_PY" --api-version-file "$tmp_api" --openapi-file "$tmp_oa" --bind-address "$bind"
pec=$?
set -e

if [[ "$pec" -ne 0 ]]; then
  log "check-runtime-profile-deploy-gate: profile evaluator exit=$pec"
  exit "$pec"
fi

log "check-runtime-profile-deploy-gate: OK (base + profile)"
exit 0
