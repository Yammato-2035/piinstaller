#!/usr/bin/env bash
# Erzeugt qcow2-Testimages NUR unter tools/vm-test/disks/.
# Nur ausführen, wenn qemu-img im PATH ist (auf diesem Referenzlaptop fehlt es).
# Keine Paketinstallation durch dieses Skript.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

require_cmd qemu-img

mkdir -p "$VM_TEST_DISKS"

SYS_GB="${SYS_GB:-8}"
BACKUP_GB="${BACKUP_GB:-1}"
REST_GB="${REST_GB:-1}"

create_qcow() {
  local name="$1"
  local size="$2"
  local path="${VM_TEST_DISKS}/${name}"
  if [[ -f "$path" ]]; then
    echo "Existiert bereits, überspringe: $path"
    return 0
  fi
  echo "Erzeuge qcow2 $size: $path"
  qemu-img create -f qcow2 "$path" "$size"
}

create_qcow "system.qcow2" "${SYS_GB}G"
create_qcow "backup.qcow2" "${BACKUP_GB}G"
create_qcow "restore-target.qcow2" "${REST_GB}G"

list_test_disks
