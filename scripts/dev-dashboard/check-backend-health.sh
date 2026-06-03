#!/usr/bin/env bash
# Developer-only read-only healthcheck (no sudo, no restart).
# Writes: docs/evidence/dev-dashboard/backend_health_latest.json
#         docs/evidence/dev-dashboard/backend_health_history.jsonl

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="$SCRIPT_DIR/$(basename "${BASH_SOURCE[0]}")"
if [[ -n "${SETUPHELFER_REPO_ROOT:-}" ]]; then
  REPO_ROOT="$(cd "$SETUPHELFER_REPO_ROOT" && pwd)"
else
  REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi
if [[ -n "${SETUPHELFER_HEALTH_EVIDENCE_DIR:-}" ]]; then
  EVIDENCE_DIR="$(cd "$SETUPHELFER_HEALTH_EVIDENCE_DIR" && pwd)"
else
  EVIDENCE_DIR="$REPO_ROOT/docs/evidence/dev-dashboard"
fi
LATEST_JSON="$EVIDENCE_DIR/backend_health_latest.json"
HISTORY_JSONL="$EVIDENCE_DIR/backend_health_history.jsonl"
TMP_JSON="$(mktemp "$EVIDENCE_DIR/.backend_health_latest.XXXXXX.json")"
CWD="$(pwd)"

API_BASE="${SETUPHELFER_API_BASE:-http://127.0.0.1:8000}"
WEB_BASE="${SETUPHELFER_WEB_BASE:-http://127.0.0.1:3001}"
CURL_MAX="${SETUPHELFER_HEALTH_CURL_MAX_TIME:-5}"
HEAD="$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
GENERATED_AT="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

mkdir -p "$EVIDENCE_DIR"

_curl_code() {
  local url="$1"
  if ! command -v curl >/dev/null 2>&1; then
    echo "000"
    return
  fi
  curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 2 --max-time "$CURL_MAX" "$url" 2>/dev/null || echo "000"
}

_curl_body_code() {
  local url="$1"
  local out
  out="$(mktemp)"
  local code="000"
  if command -v curl >/dev/null 2>&1; then
    code="$(curl -sS -o "$out" -w '%{http_code}' --connect-timeout 2 --max-time "$CURL_MAX" "$url" 2>/dev/null || echo "000")"
  fi
  echo "$code" >"${out}.code"
  mv "$out" "${out}.body" 2>/dev/null || true
  # shellcheck disable=SC2005
  echo "$(cat "${out}.body" 2>/dev/null || true)"
  rm -f "${out}.body" "${out}.code" 2>/dev/null || true
  echo "$code"
}

_systemctl_active() {
  local unit="$1"
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "unknown"
    return
  fi
  if systemctl is-active --quiet "$unit" 2>/dev/null; then
    echo "true"
  else
    echo "false"
  fi
}

_port_listening() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | grep -q ":${port} " && echo "true" || echo "false"
    return
  fi
  if command -v netstat >/dev/null 2>&1; then
    netstat -ltn 2>/dev/null | grep -q ":${port} " && echo "true" || echo "false"
    return
  fi
  echo "unknown"
}

backend_active="$(_systemctl_active setuphelfer-backend.service)"
frontend_active="$(_systemctl_active setuphelfer.service)"
port_8000="$(_port_listening 8000)"
port_3001="$(_port_listening 3001)"

api_version_http="$(_curl_code "${API_BASE}/api/version")"
version_body=""
if command -v curl >/dev/null 2>&1; then
  version_body="$(curl -sS --connect-timeout 2 --max-time "$CURL_MAX" "${API_BASE}/api/version" 2>/dev/null || true)"
fi

dev_dashboard_http="$(_curl_code "${API_BASE}/api/dev-dashboard/status")"
fleet_http="$(_curl_code "${API_BASE}/api/fleet/sessions")"
recent_http="$(_curl_code "${API_BASE}/api/dev-dashboard/recent-evidence")"
web_http="$(_curl_code "${WEB_BASE}/")"

install_profile="unknown"
profile_gate_status="unknown"
dev_control_enabled="false"

if [[ -n "$version_body" ]]; then
  parsed="$(VERSION_BODY="$version_body" python3 - <<'PY' 2>/dev/null || true
import json, os
try:
    d = json.loads(os.environ.get("VERSION_BODY") or "{}")
    print(
        d.get("install_profile", "unknown"),
        d.get("profile_gate_status", "unknown"),
        str(d.get("dev_control_enabled", False)).lower(),
        sep="\t",
    )
except Exception:
    print("unknown\tunknown\tfalse")
PY
)"
  if [[ -n "$parsed" ]]; then
    IFS=$'\t' read -r install_profile profile_gate_status dev_control_enabled <<<"$parsed"
  fi
fi

expected_profile_blocks="false"
if [[ "$install_profile" == "release" ]] || [[ "$dev_control_enabled" == "false" ]]; then
  expected_profile_blocks="true"
fi

failure_classification="none"
recommended_operator_action=""
overall_status="ok"

if [[ "$backend_active" != "true" ]] || [[ "$port_8000" != "true" ]] || [[ "$api_version_http" != "200" ]]; then
  overall_status="blocked"
  if [[ "$port_8000" != "true" ]]; then
    failure_classification="port_8000_down"
  elif [[ "$backend_active" != "true" ]]; then
    failure_classification="backend_down"
  else
    failure_classification="api_unreachable"
  fi
  recommended_operator_action="systemctl status setuphelfer-backend.service; journalctl -u setuphelfer-backend.service -n 200; sudo systemctl daemon-reload; sudo systemctl restart setuphelfer-backend.service; curl ${API_BASE}/api/version"
