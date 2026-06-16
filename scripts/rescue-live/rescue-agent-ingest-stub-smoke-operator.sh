#!/usr/bin/env bash
# Rescue-Agent Report-Ingest Stub Smoke — Operator only (requires sudo + local_lab).
# Usage: ./scripts/rescue-live/rescue-agent-ingest-stub-smoke-operator.sh
set -euo pipefail

cd "$(dirname "$0")/../.."

TS="$(date -u +%Y%m%d_%H%M%S)"
SMOKE_DIR="docs/evidence/rescue/rescue_agent_ingest_operator_smoke_${TS}"
RAW_DIR="$SMOKE_DIR/raw"
mkdir -p "$RAW_DIR"
LOG="$SMOKE_DIR/smoke.log"

restore_release() {
  echo "=== TRAP: restore release profile ===" | tee -a "$LOG"
  sudo install -m 0644 \
    packaging/systemd/dropins/92-install-profile-release.conf.example \
    /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
  sudo systemctl daemon-reload
  sudo systemctl restart setuphelfer-backend.service
  ./scripts/check-runtime-profile-deploy-gate.sh | tee -a "$LOG" || true
  curl -sS http://127.0.0.1:8000/api/version \
    | jq '{install_profile, profile_gate_status, dev_control_enabled, backend_runtime_path, rescue_agent_router_status, startup_diagnostics_status, router_registry_summary}' \
    | tee -a "$LOG" || true
  curl -sS -i http://127.0.0.1:8000/api/rescue-agent/sessions | head -20 | tee -a "$LOG" || true
}

trap restore_release EXIT

{
  echo "task=rescue_agent_report_ingest_stub_smoke_operator_guarded"
  echo "started_at=$(date -u --iso-8601=seconds)"
  echo "head=$(git rev-parse --short HEAD)"
  echo "branch=$(git branch --show-current)"
  echo "smoke_dir=$SMOKE_DIR"
} | tee "$LOG"

require_local_lab() {
  local profile dev
  profile="$(curl -sS http://127.0.0.1:8000/api/version | jq -r '.install_profile // "unknown"')"
  dev="$(curl -sS http://127.0.0.1:8000/api/version | jq -r '.dev_control_enabled // false')"
  if [[ "$profile" != "local_lab" ]]; then
    echo "ABORT: install_profile=$profile (need local_lab)" | tee -a "$LOG"
    exit 11
  fi
  if [[ "$dev" != "true" ]]; then
    echo "ABORT: dev_control_enabled=$dev (need true)" | tee -a "$LOG"
    exit 12
  fi
  echo "PROFILE_GUARD_OK local_lab active" | tee -a "$LOG"
}

{
  echo
  echo "=== BASELINE RELEASE ==="
  git rev-parse --short HEAD
  systemctl is-active setuphelfer-backend.service || true
  ./scripts/check-runtime-profile-deploy-gate.sh || true
  curl -sS http://127.0.0.1:8000/api/version \
    | jq '{install_profile, profile_gate_status, dev_control_enabled, rescue_agent_router_status}' || true
  echo "=== RELEASE ROUTE BLOCK CHECK ==="
  curl -sS -i http://127.0.0.1:8000/api/rescue-agent/register | head -15 || true
} 2>&1 | tee -a "$LOG"

{
  echo
  echo "=== ENABLE LOCAL_LAB ==="
} | tee -a "$LOG"

sudo install -d -m 0755 /etc/systemd/system/setuphelfer-backend.service.d
sudo install -m 0644 \
  packaging/systemd/dropins/92-install-profile-local-lab.conf.example \
  /etc/systemd/system/setuphelfer-backend.service.d/install-profile.conf
sudo systemctl daemon-reload
sudo systemctl restart setuphelfer-backend.service
sleep 2

curl -sS http://127.0.0.1:8000/api/version > "$RAW_DIR/version_local_lab.json"
{
  echo "=== LOCAL_LAB VERSION ==="
  jq '{install_profile, profile_gate_status, dev_control_enabled, rescue_agent_router_status, router_registry_summary}' "$RAW_DIR/version_local_lab.json"
} | tee -a "$LOG"

