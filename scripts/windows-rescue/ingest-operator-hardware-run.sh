#!/usr/bin/env bash
# Ingest operator read-only plan into inspect report + telemetry envelope (no mounts).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PLAN="${1:-${REPO_ROOT}/docs/evidence/windows-rescue/operator_windows_readonly_plan_latest.json}"
ACK="${2:-${REPO_ROOT}/docs/evidence/windows-rescue/operator_telemetry_ack_latest.json}"

cd "$REPO_ROOT"
export PYTHONPATH="${REPO_ROOT}/backend:${PYTHONPATH:-}"

python3 - "$REPO_ROOT" "$PLAN" "$ACK" <<'PY'
import json
import sys
from pathlib import Path

from core.windows_rescue_inspect import ingest_operator_hardware_run

repo = Path(sys.argv[1])
plan = Path(sys.argv[2]) if sys.argv[2] else None
ack = Path(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] and Path(sys.argv[3]).is_file() else None

result = ingest_operator_hardware_run(
    repo,
    plan_path=plan if plan and plan.is_file() else None,
    ack_path=ack,
    write_outputs=True,
)
print(json.dumps(result, indent=2, ensure_ascii=False))
PY
