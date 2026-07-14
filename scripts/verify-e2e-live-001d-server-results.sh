#!/usr/bin/env bash
# SETUPHELFER-E2E-LIVE-001D4 — Read-only server verification for physical E2E run.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) RUN_ID="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 --run-id e2e-rescue-msi-..." >&2
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

[[ -n "$RUN_ID" ]] || { echo "ERROR: --run-id required" >&2; exit 2; }

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
export VERIFY_RUN_ID="$RUN_ID"
export VERIFY_REPO="$REPO_ROOT"

python3 - <<'PY'
import json
import os
from pathlib import Path

from core.rescue_physical_e2e_server_verify import verify_server_results

run_id = os.environ["VERIFY_RUN_ID"]
repo = Path(os.environ["VERIFY_REPO"])
result = verify_server_results(run_id)
out_dir = repo / "docs/evidence/e2e_live_001d/physical_run" / run_id
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / "server-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": result.get("status"), "e2e_run_id": run_id, "path": str(out_dir / "server-verification.json")}, indent=2))
raise SystemExit(0 if result.get("status") == "physical_rescue_telemetry_diagnostics_e2e_passed" else 2)
PY