require_local_lab

curl -sS http://127.0.0.1:8000/openapi.json > "$RAW_DIR/openapi_local_lab.json"
python3 - <<PY | tee -a "$LOG"
import json
from pathlib import Path
data = json.loads(Path("$RAW_DIR/openapi_local_lab.json").read_text())
paths = [(p, sorted(s.keys())) for p, s in data.get("paths", {}).items() if "rescue-agent" in p.lower()]
print("rescue_agent_path_count=", len(paths))
for p, m in paths:
    print(p, m)
PY

{
  echo "=== RESCUE ROUTES LOCAL_LAB ==="
  curl -sS -i http://127.0.0.1:8000/api/rescue-agent/sessions | head -25 || true
} 2>&1 | tee -a "$LOG"

cat > "$RAW_DIR/negative_without_session.json" <<'JSON'
{"agent_id":"stub-negative-no-session","session_id":"","test_mode_allow_unencrypted":false}
JSON
curl -sS -D "$RAW_DIR/negative_without_session.headers" -o "$RAW_DIR/negative_without_session.body" \
  -w "%{http_code}" -X POST http://127.0.0.1:8000/api/rescue-agent/system-report \
  -H "Content-Type: application/json" --data @"$RAW_DIR/negative_without_session.json" \
  > "$RAW_DIR/negative_without_session.http_code" || true

cat > "$RAW_DIR/negative_unencrypted_without_allow.json" <<'JSON'
{"agent_id":"stub-negative-unencrypted","session_id":"invalid-session","test_mode_allow_unencrypted":false}
JSON
curl -sS -D "$RAW_DIR/negative_unencrypted_without_allow.headers" -o "$RAW_DIR/negative_unencrypted_without_allow.body" \
  -w "%{http_code}" -X POST http://127.0.0.1:8000/api/rescue-agent/system-report \
  -H "Content-Type: application/json" --data @"$RAW_DIR/negative_unencrypted_without_allow.json" \
  > "$RAW_DIR/negative_unencrypted_without_allow.http_code" || true

{
  echo "=== NEGATIVE TEST RESULTS ==="
  for name in negative_without_session negative_unencrypted_without_allow; do
    echo "--- $name http=$(cat "$RAW_DIR/$name.http_code" 2>/dev/null || true) ---"
    python3 -m json.tool "$RAW_DIR/$name.body" 2>/dev/null || cat "$RAW_DIR/$name.body"
  done
} | tee -a "$LOG"

cat > "$RAW_DIR/register_stub_request.json" <<'JSON'
{"agent_kind":"rescue_stick","agent_version":"stub-smoke","boot_id":"stub-boot-id","public_key":"stub-public-key-not-production","capabilities":["system_report","heartbeat"],"operator_label":"stub-local-lab-ingest-smoke"}
JSON
curl -sS -D "$RAW_DIR/register_stub.headers" -o "$RAW_DIR/register_stub.body" \
  -w "%{http_code}" -X POST http://127.0.0.1:8000/api/rescue-agent/register \
  -H "Content-Type: application/json" --data @"$RAW_DIR/register_stub_request.json" \
  > "$RAW_DIR/register_stub.http_code" || true

python3 -m json.tool "$RAW_DIR/register_stub.body" > "$RAW_DIR/register_stub.pretty.json" 2>/dev/null || true
{
  echo "=== REGISTRATION RESULT http=$(cat "$RAW_DIR/register_stub.http_code" 2>/dev/null || true) ==="
  cat "$RAW_DIR/register_stub.pretty.json" 2>/dev/null || cat "$RAW_DIR/register_stub.body"
} | tee -a "$LOG"

python3 - <<PY > "$RAW_DIR/register_stub_extracted.env"
import json
from pathlib import Path
try:
    data = json.loads(Path("$RAW_DIR/register_stub.body").read_text())
