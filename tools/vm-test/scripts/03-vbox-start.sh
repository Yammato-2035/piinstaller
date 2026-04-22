#!/usr/bin/env bash
# Startet die Test-VM (GUI oder headless).
# Umgebung: VM_NAME (default setuphelfer-recovery-test), optional HEADLESS=1

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd VBoxManage

VM_NAME="${VM_NAME:-setuphelfer-recovery-test}"
HEADLESS="${HEADLESS:-0}"

VBoxManage showvminfo "$VM_NAME" >/dev/null 2>&1 || die "VM nicht gefunden: $VM_NAME — zuerst 02-vbox-define-vm.sh"

if [[ "$HEADLESS" == "1" ]]; then
  echo "Starte headless: $VM_NAME"
  VBoxManage startvm "$VM_NAME" --type headless
else
  echo "Starte mit GUI: $VM_NAME"
  VBoxManage startvm "$VM_NAME"
fi
