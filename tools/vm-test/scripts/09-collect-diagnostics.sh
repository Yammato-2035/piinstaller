#!/usr/bin/env bash
# Schreibt VirtualBox-Infos zur Test-VM in eine lokale Logdatei (nicht ins Git).
# Ausgabe: tools/vm-test/logs/diagnostics-<zeit>.txt

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd VBoxManage

VM_NAME="${VM_NAME:-setuphelfer-recovery-test}"
LOG_DIR="${VM_TEST_ROOT}/logs"
mkdir -p "$LOG_DIR"
OUT="${LOG_DIR}/diagnostics-$(date +%Y%m%d-%H%M%S).txt"

{
  echo "=== $(date -Iseconds) VM-Test Diagnose ==="
  echo "VM_NAME=$VM_NAME"
  echo ""
  echo "=== VBoxManage list vms ==="
  VBoxManage list vms || true
  echo ""
  if VBoxManage showvminfo "$VM_NAME" >/dev/null 2>&1; then
    echo "=== showvminfo $VM_NAME ==="
    VBoxManage showvminfo "$VM_NAME" || true
    echo ""
    echo "=== snapshot list ==="
    VBoxManage snapshot "$VM_NAME" list || true
  else
    echo "VM $VM_NAME nicht registriert."
  fi
} >"$OUT"

echo "Diagnose geschrieben: $OUT"