except Exception:
    data = {}
print(f"REGISTRATION_STATUS={data.get('registration_status') or data.get('status') or ''}")
print(f"RESCUE_SESSION_ID={data.get('session_id') or ''}")
print(f"RESCUE_AGENT_ID={data.get('agent_id') or 'stub-rescue-agent-local-lab'}")
PY
cat "$RAW_DIR/register_stub_extracted.env" | tee -a "$LOG"

# shellcheck source=/dev/null
source "$RAW_DIR/register_stub_extracted.env"
if [[ -z "${RESCUE_SESSION_ID:-}" ]]; then
  echo "NO_SESSION_ID_FROM_REGISTRATION" | tee -a "$LOG"
else
  cat > "$RAW_DIR/system_report_stub_valid.json" <<JSON
{"agent_id":"$RESCUE_AGENT_ID","session_id":"$RESCUE_SESSION_ID","test_mode_allow_unencrypted":true}
JSON
  curl -sS -D "$RAW_DIR/system_report_stub_valid.headers" -o "$RAW_DIR/system_report_stub_valid.body" \
    -w "%{http_code}" -X POST http://127.0.0.1:8000/api/rescue-agent/system-report \
    -H "Content-Type: application/json" --data @"$RAW_DIR/system_report_stub_valid.json" \
    > "$RAW_DIR/system_report_stub_valid.http_code" || true
  {
    echo "=== VALID REPORT http=$(cat "$RAW_DIR/system_report_stub_valid.http_code" 2>/dev/null || true) ==="
    python3 -m json.tool "$RAW_DIR/system_report_stub_valid.body" 2>/dev/null || cat "$RAW_DIR/system_report_stub_valid.body"
  } | tee -a "$LOG"
fi

python3 - <<PY
import json
from pathlib import Path

raw = Path("$RAW_DIR")

def code(n):
    p = raw / f"{n}.http_code"
    return p.read_text().strip() if p.exists() else ""

def js(n):
    p = raw / f"{n}.body"
    try:
        return json.loads(p.read_text()) if p.exists() else {}
    except Exception:
        return {}

reg = js("register_stub")
valid = js("system_report_stub_valid")
log = Path("$LOG").read_text()
result = {
    "task": "rescue_agent_report_ingest_stub_smoke",
    "status": "review_required",
    "release_block_before": "PROFILE_ROUTE_BLOCKED" in log,
    "local_lab_enabled": True,
    "registration_http_code": code("register_stub"),
    "registration_status": reg.get("registration_status") or reg.get("code") or "",
    "session_id_received": bool(reg.get("session_id")),
    "negative_report_without_session_http_code": code("negative_without_session"),
    "unencrypted_report_without_allow_http_code": code("negative_unencrypted_without_allow"),
    "valid_stub_report_http_code": code("system_report_stub_valid"),
    "valid_stub_report_status": valid.get("code") or valid.get("status") or "",
    "e2ee_status": "contract_stub_only",
    "nftables_status": "preview_only_apply_false",
    "no_write_apply_routes": True,
    "release_restored_after": False,
    "smoke_dir": "$SMOKE_DIR",
    "no_iso_build": True,
    "no_qemu": True,
    "no_usb": True,
    "no_backup": True,
    "no_restore": True,
    "no_apt": True,
    "next_recommended_action": "controlled_iso_build_precheck",
}
if result["registration_http_code"] in {"200", "201", "202"} and result["valid_stub_report_http_code"] in {"200", "201", "202"}:
    result["status"] = "ok"
Path("docs/evidence/rescue/rescue_agent_report_ingest_stub_smoke_latest.json").write_text(
    json.dumps(result, indent=2, ensure_ascii=False) + "\n"
)
PY

cat docs/evidence/rescue/rescue_agent_report_ingest_stub_smoke_latest.json | tee -a "$LOG"
echo "SMOKE_MAIN_DONE smoke_dir=$SMOKE_DIR" | tee -a "$LOG"
echo "trap will restore release on exit"
