#!/usr/bin/env bash
# Validate rescue UI launcher + fallback status contract against workspace scripts.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

python3 - <<PY
import json
import sys
from pathlib import Path
from rescue.rescue_ui_launcher_contract import evaluate_workspace_launcher_contract

result = evaluate_workspace_launcher_contract(Path(${REPO_ROOT@Q}))
print(json.dumps(result, indent=2))
sys.exit(0 if result.get("contract_ok") else 15)
PY
