#!/usr/bin/env bash
# Entfernt die ISO vom virtuellen DVD-Laufwerk (SATA Port 3) und stellt die Boot-Reihenfolge
# so ein, dass zuerst die **Systemplatte** bootet (installiertes Debian), nicht die Live-CD.
#
# VM sollte **aus** sein (oder vorher ./08-vbox-stop.sh). Sonst schlägt storageattach fehl.
#
#   cd tools/vm-test
#   VM_NAME=setuphelfer-a ./scripts/10-vbox-eject-dvd-boot-disk.sh
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd VBoxManage

VM_NAME="${VM_NAME:-setuphelfer-a}"

VBoxManage showvminfo "$VM_NAME" --machinereadable 2>/dev/null | grep -q 'name=' || die "VM nicht gefunden: $VM_NAME"

state="$(VBoxManage showvminfo "$VM_NAME" --machinereadable 2>/dev/null | awk -F= '$1=="VMState"{gsub(/"/,"",$2); print $2; exit}')"
if [[ "$state" != "poweroff" && "$state" != "saved" ]]; then
  die "VM ist nicht aus (Zustand: ${state:-unbekannt}). Zuerst: VM_NAME=$VM_NAME ./scripts/08-vbox-stop.sh"
fi

VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 3 --device 0 --type dvddrive --medium emptydrive
VBoxManage modifyvm "$VM_NAME" --boot1 disk --boot2 dvd --boot3 none --boot4 none

echo "OK: DVD leer, Boot zuerst von Platte. Start: VM_NAME=$VM_NAME ./scripts/03-vbox-start.sh"
