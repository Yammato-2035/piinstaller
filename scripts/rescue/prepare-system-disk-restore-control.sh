#!/usr/bin/env bash
# Arm one-shot system-disk restore control on SETUP_LOGS (Phase C).
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SETUP_LOGS="${SETUP_LOGS:-}"
EXECUTE=false
ARTIFACT="${BACKUP_ARTIFACT:-}"
JOB_ID="${BACKUP_JOB_ID:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=true; shift ;;
    --setup-logs) SETUP_LOGS="$2"; shift 2 ;;
    --artifact) ARTIFACT="$2"; shift 2 ;;
    --job-id) JOB_ID="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--setup-logs PATH] [--artifact PATH] [--job-id ID] --execute" >&2
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$SETUP_LOGS" ]]; then
  for cand in /media/*/SETUP_LOGS /media/*/SETUP_LOGS2 /run/media/*/SETUP_LOGS*; do
    [[ -d "$cand" ]] && SETUP_LOGS="$cand" && break
  done
fi
[[ -n "$SETUP_LOGS" ]] || { echo "ERROR: SETUP_LOGS not mounted" >&2; exit 1; }
[[ "$EXECUTE" == true ]] || { echo "Plan only — use --execute"; exit 0; }

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<PY
import json
from pathlib import Path
from core.rescue_payload_version import rescue_payload_version
from core.rescue_system_disk_restore_gate import (
    build_system_disk_restore_control,
    write_system_disk_restore_control,
)

logs = Path(${SETUP_LOGS@Q})
control = build_system_disk_restore_control(
    expected_payload_version=rescue_payload_version() or "1.10.0.37",
    backup_job_id=${JOB_ID@Q},
    backup_artifact=${ARTIFACT@Q},
    operator_consent="explicit",
)
path = write_system_disk_restore_control(logs, control)
print(json.dumps({"ok": True, "path": str(path), "run_nonce": control["run_nonce"]}, indent=2))
PY
