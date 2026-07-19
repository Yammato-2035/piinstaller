#!/usr/bin/env bash
# RS-011B: Collect MSI evidence on rescue stick (read-only APIs, no backup/restore).
# Run ON MSI after boot from SETUPHELFER.
# Evidence path: /run/setuphelfer/esp-rw/setuphelfer/evidence/msi-rs011b/
set -uo pipefail

if [[ "${1:-}" == "--self-test" ]]; then
  if ! bash -n "$0" 2>/dev/null; then
    echo "ERROR: collect script syntax check failed" >&2
    exit 1
  fi
  echo "OK: collector_selftest"
  exit 0
fi

RUN_ID="${RS011B_RUN_ID:-RS_011B}"
API="${SETUPHELFER_RESCUE_API:-http://127.0.0.1:8000}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
ESP_RW="/run/setuphelfer/esp-rw"
RAM_EV="/run/setuphelfer/msi-rs011b-evidence"

resolve_collector_pythonpath() {
  local paths=() cand
  for cand in \
    "/opt/setuphelfer-rescue/backend" \
    "${REPO_ROOT}/backend" \
    "/usr/local/lib/setuphelfer-rescue/backend"; do
    [[ -d "$cand" ]] || continue
    paths+=("$cand")
  done
  if ((${#paths[@]} > 0)); then
    local IFS=:
    printf '%s' "${paths[*]}"
  fi
}

resolve_collector_python() {
  local cand
  for cand in \
    "/opt/setuphelfer-rescue/backend/venv/bin/python3" \
    "/run/setuphelfer/backend/venv/bin/python3" \
    "${REPO_ROOT}/backend/venv/bin/python3"; do
    if [[ -x "$cand" ]]; then
      printf '%s' "$cand"
      return 0
    fi
  done
  return 1
}

_collector_py="$(resolve_collector_pythonpath)"
if [[ -n "$_collector_py" ]]; then
  export PYTHONPATH="${_collector_py}${PYTHONPATH:+:${PYTHONPATH}}"
fi
_COLLECTOR_VENV="$(resolve_collector_python || true)"
_BACKEND_PYTHON="${_COLLECTOR_VENV:-}"
export SETUPHELFER_WORKSPACE_ROOT="${SETUPHELFER_WORKSPACE_ROOT:-$REPO_ROOT}"

write_supplement_failed_stubs() {
  local reason="$1"
  local msg="$2"
  local py="${_BACKEND_PYTHON:-}"
  if [[ -z "$py" ]]; then
    python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path

ev = Path(${EV@Q})
now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
meta = {
    "rescue_version": ${PV@Q},
    "collector_version": ${PV@Q},
    "boot_session_id": ${BOOT_SESSION_ID@Q},
    "collected_at": now,
    "source_run_id": ${RUN_ID@Q},
    "stale": False,
    "generated_by": "collect-msi-rs011b-evidence.sh",
    "error_reason": ${reason@Q},
}
for name in ("msi-killer-e2500-detection.json", "msi-aer-summary.json"):
    stub = {
        "schema_version": 1,
        "run_id": "RS_011D",
        "status": "failed",
        "error_code": ${reason@Q},
        "errors": [${msg@Q}],
        "checked_at": now,
        "secrets_exposed": False,
        "current_result_valid": False,
        "stale_previous_artifact": True,
        **meta,
    }
    (ev / name).write_text(json.dumps(stub, indent=2) + "\\n", encoding="utf-8")
summary = {
    "schema_version": 1,
    "run_id": "RS_011D",
    "status": "failed",
    "error_code": ${reason@Q},
    "errors": [${msg@Q}],
    "written": [],
    "missing": [],
    "failed": ["msi-killer-e2500-detection.json", "msi-aer-summary.json"],
    "complete": False,
    "checked_at": now,
    "secrets_exposed": False,
    "current_result_valid": False,
    "stale_previous_artifacts": [],
    "api_status": [],
    **meta,
}
(ev / "collector-summary.json").write_text(json.dumps(summary, indent=2) + "\\n", encoding="utf-8")
PY
    return
  fi
  PYTHONPATH="${_collector_py}${PYTHONPATH:+:${PYTHONPATH}}" "$py" - <<PY
import json
from pathlib import Path
from core.rescue_stale_artifact_guard import build_failed_stub, build_artifact_metadata

ev = Path(${EV@Q})
meta = build_artifact_metadata(
    rescue_version=${PV@Q},
    boot_session_id=${BOOT_SESSION_ID@Q},
    source_run_id=${RUN_ID@Q},
    generated_by="collect-msi-rs011b-evidence.sh",
    error_reason=${reason@Q},
)
for name in ("msi-killer-e2500-detection.json", "msi-aer-summary.json"):
    stub = build_failed_stub(
        error_code=${reason@Q},
        errors=[${msg@Q}],
        metadata=meta,
    )
    (ev / name).write_text(json.dumps(stub, indent=2) + "\\n", encoding="utf-8")
summary = build_failed_stub(
    error_code=${reason@Q},
    errors=[${msg@Q}],
    metadata=meta,
)
summary.update({
    "written": [],
    "missing": [],
    "failed": ["msi-killer-e2500-detection.json", "msi-aer-summary.json"],
    "complete": False,
    "current_result_valid": False,
    "stale_previous_artifacts": [],
    "api_status": [],
})
(ev / "collector-summary.json").write_text(json.dumps(summary, indent=2) + "\\n", encoding="utf-8")
PY
}

run_rs011d_supplement() {
  local _suppl_log="${EV}/rs011d-supplement.log"
  : >"$_suppl_log"

  export SETUPHELFER_MSI_EVIDENCE_DIR="$EV"
  export SETUPHELFER_EVIDENCE_ROOT="$(dirname "$EV")"
  export SETUPHELFER_SETUP_LOGS_ROOT="$LOGS_ROOT"
  export SETUPHELFER_SKIP_MOUNT_DISCOVERY_FOR_SUPPLEMENT=1
  export RS011B_BOOT_SESSION_ID="$BOOT_SESSION_ID"
  export RS011B_RESCUE_VERSION="${PV:-unknown}"
  export RS011B_RUN_ID="$RUN_ID"

  if [[ -z "$_COLLECTOR_VENV" ]]; then
    echo "RS011D_SUPPLEMENT_PYTHON_PRECHECK_FAILED collector_backend_venv_missing" >>"$_suppl_log"
    write_supplement_failed_stubs "collector_backend_venv_missing" \
      "backend venv python not found under /opt/setuphelfer-rescue/backend/venv/bin/python3"
    return 1
  fi

  if ! PYTHONPATH="${_collector_py}${PYTHONPATH:+:${PYTHONPATH}}" \
    "$_COLLECTOR_VENV" -c "import sys; import psutil; print(sys.executable)" >>"$_suppl_log" 2>&1; then
    echo "RS011D_SUPPLEMENT_PYTHON_PRECHECK_FAILED collector_python_missing_psutil" >>"$_suppl_log"
    write_supplement_failed_stubs "collector_python_missing_psutil" \
      "psutil import failed in collector venv python"
    return 1
  fi

  if ! _rw_usable "$EV"; then
    echo "RS011D_SUPPLEMENT_EVIDENCE_DIR_NOT_WRITABLE $EV" >>"$_suppl_log"
    write_supplement_failed_stubs "evidence_dir_not_writable" "EV not writable: ${EV}"
    return 1
  fi

  if PYTHONPATH="${_collector_py}${PYTHONPATH:+:${PYTHONPATH}}" \
    "$_COLLECTOR_VENV" - <<PY >>"$_suppl_log" 2>&1
import os
import sys
from pathlib import Path

os.environ.setdefault("SETUPHELFER_WORKSPACE_ROOT", ${REPO_ROOT@Q})
try:
    from core.rescue_msi_evidence_bundle import collect_rs011d_supplement
except ImportError as exc:
    print(f"IMPORT_ERROR: {exc}", file=sys.stderr)
    raise
result = collect_rs011d_supplement()
print("RS011D_SUPPLEMENT_OK", result.get("complete"), result.get("failed"))
PY
  then
    return 0
  fi
  return 1
}

resolve_expected_version() {
  if [[ -n "${RS011B_EXPECTED_VERSION:-}" ]]; then
    printf '%s' "$RS011B_EXPECTED_VERSION"
    return 0
  fi
  local py="${_BACKEND_PYTHON:-python3}"
  PYTHONPATH="${_collector_py}${PYTHONPATH:+:${PYTHONPATH}}" "$py" - <<'PY' 2>/dev/null || true
import json
import os
from pathlib import Path
from core.rescue_collector_version import resolve_expected_project_version
info = resolve_expected_project_version(
    override=os.environ.get("RS011B_EXPECTED_VERSION"),
    api_base=os.environ.get("SETUPHELFER_RESCUE_API", "http://127.0.0.1:8000"),
)
print(info.get("expected_version") or "")
PY
}

_rw_usable() {
  local d="$1" t
  [[ -d "$d" ]] || return 1
  t="$d/.rw-test.$$"
  if : >"$t" 2>/dev/null; then
    rm -f "$t" 2>/dev/null || true
    return 0
  fi
  return 1
}

mount_setup_logs_rw() {
  # Already mounted by boot-diagnostics / common.sh
  if mountpoint -q "$ESP_RW" 2>/dev/null && _rw_usable "$ESP_RW"; then
    printf '%s' "$ESP_RW"
    return 0
  fi

  # Source project helper if present on live system
  for common in /usr/local/sbin/setuphelfer-rescue-common.sh /opt/setuphelfer-rescue/scripts/rescue-live/image/setuphelfer-rescue-common.sh; do
    if [[ -f "$common" ]]; then
      # shellcheck source=/dev/null
      source "$common"
      if base="$(setuphelfer_rescue_evidence_writable_base 2>/dev/null)" && _rw_usable "$base"; then
        printf '%s' "$base"
        return 0
      fi
    fi
  done

  # Same strategy as setuphelfer-rescue-boot-diagnostics
  local logsdev cand
  for cand in /dev/disk/by-partlabel/SETUPHELFER_LOGS /dev/disk/by-label/SETUP_LOGS /dev/disk/by-label/SETUPHELFER_LOGS; do
    if [[ -e "$cand" ]]; then
      logsdev="$(readlink -f "$cand" 2>/dev/null || echo "$cand")"
      break
    fi
  done
  if [[ -n "${logsdev:-}" && -b "$logsdev" ]]; then
    mkdir -p "$ESP_RW" 2>/dev/null || sudo mkdir -p "$ESP_RW"
    if mount -t vfat -o rw,flush,umask=0022 "$logsdev" "$ESP_RW" 2>/dev/null \
      || sudo mount -t vfat -o rw,flush,umask=0022 "$logsdev" "$ESP_RW" 2>/dev/null; then
      if _rw_usable "$ESP_RW"; then
        printf '%s' "$ESP_RW"
        return 0
      fi
    fi
  fi

  # Desktop auto-mount
  local mp
  shopt -s nullglob
  for mp in /media/*/SETUP_LOGS /media/*/*/SETUP_LOGS; do
    if [[ -d "$mp" ]] && _rw_usable "$mp"; then
      printf '%s' "$mp"
      return 0
    fi
  done
  shopt -u nullglob

  return 1
}

LOGS_ROOT="$(mount_setup_logs_rw)" || {
  echo "WARN: SETUP_LOGS nicht beschreibbar — schreibe nach ${RAM_EV} (später auf Stick kopieren)" >&2
  LOGS_ROOT="$RAM_EV"
  mkdir -p "$LOGS_ROOT" 2>/dev/null || sudo mkdir -p "$LOGS_ROOT"
}

EV="${LOGS_ROOT}/setuphelfer/evidence/msi-rs011b"
mkdir -p "$EV/screenshots" 2>/dev/null || sudo mkdir -p "$EV/screenshots"
if ! _rw_usable "$(dirname "$EV")" 2>/dev/null; then
  sudo mkdir -p "$EV/screenshots"
  sudo chmod -R a+rwX "${LOGS_ROOT}/setuphelfer" 2>/dev/null || true
fi

log_step() {
  local phase="$1" msg="$2" status="${3:-ok}"
  printf '{"ts":"%s","run_id":"%s","phase":"%s","status":"%s","message":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$RUN_ID" "$phase" "$status" "$msg" >>"$EV/operator-steps.jsonl"
}

behavior() {
  local event="$1" detail="${2:-{}}"
  printf '{"ts":"%s","event":"%s","detail":%s}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$event" "$detail" >>"$EV/beta-operator-behavior.jsonl"
}

curl_json() {
  local url="$1" out="$2"
  local code body
  body="$(curl -sS -w '\n%{http_code}' "$url" 2>/dev/null || printf '\n000')"
  code="${body##*$'\n'}"
  body="${body%$'\n'*}"
  printf '%s' "$body" >"$out" 2>/dev/null || sudo tee "$out" >/dev/null <<<"$body"
  printf '%s' "$code"
}

echo "=== RS-011B evidence collect ==="
echo "LOGS_ROOT=$LOGS_ROOT"
echo "EV=$EV"
EXPECTED_VERSION="$(resolve_expected_version)"
echo "EXPECTED_VERSION=${EXPECTED_VERSION:-<unresolved>}"
log_step "collect_start" "Evidence collection started logs_root=${LOGS_ROOT}"

for src in \
  /run/setuphelfer/evidence/boot/boot-timeline.jsonl \
  /run/setuphelfer/evidence/boot/boot-summary.json \
  /run/setuphelfer/evidence/boot/boot-summary.md \
  /run/setuphelfer/evidence/boot/gui-watchdog.json; do
  if [[ -f "$src" ]]; then
    cp -a "$src" "$EV/" 2>/dev/null || sudo cp -a "$src" "$EV/"
    log_step "boot_evidence" "copied $(basename "$src")"
  fi
done

code="$(curl_json "${API}/api/version" "$EV/api-version.json")"
log_step "api_version" "HTTP ${code}" "$([[ "$code" == "200" ]] && echo ok || echo fail)"
if [[ "$code" != "200" ]]; then
  python3 - <<PY >"$EV/collector-version-check.json" 2>/dev/null || true
import json
from datetime import datetime, timezone
print(json.dumps({
    "schema_version": 1,
    "status": "failed",
    "api_project_version": None,
    "expected_project_version": ${EXPECTED_VERSION@Q} or None,
    "skip_version_check": False,
    "match": None,
    "exit_code": 3,
    "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}))
PY
  echo "ERROR: Backend nicht erreichbar unter ${API}/api/version (HTTP ${code})" >&2
  echo "  systemctl status setuphelfer-backend.service" >&2
  echo "  journalctl -u setuphelfer-backend.service -n 40 --no-pager" >&2
  behavior "error_seen" "{\"code\":\"MSI_BACKEND_UNSTABLE\",\"http\":\"${code}\"}"
  exit 3
fi

PV="$(python3 - <<PY 2>/dev/null || echo unknown
import json
from pathlib import Path
p = Path(${EV@Q}) / "api-version.json"
d = json.loads(p.read_text(encoding="utf-8"))
print(d.get("project_version") or d.get("version") or "unknown")
PY
)"
python3 - <<PY >"$EV/collector-version-check.json" 2>/dev/null || true
import json
import os
from core.rescue_collector_version import evaluate_version_check
skip = os.environ.get("RS011B_SKIP_VERSION_CHECK") == "1"
check = evaluate_version_check(
    api_version=${PV@Q},
    expected_version=${EXPECTED_VERSION@Q} or None,
    skip_version_check=skip,
)
print(json.dumps(check, indent=2))
PY
if [[ -n "${EXPECTED_VERSION:-}" && "$PV" != "$EXPECTED_VERSION" && "${RS011B_SKIP_VERSION_CHECK:-}" != "1" ]]; then
  log_step "version_check" "expected ${EXPECTED_VERSION} got ${PV}" "fail"
  echo "HARDSTOP: version mismatch (${PV} != ${EXPECTED_VERSION})" >&2
  echo "  Trotzdem sammeln: RS011B_SKIP_VERSION_CHECK=1 $0" >&2
  behavior "error_seen" "{\"code\":\"MSI_VERSION_MISMATCH\",\"version\":\"${PV}\"}"
  exit 17
fi
if [[ "${RS011B_SKIP_VERSION_CHECK:-}" == "1" ]]; then
  log_step "version_check" "skip RS011B_SKIP_VERSION_CHECK=1 api=${PV}" "review_required"
else
  log_step "version_check" "project_version=${PV}" "ok"
fi

BOOT_SESSION_ID="${RS011B_BOOT_SESSION_ID:-$(date -u +%Y%m%d_%H%M%S)_${PV}}"
export RS011B_BOOT_SESSION_ID="$BOOT_SESSION_ID"

API_STATUS_TMP="$(mktemp)"
: >"$API_STATUS_TMP"
for ep in \
  "rescue-health:${API}/api/rescue/monitoring/health" \
  "disk-inventory:${API}/api/rescue/disks/inventory" \
  "storage-discovery:${API}/api/rescue/storage/discovery"; do
  name="${ep%%:*}"
  url="${ep#*:}"
  c="$(curl_json "$url" "$EV/${name}.json")"
  st="$([[ "$c" == "200" ]] && echo ok || echo api_endpoint_failed)"
  log_step "api_${name}" "HTTP ${c}" "$([[ "$c" == "200" ]] && echo ok || echo warn)"
  printf '{"endpoint":"%s","http_code":%s,"status":"%s","rescue_version":"%s","checked_at":"%s"}\n' \
    "$name" "$c" "$st" "$PV" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >>"$API_STATUS_TMP"
done
python3 - <<PY >"$EV/api-endpoint-status.json"
import json
from pathlib import Path
rows = []
for line in Path(${API_STATUS_TMP@Q}).read_text(encoding="utf-8").splitlines():
    if line.strip():
        rows.append(json.loads(line))
payload = {
    "schema_version": 1,
    "rescue_version": ${PV@Q},
    "boot_session_id": ${BOOT_SESSION_ID@Q},
    "endpoints": rows,
}
print(json.dumps(payload, indent=2))
PY
rm -f "$API_STATUS_TMP"

sanitize_api_evidence_json() {
  local py="${_BACKEND_PYTHON:-python3}"
  PYTHONPATH="${_collector_py}${PYTHONPATH:+:${PYTHONPATH}}" "$py" - <<PY
import json
from pathlib import Path
from core.rescue_discovery_failed_stub import (
    build_disk_inventory_failed_stub,
    build_rescue_health_degraded,
    build_storage_discovery_failed_stub,
    is_valid_api_json_body,
)

ev = Path(${EV@Q})
ver = ${PV@Q}
sess = ${BOOT_SESSION_ID@Q}
mapping = {
    "rescue-health.json": ("rescue-health", build_rescue_health_degraded),
    "disk-inventory.json": ("disk-inventory", build_disk_inventory_failed_stub),
    "storage-discovery.json": ("storage-discovery", build_storage_discovery_failed_stub),
}
for name, (endpoint, builder) in mapping.items():
    path = ev / name
    if not path.is_file():
        continue
    raw = path.read_text(encoding="utf-8", errors="replace")
    if is_valid_api_json_body(raw):
        continue
    http = 500
    if name == "storage-discovery.json":
        stub = builder(
            message_redacted=raw.strip()[:200] or "invalid_api_body",
            http_status=http,
            rescue_version=ver,
            boot_session_id=sess,
        )
    elif name == "disk-inventory.json":
        stub = builder(rescue_version=ver, boot_session_id=sess)
    else:
        stub = builder(rescue_version=ver, boot_session_id=sess)
    path.write_text(json.dumps(stub, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
PY
}
sanitize_api_evidence_json

if command -v lsblk >/dev/null 2>&1; then
  lsblk -J -O >"$EV/lsblk.json" 2>/dev/null \
    || lsblk -o NAME,PATH,TYPE,SIZE,MODEL,TRAN,RM,LABEL,FSTYPE,MOUNTPOINTS >"$EV/lsblk.txt" 2>/dev/null \
    || sudo lsblk -J -O >"$EV/lsblk.json"
fi

python3 - <<PY 2>/dev/null || true
import json
from pathlib import Path
ev = Path(${EV@Q})
lines = ["# Disk Discovery Summary (RS-011B)", "", f"Generated: ${TS}", ""]
sd = {}
p = ev / "storage-discovery.json"
if p.is_file():
    sd = json.loads(p.read_text(encoding="utf-8"))
sources = sd.get("source_candidates") or []
targets = sd.get("target_candidates") or []
diag = sd.get("diagnostics") or {}
lines += [
    f"- source_candidates: {len(sources)}",
    f"- target_candidates: {len(targets)}",
    f"- empty_reason_code: {diag.get('empty_reason_code')}",
    "",
    "## Sources",
]
for s in sources:
    if s.get("can_be_backup_source") or s.get("type") == "system_group":
        lines.append(f"- {s.get('path')} role={s.get('role')} type={s.get('type')}")
lines += ["", "## Targets"]
for t in targets:
    if t.get("can_be_backup_target", True):
        lines.append(f"- {t.get('path')} role={t.get('role')} label={t.get('label')}")
(ev / "disk-discovery-summary.md").write_text("\\n".join(lines) + "\\n", encoding="utf-8")
PY

if [[ ! -f "$EV/RS_011B_MSI_BOOT_SUMMARY.md" ]]; then
  cat >"$EV/RS_011B_MSI_BOOT_SUMMARY.md" <<EOF
# RS-011B MSI Boot Summary

| Feld | Wert |
|------|------|
| Datum | ${TS} |
| Stick-Version (API) | ${PV} |
| Evidence-Pfad | ${EV} |

## Operator ergänzen

- X-Statusscreen sichtbar: ja/nein
- Schwarzphase >5s: ja/nein
- GUI stabil: ja/nein
EOF
fi

[[ -f "$EV/screenshot-index.json" ]] || echo '{"schema_version":1,"screenshots":[]}' >"$EV/screenshot-index.json"

sync 2>/dev/null || true
if [[ "$LOGS_ROOT" == "$RAM_EV" ]]; then
  echo ""
  echo "WARN: Evidence nur im RAM — nach Reboot weg. Kopieren:"
  echo "  sudo cp -a ${EV} /run/setuphelfer/esp-rw/setuphelfer/evidence/  # wenn SETUP_LOGS später mountbar"
fi

behavior "preflight_started" "{\"phase\":\"evidence_collect\"}"

if run_rs011d_supplement; then
  log_step "rs011d_supplement" "ok collector_python=${_COLLECTOR_VENV:-missing}" "ok"
else
  log_step "rs011d_supplement" "failed — see rs011d-supplement.log" "warn"
  echo "WARN: RS-011D supplement failed — see ${EV}/rs011d-supplement.log" >&2
fi

log_step "collect_done" "Phase 1 complete"
echo ""
echo "OK: Evidence -> ${EV}"
echo "Import auf Dev-Rechner: ./scripts/rescue/import-msi-rs011b-evidence.sh"

if [[ "${1:-}" == "--preflight-only" ]] || [[ "${RS011B_PREFLIGHT:-}" == "1" ]]; then
  : "${RS011B_SOURCE_DEVICE:?Set RS011B_SOURCE_DEVICE=/dev/nvme0n1}"
  : "${RS011B_TARGET_DEVICE:?Set RS011B_TARGET_DEVICE=/dev/sdb}"
  : "${RS011B_TARGET_MOUNT:?Set RS011B_TARGET_MOUNT=/media/.../Backup}"
  body="$(python3 - <<PY
import json
print(json.dumps({
    "source_device": ${RS011B_SOURCE_DEVICE@Q},
    "source_type": "system_group",
    "source_role": "windows_system_disk",
    "target_device": ${RS011B_TARGET_DEVICE@Q},
    "target_mount": ${RS011B_TARGET_MOUNT@Q},
    "target_mode": "external_hdd",
    "free_bytes": 0,
    "operator_confirm_source": True,
    "operator_confirm_target": True,
    "operator_confirm_no_restore": True,
    "operator_confirm_no_wipe": True,
    "booted_from_rescue": True,
}))
PY
)"
  code="$(curl -sS -o "$EV/backup-preflight.json" -w '%{http_code}' \
    -X POST "${API}/api/rescue/backup/full-plan" \
    -H 'Content-Type: application/json' \
    -d "$body" 2>/dev/null || echo "000")"
  log_step "preflight_api" "HTTP ${code}" "$([[ "$code" == "200" ]] && echo ok || echo fail)"
  echo "Preflight: $EV/backup-preflight.json (execute_allowed must be false)"
fi
