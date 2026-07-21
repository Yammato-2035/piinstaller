#!/usr/bin/env bash
# Arm one-shot physical E2E run-control on SETUP_LOGS (SABRENT / MSI GE63).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SETUP_LOGS="${SETUP_LOGS:-}"
EXECUTE=false
PAYLOAD_VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=true; shift ;;
    --setup-logs) SETUP_LOGS="$2"; shift 2 ;;
    --payload-version) PAYLOAD_VERSION="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--setup-logs PATH] [--payload-version X.Y.Z.W] --execute" >&2
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

if [[ -z "$PAYLOAD_VERSION" ]]; then
  PAYLOAD_VERSION="$(python3 -c "import json; from pathlib import Path; print(json.loads(Path('${REPO_ROOT}/config/rescue_payload_version.json').read_text())['rescue_payload_version'])")"
fi

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<PY
import json
from pathlib import Path
from core.rescue_physical_e2e_run_control import build_run_control, write_run_control

logs = Path(${SETUP_LOGS@Q})
ctrl = build_run_control(
    expected_payload_version=${PAYLOAD_VERSION@Q},
    vendor="Micro-Star International Co., Ltd.",
    model_contains="GE63 Raider",
    telemetry_required=False,
    diagnostics_required=False,
    auto_shutdown=True,
)
path = write_run_control(logs, ctrl)
print(json.dumps({"armed": True, "path": str(path), "payload": ctrl["expected_payload_version"], "nonce": ctrl["run_nonce"]}, indent=2))
PY
