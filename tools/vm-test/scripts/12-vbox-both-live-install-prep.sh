#!/usr/bin/env bash
# Bereitet **setuphelfer-a** und **setuphelfer-b** für einen **Neustart mit Live-ISO** vor:
# VMs aus, ISO an Port 3, Boot-Reihenfolge DVD → Platte.
#
#   cd tools/vm-test
#   LIVE_ISO=/abs/debian-live-….iso ./scripts/12-vbox-both-live-install-prep.sh
#
# Anschließend: im Installer / Live die Systeme wie gewohnt einrichten (Passwort unverändert lassen),
# dann im Gast: **in-guest-vmtest-postinstall.sh** (siehe VM_FRESH_INSTALL_AND_BACKUP.md).
#
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd VBoxManage

ISO="${LIVE_ISO:-}"
[[ -n "$ISO" ]] || die "Setze LIVE_ISO=/absoluter/pfad.iso"
[[ -f "$ISO" ]] || die "ISO nicht gefunden: $ISO"
case "$ISO" in
  /*) ;;
  *) die "LIVE_ISO muss absoluter Pfad sein" ;;
esac

for VM_NAME in setuphelfer-a setuphelfer-b; do
  VBoxManage showvminfo "$VM_NAME" >/dev/null 2>&1 || die "VM fehlt: $VM_NAME"
  echo "=== $VM_NAME ==="
  FORCE=1 VM_NAME="$VM_NAME" "${SCRIPT_DIR}/08-vbox-stop.sh" || true
  sleep 2
  LIVE_ISO="$ISO" VM_NAME="$VM_NAME" "${SCRIPT_DIR}/11-vbox-attach-live-iso-boot-dvd.sh"
done

echo "Fertig. Nacheinander starten (oder nur eine VM): VM_NAME=setuphelfer-a ./scripts/03-vbox-start.sh"
