#!/usr/bin/env bash
# PI-RS-TEL-002 profile-aware runtime gate (release vs lab)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

BASE_URL="${SETUPHELFER_VERSION_URL:-http://127.0.0.1:8000}"
SERVICE="${SETUPHELFER_BACKEND_SERVICE:-setuphelfer-backend.service}"
EXPECTED="${SETUPHELPER_EXPECTED_PROFILE:-release}"
OUT_JSON="${ROOT}/docs/evidence/runtime-results/profile_aware_runtime_gate_latest.json"

service_active="false"
if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet "$SERVICE" 2>/dev/null; then
  service_active="true"
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

version_code="000"
lab_code="000"
dcc_code="000"

version_code="$(curl -sS -o "$tmpdir/version.json" -w '%{http_code}' --connect-timeout 2 --max-time 8 "${BASE_URL}/api/version" 2>/dev/null || echo 000)"
lab_code="$(curl -sS -o "$tmpdir/lab.json" -w '%{http_code}' --connect-timeout 2 --max-time 8 "${BASE_URL}/api/rescue/telemetry/lab/status" 2>/dev/null || echo 000)"
dcc_code="$(curl -sS -o "$tmpdir/dcc.json" -w '%{http_code}' --connect-timeout 2 --max-time 8 "${BASE_URL}/api/dev-dashboard/status" 2>/dev/null || echo 000)"

PYTHONPATH="${ROOT}/backend" python3 - "$EXPECTED" "$service_active" "$version_code" "$lab_code" "$dcc_code" "$tmpdir" "$OUT_JSON" <<'PY'
import json
import sys
from pathlib import Path

from core.profile_aware_runtime_gate import evaluate_profile_aware_runtime_gate

expected, service_active, version_code, lab_code, dcc_code, tmpdir, out_json = sys.argv[1:8]
tmpdir = Path(tmpdir)
out_path = Path(out_json)

def load_json(name: str) -> dict:
    p = tmpdir / name
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}

version_payload = load_json("version.json")
lab_body = load_json("lab.json")

result = evaluate_profile_aware_runtime_gate(
    expected_profile=expected,
    version_http_status=int(version_code),
    version_payload=version_payload,
    lab_status_http=int(lab_code),
    lab_status_body=lab_body,
    dcc_status_http=int(dcc_code),
    service_active=service_active == "true",
    backend_runtime_path=version_payload.get("backend_runtime_path"),
)

out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))

if result["status"].endswith("_blocked"):
    sys.exit(1)
if result["status"].endswith("_review_required"):
    sys.exit(2)
sys.exit(0)
PY
