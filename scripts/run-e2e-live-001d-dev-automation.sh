#!/usr/bin/env bash
# SETUPHELFER-E2E-LIVE-001D / 001D7E — Dev automation + evidence import.
#
# Usage:
#   ./scripts/run-e2e-live-001d-dev-automation.sh --mode auto-discovery --setup-logs-root PATH --import-only --execute
#   ./scripts/run-e2e-live-001d-dev-automation.sh --mode physical-e2e --import-only --execute
#   ./scripts/run-e2e-live-001d-dev-automation.sh --mode auto --import-only --execute
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXECUTE=false
IMPORT_ONLY=false
RUN_ONLY=false
PHYSICAL_MSI_IMPORT=false
MODE="auto"
SETUP_LOGS_ROOT="${SETUP_LOGS_ROOT:-${SETUP_LOGS:-}}"
TARGET_BYTES="${TARGET_BYTES:-67108864}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=true; shift ;;
    --import-only) IMPORT_ONLY=true; shift ;;
    --run-only) RUN_ONLY=true; shift ;;
    --physical-msi-import) PHYSICAL_MSI_IMPORT=true; MODE="physical-e2e"; shift ;;
    --mode) MODE="$2"; shift 2 ;;
    --setup-logs-root) SETUP_LOGS_ROOT="$2"; shift 2 ;;
    --target-bytes) TARGET_BYTES="$2"; shift 2 ;;
    -h|--help)
      sed -n '1,20p' "$0"
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ "$IMPORT_ONLY" == true && "$RUN_ONLY" == true ]]; then
  echo "ERROR: --import-only and --run-only are mutually exclusive" >&2
  exit 2
fi

echo "=== SETUPHELFER E2E-LIVE-001D Dev Automation ==="
echo "Repository: ${REPO_ROOT}"
echo "Execute:    ${EXECUTE}"
echo "Mode:       ${MODE}"

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

# Resolve SETUP_LOGS without accepting empty shadow directories.
SETUP_LOGS="$(
python3 - <<PY
import json
from core.rescue_setup_logs_resolver import select_setup_logs_for_import
sel = select_setup_logs_for_import(explicit_root=${SETUP_LOGS_ROOT@Q} or None)
print(json.dumps(sel))
PY
)"

echo "SETUP_LOGS selection: ${SETUP_LOGS}"
SETUP_LOGS_PATH="$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print(d.get("setup_logs_base") or "")' "$SETUP_LOGS")"
SETUP_LOGS_OK="$(python3 -c 'import json,sys; d=json.loads(sys.argv[1]); print("yes" if d.get("ok") else "no")' "$SETUP_LOGS")"

if [[ "$SETUP_LOGS_OK" == "yes" && -n "$SETUP_LOGS_PATH" ]]; then
  echo "SETUP_LOGS: ${SETUP_LOGS_PATH}"
  ls -la "${SETUP_LOGS_PATH}/setuphelfer/evidence/" 2>/dev/null | head -20 || true
else
  echo "SETUP_LOGS: not resolved (shadow mounts ignored)"
fi

lsblk -e7 -o NAME,PATH,TYPE,TRAN,RM,SIZE,MODEL,LABEL,MOUNTPOINTS 2>/dev/null | grep -E 'NAME|usb|SETUP' || true

if [[ "$EXECUTE" != true ]]; then
  echo ""
  echo "Plan mode — no changes. Use --execute to run."
  exit 0
fi

export SETUP_LOGS="${SETUP_LOGS_PATH}"

RESULT_JSON="${REPO_ROOT}/docs/evidence/e2e_live_001d/dev_automation_latest.json"
mkdir -p "$(dirname "$RESULT_JSON")"

python3 - <<PY
import json
import os
from pathlib import Path

from core.rescue_auto_discovery_import import (
    detect_evidence_mode,
    import_auto_discovery_evidence,
    resolve_import_setup_logs,
)
from core.rescue_physical_e2e_dev_automation import run_full_dev_automation
from core.rescue_physical_e2e_physical_import import import_physical_msi_evidence

repo = Path(${REPO_ROOT@Q})
mode = ${MODE@Q}
explicit = ${SETUP_LOGS_ROOT@Q} or None
selected = resolve_import_setup_logs(explicit_root=explicit or None)
out = {
    "feature": "SETUPHELFER-E2E-LIVE-001D7E",
    "mode_requested": mode,
    "setup_logs_selection": {
        **{k: (str(v) if isinstance(v, Path) else v) for k, v in selected.items()}
    },
    "production_ready": False,
}
if not selected.get("ok"):
    out["status"] = selected.get("code") or "setup_logs_not_mounted"
    out["import"] = {"import_ok": False, **selected}
    Path(${RESULT_JSON@Q}).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    raise SystemExit(1)

logs = Path(str(selected["setup_logs_base"]))
out["setup_logs_base"] = str(logs)
out["setup_logs_mounted"] = True

if ${IMPORT_ONLY@Q} == "true" or True:
    detected = detect_evidence_mode(logs)
    effective = mode
    if mode == "auto":
        if not detected.get("ok"):
            out["status"] = detected.get("code") or "ambiguous_evidence_mode"
            out["import"] = detected
            Path(${RESULT_JSON@Q}).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
            print(json.dumps(out, indent=2))
            raise SystemExit(1)
        effective = detected["mode"]
    out["mode_effective"] = effective

    if ${IMPORT_ONLY@Q} != "true" and ${RUN_ONLY@Q} != "true" and effective == "physical-e2e":
        result = run_full_dev_automation(
            repo_root=repo,
            import_evidence=True,
            run_lab=True,
            setup_logs_base=logs,
            physical_msi_import_only=False,
        )
        out.update(result)
    elif effective == "auto-discovery":
        imp = import_auto_discovery_evidence(repo_root=repo, setup_logs_base=logs)
        if explicit:
            imp.setdefault("import", {})["explicit_root_used"] = True
        out["import"] = imp
        out["status"] = imp.get("acceptance_status") or ("dev_automation_passed" if imp.get("import_ok") else "dev_automation_failed")
    elif effective == "physical-e2e":
        if ${IMPORT_ONLY@Q} == "true":
            out["import"] = import_physical_msi_evidence(repo_root=repo, setup_logs_base=logs)
            out["status"] = "dev_automation_passed" if out["import"].get("import_ok") else out["import"].get("code") or "dev_automation_failed"
        else:
            result = run_full_dev_automation(
                repo_root=repo,
                import_evidence=True,
                run_lab=${RUN_ONLY@Q} != "true",
                setup_logs_base=logs,
                physical_msi_import_only=${PHYSICAL_MSI_IMPORT@Q} == "true",
            )
            out.update(result)
    else:
        out["status"] = "unknown_mode"
        out["import"] = {"import_ok": False, "mode": effective}

Path(${RESULT_JSON@Q}).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
print(json.dumps({
    "status": out.get("status"),
    "setup_logs_base": out.get("setup_logs_base"),
    "mode_effective": out.get("mode_effective"),
    "import_ok": (out.get("import") or {}).get("import_ok"),
    "result_json": ${RESULT_JSON@Q},
}, indent=2))
ok_statuses = {
    "dev_automation_passed",
    "rescue_auto_discovery_evidence_complete",
    "rescue_auto_discovery_failure_fully_observed",
    "rescue_setup_logs_resolution_failed_fully_observed",
}
raise SystemExit(0 if out.get("status") in ok_statuses or (out.get("import") or {}).get("import_ok") else 1)
PY
