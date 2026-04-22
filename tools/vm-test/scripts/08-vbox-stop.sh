#!/usr/bin/env bash
# Fährt die Test-VM herunter (ACPI) oder erzwingt PowerOff nach Timeout.
# Vor VDI-Kopie oder Zerstörung der Systemplatte ausführen.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd VBoxManage

VM_NAME="${VM_NAME:-setuphelfer-recovery-test}"
FORCE="${FORCE:-0}"

VBoxManage showvminfo "$VM_NAME" >/dev/null 2>&1 || die "VM nicht gefunden: $VM_NAME"

if [[ "$FORCE" == "1" ]]; then
  VBoxManage controlvm "$VM_NAME" poweroff || true
  echo "poweroff gesendet."
  exit 0
fi

VBoxManage controlvm "$VM_NAME" acpipowerbutton 2>/dev/null || VBoxManage controlvm "$VM_NAME" poweroff || true
echo "Shutdown angefordert. Bei hängender VM: FORCE=1 $(basename "$0")"
