#!/usr/bin/env bash
# Rescue UI smoke gate — must pass before squashfs/repack/payload build.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

die() { echo "check-rescue-ui-smoke-gate: FAIL — $*" >&2; exit "${2:-1}"; }

PY="${REPO_ROOT}/backend/venv/bin/python"
[[ -x "$PY" ]] || PY=python3

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

echo "check-rescue-ui-smoke-gate: running static UI contract tests…"
"$PY" -m pytest "${REPO_ROOT}/backend/tests/test_rescue_ui_smoke_gate_v1.py" \
  "${REPO_ROOT}/backend/tests/test_rescue_ui_screenshot_v1.py" \
  "${REPO_ROOT}/backend/tests/test_rescue_react_ui_contract_v1.py" \
  "${REPO_ROOT}/backend/tests/test_rescue_gui_visual_contract_v1.py" \
  -q || die "pytest smoke gate failed" 17

echo "check-rescue-ui-smoke-gate: OK"
exit 0