elif [[ "$expected_profile_blocks" == "true" ]]; then
  if [[ "$dev_dashboard_http" == "404" ]] && [[ "$fleet_http" == "404" ]] && [[ "$recent_http" == "404" ]]; then
    overall_status="ok"
    failure_classification="none"
  else
    overall_status="warning"
    failure_classification="profile_mismatch"
    recommended_operator_action="Prüfe install-profile.conf und SETUPHELFER_INSTALL_PROFILE; erwartet PROFILE_ROUTE_BLOCKED unter release."
  fi
else
  if [[ "$dev_dashboard_http" != "200" ]] || [[ "$recent_http" != "200" ]]; then
    overall_status="warning"
    failure_classification="dev_routes_blocked_unexpected"
    recommended_operator_action="Profil local_lab aktivieren oder Dev-Capabilities prüfen; Dev-Routen sollten HTTP 200 liefern."
  fi
  if [[ "$frontend_active" != "true" ]] || [[ "$port_3001" != "true" ]]; then
    if [[ "$overall_status" == "ok" ]]; then
      overall_status="warning"
    fi
    if [[ "$failure_classification" == "none" ]]; then
      failure_classification="frontend_down"
    fi
    recommended_operator_action="${recommended_operator_action:-systemctl status setuphelfer.service; sudo systemctl restart setuphelfer.service}"
  fi
fi

if [[ "$web_http" != "200" ]] && [[ "$overall_status" == "ok" ]]; then
  overall_status="warning"
  if [[ "$failure_classification" == "none" ]]; then
    failure_classification="frontend_down"
  fi
fi

last_ok_at=""
last_failure_at=""
if [[ -f "$LATEST_JSON" ]]; then
  read_prev="$(python3 - <<PY 2>/dev/null || true
import json
from pathlib import Path
p = Path("$LATEST_JSON")
try:
    d = json.loads(p.read_text(encoding="utf-8"))
    print(d.get("last_ok_at") or "", d.get("last_failure_at") or "", sep="\t")
except Exception:
    print("\t")
PY
)"
  IFS=$'\t' read -r last_ok_at last_failure_at <<<"$read_prev"
fi

if [[ "$overall_status" == "ok" ]]; then
  last_ok_at="$GENERATED_AT"
else
  last_failure_at="$GENERATED_AT"
fi

export GENERATED_AT HEAD backend_active frontend_active port_8000 port_3001
export api_version_http install_profile profile_gate_status dev_control_enabled
export dev_dashboard_http fleet_http recent_http web_http
export expected_profile_blocks overall_status failure_classification recommended_operator_action
export last_ok_at last_failure_at API_BASE
export REPO_ROOT EVIDENCE_DIR LATEST_JSON HISTORY_JSONL SCRIPT_PATH CWD

python3 - <<'PY' >"$TMP_JSON"
import json, os
doc = {
    "task": "developer_backend_healthcheck",
    "generated_at": os.environ["GENERATED_AT"],
    "head": os.environ["HEAD"],
    "backend_service_active": os.environ["backend_active"] == "true",
    "frontend_service_active": os.environ["frontend_active"] == "true",
    "backend_port_8000_listening": os.environ["port_8000"] == "true",
    "frontend_port_3001_listening": os.environ["port_3001"] == "true",
    "api_version_http": int(os.environ["api_version_http"]) if os.environ["api_version_http"].isdigit() else 0,
    "install_profile": os.environ["install_profile"],
    "profile_gate_status": os.environ["profile_gate_status"],
    "dev_control_enabled": os.environ["dev_control_enabled"] == "true",
    "dev_dashboard_status_http": int(os.environ["dev_dashboard_http"]) if os.environ["dev_dashboard_http"].isdigit() else 0,
    "fleet_sessions_http": int(os.environ["fleet_http"]) if os.environ["fleet_http"].isdigit() else 0,
    "recent_evidence_http": int(os.environ["recent_http"]) if os.environ["recent_http"].isdigit() else 0,
    "web_ui_http": int(os.environ["web_http"]) if os.environ["web_http"].isdigit() else 0,
    "expected_profile_blocks": os.environ["expected_profile_blocks"] == "true",
    "overall_status": os.environ["overall_status"],
    "failure_classification": os.environ["failure_classification"],
    "recommended_operator_action": os.environ["recommended_operator_action"],
    "last_ok_at": os.environ["last_ok_at"] or None,
    "last_failure_at": os.environ["last_failure_at"] or None,
    "api_base": os.environ["API_BASE"],
    "repo_root": os.environ["REPO_ROOT"],
    "evidence_dir": os.environ["EVIDENCE_DIR"],
    "latest_path": os.environ["LATEST_JSON"],
    "history_path": os.environ["HISTORY_JSONL"],
    "script_path": os.environ["SCRIPT_PATH"],
    "cwd": os.environ["CWD"],
}
print(json.dumps(doc, indent=2, ensure_ascii=False))
PY

mv -f "$TMP_JSON" "$LATEST_JSON"
chmod 664 "$LATEST_JSON" 2>/dev/null || chmod 644 "$LATEST_JSON" 2>/dev/null || true
python3 -c "import json; print(json.dumps(json.load(open('$LATEST_JSON')), separators=(',',':')))" >>"$HISTORY_JSONL"
chmod 664 "$HISTORY_JSONL" 2>/dev/null || chmod 644 "$HISTORY_JSONL" 2>/dev/null || true

exit_code=0
if [[ "$overall_status" == "blocked" ]]; then
  exit_code=2
elif [[ "$overall_status" == "warning" ]]; then
  exit_code=1
fi
exit "$exit_code"
