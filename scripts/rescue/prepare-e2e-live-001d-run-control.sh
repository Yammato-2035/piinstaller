#!/usr/bin/env bash
# SETUPHELFER-E2E-LIVE-001D4 — Write one-shot run-control on SETUP_LOGS.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SETUP_LOGS="${SETUP_LOGS:-}"
EXECUTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=true; shift ;;
    --setup-logs) SETUP_LOGS="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--setup-logs PATH] --execute" >&2
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$SETUP_LOGS" ]]; then
  for cand in /media/*/SETUP_LOGS /run/media/*/SETUP_LOGS; do
    [[ -d "$cand" ]] && SETUP_LOGS="$cand" && break
  done
fi

[[ -n "$SETUP_LOGS" ]] || { echo "ERROR: SETUP_LOGS not mounted" >&2; exit 1; }
[[ "$EXECUTE" == true ]] || { echo "Plan only — use --execute to write run-control.json"; exit 0; }

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<PY
import json
from pathlib import Path
from core.rescue_physical_e2e_run_control import build_run_control, write_run_control

logs = Path(${SETUP_LOGS@Q})
control = build_run_control(expected_payload_version="1.10.0.22")
path = write_run_control(logs, control)
print(json.dumps({"ok": True, "path": str(path), "run_nonce": control["run_nonce"], "secrets_in_file": False}, indent=2))
PY
