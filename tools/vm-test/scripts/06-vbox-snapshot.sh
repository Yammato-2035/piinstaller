#!/usr/bin/env bash
# VirtualBox-Snapshot der Test-VM (optional vor Zerstörung der Systemplatte).
# VM sollte aus sein, wenn du die system.vdi-Datei separat kopierst; Snapshots sind VM-intern.
#
# Aufruf: ./06-vbox-snapshot.sh take|list|restore|delete [SnapshotName]
# Beispiel: ./06-vbox-snapshot.sh take pre-disk-wipe

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd VBoxManage

VM_NAME="${VM_NAME:-setuphelfer-recovery-test}"
ACTION="${1:-}"
SNAP="${2:-manual-snapshot}"

[[ -n "$ACTION" ]] || die "Usage: $0 take|list|restore|delete [SnapshotName]"

VBoxManage showvminfo "$VM_NAME" >/dev/null 2>&1 || die "VM nicht gefunden: $VM_NAME"

case "$ACTION" in
  take)
    VBoxManage snapshot "$VM_NAME" take "$SNAP" --description "vm-test $(date -Iseconds)"
    echo "Snapshot erstellt: $SNAP"
    ;;
  list)
    VBoxManage snapshot "$VM_NAME" list
    ;;
  restore)
    VBoxManage snapshot "$VM_NAME" restore "$SNAP"
    echo "Snapshot wiederhergestellt: $SNAP (VM ggf. starten)"
    ;;
  delete)
    VBoxManage snapshot "$VM_NAME" delete "$SNAP"
    echo "Snapshot gelöscht: $SNAP"
    ;;
  *)
    die "Unbekannte Aktion: $ACTION"
    ;;
esac
