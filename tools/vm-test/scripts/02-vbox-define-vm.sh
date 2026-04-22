#!/usr/bin/env bash
# Legt eine VirtualBox-VM an und hängt die Test-VDIs aus tools/vm-test/disks/ ein.
# Einmalig ausführen; danach 03-vbox-start.sh / 04-vbox-rescue-iso.sh nutzen.
# Voraussetzung: 01-create-disks-vbox.sh ausgeführt, VBoxManage im PATH.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd VBoxManage

VM_NAME="${VM_NAME:-setuphelfer-recovery-test}"
RAM_MB="${RAM_MB:-2048}"
CPU_COUNT="${CPU_COUNT:-2}"

for f in system.vdi backup.vdi restore-target.vdi; do
  [[ -f "${VM_TEST_DISKS}/$f" ]] || die "Fehlt: ${VM_TEST_DISKS}/$f — zuerst 01-create-disks-vbox.sh ausführen"
done

SYS_ABS="$(resolve_disk_path system.vdi)"
BACK_ABS="$(resolve_disk_path backup.vdi)"
REST_ABS="$(resolve_disk_path restore-target.vdi)"

if VBoxManage showvminfo "$VM_NAME" >/dev/null 2>&1; then
  echo "VM existiert bereits: $VM_NAME (überspringe createvm)"
else
  VBoxManage createvm --name "$VM_NAME" --register
  VBoxManage modifyvm "$VM_NAME" --memory "$RAM_MB" --cpus "$CPU_COUNT" \
    --acpi on --ioapic on --rtcuseutc on \
    --boot1 dvd --boot2 disk --boot3 none --boot4 none
  VBoxManage modifyvm "$VM_NAME" --paravirtprovider default --chipset ich9
fi

# SATA-Controller für alle Platten + DVD
VBoxManage storagectl "$VM_NAME" --name "SATA" --add sata --controller IntelAhci --portcount 4 || true
VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 0 --device 0 --type hdd --medium "$SYS_ABS"
VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 1 --device 0 --type hdd --medium "$BACK_ABS"
VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 2 --device 0 --type hdd --medium "$REST_ABS"
# Port 3: DVD (leer bis Rescue-ISO gesetzt wird)
VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 3 --device 0 --type dvddrive --medium emptydrive

echo "VM $VM_NAME konfiguriert. Installations-ISO manuell einhängen (GUI oder):"
echo "  VBoxManage storageattach \"$VM_NAME\" --storagectl SATA --port 3 --medium /pfad/zu/debian-12.iso"
