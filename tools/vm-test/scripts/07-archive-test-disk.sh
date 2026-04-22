#!/usr/bin/env bash
# Kopiert ein Allowlist-Testmedium unter disks/ zu einem Zeitstempel-Backup (gleiches Verzeichnis).
# VirtualBox: VM mit angehängtem Medium vorher herunterfahren, sonst inkonsistente Kopie.
#
# Aufruf: ./07-archive-test-disk.sh <Basisname> ARCHIVE_TEST_DISK
# Beispiel: ./07-archive-test-disk.sh system.vdi ARCHIVE_TEST_DISK

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

ALLOWED_NAMES=(
  system.vdi
  backup.vdi
  restore-target.vdi
  system.qcow2
  backup.qcow2
  restore-target.qcow2
)

basename_only="${1:-}"
confirm="${2:-}"

[[ -n "$basename_only" ]] || die "Usage: $0 <Basisname> ARCHIVE_TEST_DISK"
[[ "$confirm" == "ARCHIVE_TEST_DISK" ]] || die "Zweites Argument muss exakt ARCHIVE_TEST_DISK sein"

ok=0
for a in "${ALLOWED_NAMES[@]}"; do
  [[ "$a" == "$basename_only" ]] && ok=1 && break
done
[[ "$ok" -eq 1 ]] || die "Basisname nicht auf Allowlist: $basename_only"

full="$(resolve_disk_path "$basename_only")"
assert_disk_extension "$full"

ts="$(date +%Y%m%d-%H%M%S)"
dest="${VM_TEST_DISKS}/${basename_only}.bak-${ts}"
dest="$(cd "$VM_TEST_DISKS" && realpath -m "$dest")"
base="$(cd "$VM_TEST_DISKS" && pwd)"
[[ "$dest" == "$base"/* ]] || die "Zielpfad ungültig: $dest"

echo "Quelle: $full"
echo "Ziel:   $dest"
read -r -p "Kopie starten? [yes/NEIN] " ans
[[ "${ans:-}" == "yes" ]] || die "Abgebrochen."

cp -a -- "$full" "$dest"
ls -la "$dest"
echo "Archiv-Kopie fertig."
