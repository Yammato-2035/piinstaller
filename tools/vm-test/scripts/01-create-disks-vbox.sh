#!/usr/bin/env bash
# Erzeugt VirtualBox-Testmedien (VDI) NUR unter tools/vm-test/disks/.
# Voraussetzung: VBoxManage im PATH (auf diesem Host verfügbar).
# Keine Paketinstallation durch dieses Skript.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd VBoxManage

mkdir -p "$VM_TEST_DISKS"

# Größen (MB): bewusst klein für Iteration; Gast-OS-Install ggf. anpassen
SYS_MB="${SYS_MB:-8192}"     # 8 GiB Systemplatte
BACKUP_MB="${BACKUP_MB:-512}" # 512 MiB Backup-Ziel
REST_MB="${REST_MB:-512}"   # optional zweites Ziel / Restore-Test

create_vdi() {
  local name="$1"
  local size_mb="$2"
  local path="${VM_TEST_DISKS}/${name}"
  if [[ -f "$path" ]]; then
    echo "Existiert bereits, überspringe: $path"
    return 0
  fi
  echo "Erzeuge VDI ${size_mb} MiB: $path"
  VBoxManage createmedium disk --filename "$path" --size "$size_mb" --format VDI
}

create_vdi "system.vdi" "$SYS_MB"
create_vdi "backup.vdi" "$BACKUP_MB"
create_vdi "restore-target.vdi" "$REST_MB"

echo ""
echo "Fertig. Inhalt von VM_TEST_DISKS:"
list_test_disks
