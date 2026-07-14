#!/usr/bin/env bash
# SETUPHELFER-E2E-LIVE-001D — Import physical E2E evidence from SETUP_LOGS.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN_ID="${1:-}"
SETUP_LOGS="${SETUP_LOGS:-}"

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

python3 - <<PY
import json
import sys
from pathlib import Path

from core.rescue_physical_e2e_evidence_import import (
    find_setup_logs_mount,
    import_e2e_run_evidence,
    import_latest_e2e_evidence,
    list_e2e_run_dirs,
)

repo = Path(${REPO_ROOT@Q})
run_id = ${RUN_ID@Q} or ""
logs_override = ${SETUP_LOGS@Q} or ""
base = Path(logs_override) if logs_override else find_setup_logs_mount()
if base is None:
    print(json.dumps({"import_ok": False, "error": "setup_logs_not_mounted"}))
    sys.exit(1)
if run_id:
    result = import_e2e_run_evidence(base / "setuphelfer" / "evidence" / "e2e" / run_id, repo_root=repo, setup_logs_base=base)
else:
    runs = list_e2e_run_dirs(base)
    if not runs:
        result = {"import_ok": False, "error": "no_e2e_runs_found", "setup_logs_base": str(base)}
    else:
        result = import_e2e_run_evidence(runs[0], repo_root=repo, setup_logs_base=base)
print(json.dumps(result, indent=2, ensure_ascii=False))
sys.exit(0 if result.get("import_ok") else 2)
PY
