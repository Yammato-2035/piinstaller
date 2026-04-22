#!/usr/bin/env bash
# Hängt eine Rescue-/Live-ISO an SATA-Port 3 (DVD) für den nächsten Boot.
# Aufruf: RESCUE_ISO=/absoluter/pfad.iso ./04-vbox-rescue-iso.sh
# VM muss aus sein oder DVD-Hotplug je nach Version; bei Zweifel VM stoppen.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd VBoxManage

VM_NAME="${VM_NAME:-setuphelfer-recovery-test}"
ISO="${RESCUE_ISO:-}"

[[ -n "$ISO" ]] || die "Setze RESCUE_ISO=/absoluter/pfad/zur.iso"
[[ -f "$ISO" ]] || die "ISO nicht gefunden: $ISO"
case "$ISO" in
  /*) ;;
  *) die "RESCUE_ISO muss absoluter Pfad sein: $ISO" ;;
esac

VBoxManage showvminfo "$VM_NAME" >/dev/null 2>&1 || die "VM nicht gefunden: $VM_NAME"

VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 3 --device 0 --type dvddrive --medium "$ISO"
VBoxManage modifyvm "$VM_NAME" --boot1 dvd --boot2 disk

echo "Rescue-ISO eingehängt. Nächster Start bootet von DVD (wenn BIOS/EFI-Reihenfolge passt)."
