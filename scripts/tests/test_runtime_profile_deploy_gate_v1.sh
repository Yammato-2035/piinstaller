#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
EVAL="$REPO_ROOT/scripts/runtime_profile_deploy_gate_eval.py"
fail() { echo "FAIL: $*" >&2; exit 1; }

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

cat >"$tmp" <<'JSON'
{
  "install_profile": "release",
  "manifest_profile": "release",
  "profile_gate_status": "green",
  "profile_gate_errors": [],
  "public_exposure_allowed": false,
  "dev_control_enabled": false,
  "fleet_sessions_enabled": false,
  "dev_diagnostics_enabled": false,
  "rescue_remote_enabled": false,
  "dev_server_enabled": false
}
JSON

cat >"${tmp}.oa" <<'JSON'
{"paths":{"/api/fleet/sessions":{}}}
JSON

# OpenAPI-only: release + fleet in schema but capability off => OK (not HTTP-accessible)
python3 "$EVAL" --api-version-file "$tmp" --openapi-file "${tmp}.oa" --no-http-probe --bind-address 127.0.0.1 || fail "release+openapi fleet schema should pass without http probe"

cat >"$tmp" <<'JSON'
{
  "install_profile": "release",
  "manifest_profile": "release",
  "fleet_sessions_enabled": true,
  "profile_gate_status": "green",
  "profile_gate_errors": [],
  "public_exposure_allowed": false
}
JSON

python3 "$EVAL" --api-version-file "$tmp" --openapi-file "${tmp}.oa" --no-http-probe --bind-address 127.0.0.1 && fail "expected exit 19 when fleet capability enabled in release"

python3 "$EVAL" --api-version-file "$tmp" --openapi-file "${tmp}.oa" --no-http-probe --bind-address 127.0.0.1 >/dev/null 2>&1 || ec=$?
[[ "${ec:-0}" -eq 19 ]] || fail "expected exit 19 got ${ec:-0}"

cat >"$tmp" <<'JSON'
{
  "install_profile": "local_lab",
  "manifest_profile": "local_lab",
  "profile_gate_status": "green",
  "profile_gate_errors": [],
  "public_exposure_allowed": false,
  "dev_control_enabled": true,
  "fleet_sessions_enabled": true,
  "dev_diagnostics_enabled": true
}
JSON

cat >"${tmp}.oa" <<'JSON'
{"paths":{"/api/fleet/sessions":{},"/api/dev-diagnostics/latest":{},"/api/dev-dashboard/status":{}}}
JSON

python3 "$EVAL" --api-version-file "$tmp" --openapi-file "${tmp}.oa" --no-http-probe --bind-address 127.0.0.1 || fail "local_lab with required paths should pass"

echo "OK: runtime profile deploy gate v1"
