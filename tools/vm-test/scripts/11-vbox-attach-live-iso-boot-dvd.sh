#!/usr/bin/env bash
# Hängt eine **Live- oder Netinst-ISO** an SATA Port 3 und stellt die Boot-Reihenfolge so ein,
# dass zuerst von der **DVD** gebootet wird (Installation / Live-Sitzung).
#
# Die VM wird bei Bedarf **heruntergefahren** (ACPI, sonst FORCE=1 empfohlen).
#
#   cd tools/vm-test
#   LIVE_ISO=/abs/debian-live-….iso VM_NAME=setuphelfer-a ./scripts/11-vbox-attach-live-iso-boot-dvd.sh
#
# Optional danach: VM_NAME=… ./scripts/03-vbox-start.sh
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd VBoxManage

VM_NAME="${VM_NAME:-setuphelfer-a}"
ISO="${LIVE_ISO:-${RESCUE_ISO:-}}"

[[ -n "$ISO" ]] || die "Setze LIVE_ISO=/absoluter/pfad.iso (oder RESCUE_ISO)"
[[ -f "$ISO" ]] || die "ISO nicht gefunden: $ISO"
case "$ISO" in
  /*) ;;
  *) die "LIVE_ISO muss absoluter Pfad sein: $ISO" ;;
esac

VBoxManage showvminfo "$VM_NAME" >/dev/null 2>&1 || die "VM nicht gefunden: $VM_NAME"

state="$(VBoxManage showvminfo "$VM_NAME" --machinereadable 2>/dev/null | awk -F= '$1=="VMState"{gsub(/"/,"",$2); print $2; exit}')"
if [[ "$state" == "running" ]]; then
  echo "VM läuft — ACPI-Stopp (30 s warten, sonst FORCE=1 und erneut ausführen)"
  VBoxManage controlvm "$VM_NAME" acpipowerbutton 2>/dev/null || true
  for _ in $(seq 1 30); do
    s="$(VBoxManage showvminfo "$VM_NAME" --machinereadable 2>/dev/null | awk -F= '$1=="VMState"{gsub(/"/,"",$2); print $2; exit}')"
    [[ "$s" == "poweroff" || "$s" == "saved" ]] && break
    sleep 1
  done
  state="$(VBoxManage showvminfo "$VM_NAME" --machinereadable 2>/dev/null | awk -F= '$1=="VMState"{gsub(/"/,"",$2); print $2; exit}')"
  if [[ "$state" != "poweroff" && "$state" != "saved" ]]; then
    die "VM noch nicht aus (Zustand: $state). FORCE=1 VM_NAME=$VM_NAME ./scripts/08-vbox-stop.sh"
  fi
fi

VBoxManage storageattach "$VM_NAME" --storagectl "SATA" --port 3 --device 0 --type dvddrive --medium "$ISO"
VBoxManage modifyvm "$VM_NAME" --boot1 dvd --boot2 disk --boot3 none --boot4 none

echo "OK: ISO eingehängt, Boot zuerst DVD. VM starten: VM_NAME=$VM_NAME ./scripts/03-vbox-start.sh"
