#!/usr/bin/env bash
# Validate fallback TUI menu contract (workspace scripts, no runtime).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

python3 - <<PY
import json
import sys
from pathlib import Path
from rescue.rescue_ui_launcher_contract import (
    evaluate_workspace_launcher_contract,
    validate_launcher_script_contract,
    validate_network_scripts_contract,
)

repo = Path(${REPO_ROOT@Q})
image = repo / "scripts/rescue-live/image"
launcher = (image / "setuphelfer-rescue-ui-launch").read_text(encoding="utf-8")
network = (image / "setuphelfer-rescue-network-onboarding").read_text(encoding="utf-8")
common = (image / "setuphelfer-rescue-common.sh").read_text(encoding="utf-8")
launcher_r = validate_launcher_script_contract(launcher)
network_r = validate_network_scripts_contract(network, common)
ws = evaluate_workspace_launcher_contract(repo)
payload = {
    "launcher_menu_contract": launcher_r,
    "network_menu_contract": network_r,
    "workspace_contract": ws,
    "contract_ok": launcher_r["contract_ok"] and network_r["contract_ok"],
}
print(json.dumps(payload, indent=2))
sys.exit(0 if payload["contract_ok"] else 16)
PY
