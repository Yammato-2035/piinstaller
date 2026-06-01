#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
AGENT="${REPO_ROOT}/scripts/rescue-live/setuphelfer-rescue-remote-agent.sh"
fail() { echo "FAIL: $*" >&2; exit 1; }

[[ -f "$AGENT" ]] || fail "missing agent script"
bash -n "$AGENT" || fail "bash -n agent"

grep -q 'blocked' "$AGENT" || fail "missing blocked runbook handling"
grep -q 'collect_network_status' "$AGENT" || fail "missing allowed runbook"
grep -q 'shell' "$AGENT" && grep -q 'blocked' "$AGENT" || fail "shell must be blocked"

grep -q 'eval' "$AGENT" && fail "eval present"
grep -q 'shell=True' "$AGENT" && fail "shell=True present"
grep -q 'bash -c' "$AGENT" && fail "bash -c present"

grep -q 'subprocess.run' "$AGENT" || fail "expected subprocess.run for allowlisted cmds"

echo "OK: rescue remote agent allowlist v1"
