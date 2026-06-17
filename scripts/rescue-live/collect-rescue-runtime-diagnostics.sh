#!/bin/bash
# Collect rescue runtime diagnostics (RS-F2B.1) — read-only except SETUP_LOGS evidence writes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

export PYTHONPATH="${REPO_ROOT}/backend:${PYTHONPATH:-}"

python3 - <<'PY'
from core.rescue_runtime_diagnostics import write_rescue_runtime_diagnostics
import json
import sys

result = write_rescue_runtime_diagnostics()
print(json.dumps(result, indent=2))
if result.get("non_persistent"):
    print(result.get("warning") or "Evidence nicht persistent", file=sys.stderr)
PY
