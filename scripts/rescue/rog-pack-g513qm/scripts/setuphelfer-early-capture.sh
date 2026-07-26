#!/usr/bin/env bash
# Early local capture for Control C — safe to run before amdgpu load.
set -euo pipefail
export G513QM_RUN_ID="${G513QM_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)-early}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -x "$SCRIPT_DIR/setuphelfer-gpu" ]]; then
  "$SCRIPT_DIR/setuphelfer-gpu" capture
  "$SCRIPT_DIR/setuphelfer-gpu" status
else
  mkdir -p "/run/setuphelfer/g513qm-kernel-abc/$G513QM_RUN_ID"
  dmesg >"/run/setuphelfer/g513qm-kernel-abc/$G513QM_RUN_ID/dmesg-early.txt" || true
fi
