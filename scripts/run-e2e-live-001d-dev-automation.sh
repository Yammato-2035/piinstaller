#!/usr/bin/env bash
# SETUPHELFER-E2E-LIVE-001D — Dev automation: lab E2E run + SETUP_LOGS evidence import.
#
# Usage:
#   ./scripts/run-e2e-live-001d-dev-automation.sh              # plan only
#   ./scripts/run-e2e-live-001d-dev-automation.sh --execute    # run lab + import
#   ./scripts/run-e2e-live-001d-dev-automation.sh --import-only --execute
#   ./scripts/run-e2e-live-001d-dev-automation.sh --run-only --execute
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXECUTE=false
IMPORT_ONLY=false
RUN_ONLY=false
TARGET_BYTES="${TARGET_BYTES:-67108864}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=true; shift ;;
    --import-only) IMPORT_ONLY=true; shift ;;
    --run-only) RUN_ONLY=true; shift ;;
    --target-bytes) TARGET_BYTES="$2"; shift 2 ;;
    -h|--help)
      sed -n '1,12p' "$0"
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

# Stick / SETUP_LOGS detection
SETUP_LOGS=""
for cand in /media/*/SETUP_LOGS /run/media/*/SETUP_LOGS; do
  if [[ -d "$cand/setuphelfer" || -d "$cand" ]]; then
    SETUP_LOGS="$cand"
    break
  fi
done

if [[ -n "$SETUP_LOGS" ]]; then
  echo "SETUP_LOGS: ${SETUP_LOGS}"
  ls -la "${SETUP_LOGS}/setuphelfer/evidence/e2e/" 2>/dev/null || echo "(no e2e runs yet)"
else
  echo "SETUP_LOGS: not mounted (lab evidence will use /run/setuphelfer/esp-rw fallback)"
fi

lsblk -e7 -o NAME,PATH,TYPE,TRAN,RM,SIZE,MODEL,LABEL,MOUNTPOINTS 2>/dev/null | grep -E 'NAME|usb|SETUP' || true

if [[ "$EXECUTE" != true ]]; then
  echo ""
  echo "Plan mode — no changes. Use --execute to run."
  echo "  Lab workdir: /tmp/setuphelfer-e2e-lab-work"
  echo "  Token:       \${SETUPHELFER_RS_TELEMETRY_LAB_TOKEN_FILE:-~/.config/setuphelfer/rescue/telemetry-lab-token}"
  exit 0
fi

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
export SETUP_LOGS

RUN_LAB=true
IMPORT=true
if [[ "$IMPORT_ONLY" == true ]]; then RUN_LAB=false; fi
if [[ "$RUN_ONLY" == true ]]; then IMPORT=false; fi

PY_RUN_LAB=False
PY_IMPORT=False
[[ "$RUN_LAB" == true ]] && PY_RUN_LAB=True
[[ "$IMPORT" == true ]] && PY_IMPORT=True

RESULT_JSON="${REPO_ROOT}/docs/evidence/e2e_live_001d/dev_automation_latest.json"
mkdir -p "$(dirname "$RESULT_JSON")"

python3 - <<PY
import json
import os
from pathlib import Path

from core.rescue_physical_e2e_dev_automation import run_full_dev_automation

repo = Path(${REPO_ROOT@Q})
logs = os.environ.get("SETUP_LOGS") or None
result = run_full_dev_automation(
    repo_root=repo,
    import_evidence=${PY_IMPORT},
    run_lab=${PY_RUN_LAB},
    setup_logs_base=Path(logs) if logs else None,
)
out = Path(${RESULT_JSON@Q})
out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\\n", encoding="utf-8")
print(json.dumps({
    "status": result.get("status"),
    "setup_logs_base": result.get("setup_logs_base"),
    "e2e_run_id": (result.get("lab_run") or {}).get("workflow", {}).get("e2e_run_id"),
    "import_ok": (result.get("import") or {}).get("import_ok"),
    "result_json": str(out),
}, indent=2))
raise SystemExit(0 if result.get("status") == "dev_automation_passed" else 1)
PY
