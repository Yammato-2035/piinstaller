#!/usr/bin/env bash
# Evaluate Phase A physical E2E evidence on SETUP_LOGS after MSI boot.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SETUP_LOGS="${1:-}"
if [[ -z "$SETUP_LOGS" ]]; then
  for cand in /media/*/SETUP_LOGS /media/*/SETUP_LOGS2 /run/media/*/SETUP_LOGS*; do
    [[ -d "$cand" ]] && SETUP_LOGS="$cand" && break
  done
fi
[[ -n "$SETUP_LOGS" ]] || { echo "ERROR: SETUP_LOGS not mounted" >&2; exit 1; }

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<PY
import json, sys
from pathlib import Path
from core.rescue_phase_a_evidence_eval import evaluate_phase_a_physical_e2e

out = evaluate_phase_a_physical_e2e(Path(${SETUP_LOGS@Q}))
print(json.dumps(out, indent=2))
code = out.get("code") or ""
if out.get("ok"):
    sys.exit(0)
if code == "phase_a_pending_msi_boot":
    sys.exit(2)
sys.exit(3)
PY
