#!/usr/bin/env bash
# Im **Gast** als root: zweite Platte partitionieren (eine ext4-Partition) und nach /mnt/backup-test mounten.
# Nur für Test-VMs — zerstört die Partitionstabelle auf dem gewählten Gerät, wenn noch kein nutzbares Layout da ist.
#
# Pflicht:
#   VMTEST_BACKUP_DEV=/dev/sdX   (z. B. /dev/sdc — niemals die Systemplatte)
#   VMTEST_CONFIRM_ERASE_DISK=yes  (nur nötig, wenn neu partitioniert werden muss)
#
# Aufruf:
#   sudo env VMTEST_BACKUP_DEV=/dev/sdc VMTEST_CONFIRM_ERASE_DISK=yes \
#     bash tools/vm-test/scripts/in-guest-prepare-backup-disk.sh
#
# Optional: nach dem Mount Rechte für den Setuphelfer-Backend-Dienst (Gruppe setuphelfer, 0770):
#   VMTEST_BACKUP_OWNER_GROUP=setuphelfer  (Standard)
#
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Bitte mit root ausführen: sudo bash $0" >&2
  exit 1
fi

DEV="${VMTEST_BACKUP_DEV:-}"
MOUNT="${VMTEST_BACKUP_MOUNT:-/mnt/backup-test}"
LABEL="${VMTEST_BACKUP_LABEL:-backup-test}"

[[ -n "$DEV" ]] || { echo "FEHLER: VMTEST_BACKUP_DEV setzen (z. B. /dev/sdc)." >&2; exit 1; }
[[ -b "$DEV" ]] || { echo "FEHLER: $DEV ist kein Blockgerät." >&2; exit 1; }

_finalize_backup_mount_permissions() {
  local mnt="$1"
  local og="${VMTEST_BACKUP_OWNER_GROUP:-setuphelfer}"
  [[ -n "$og" ]] || return 0
  if ! getent group "$og" >/dev/null 2>&1; then
    groupadd --system "$og" 2>/dev/null || groupadd "$og" 2>/dev/null || true
  fi
  if getent group "$og" >/dev/null 2>&1; then
    chown "root:$og" "$mnt"
    chmod 0770 "$mnt"
    echo "OK: $mnt → root:$og (0770) für Backup-Tests."
  else
    echo "WARN: Gruppe $og fehlt — chown/chmod für $mnt übersprungen." >&2
  fi
}

ROOT_SRC="$(findmnt -n -o SOURCE / 2>/dev/null || true)"
if [[ -n "$ROOT_SRC" && "$ROOT_SRC" == "${DEV}"* ]]; then
  echo "FEHLER: $DEV gehört zum Root-Dateisystem ($ROOT_SRC) — abbrechen." >&2
  exit 1
fi

mkdir -p "$MOUNT"

if findmnt "$MOUNT" >/dev/null 2>&1; then
  echo "OK: $MOUNT ist bereits gemountet."
  _finalize_backup_mount_permissions "$MOUNT"
  exit 0
fi

PART="${DEV}1"
if [[ -b "$PART" ]]; then
  if blkid -o VALUE -s TYPE "$PART" 2>/dev/null | grep -q ext4; then
    mount "$PART" "$MOUNT"
    echo "OK: $PART nach $MOUNT gemountet (bestehende Partition)."
    _finalize_backup_mount_permissions "$MOUNT"
    exit 0
  fi
fi

if [[ "${VMTEST_CONFIRM_ERASE_DISK:-}" != "yes" ]]; then
  echo "FEHLER: Keine nutzbare Partition auf $DEV — zum Neu-Anlegen VMTEST_CONFIRM_ERASE_DISK=yes setzen." >&2
  exit 1
fi

if command -v apt-get >/dev/null 2>&1; then
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq parted >/dev/null 2>&1 || true
fi
command -v parted >/dev/null 2>&1 || { echo "FEHLER: parted fehlt." >&2; exit 1; }

umount "$MOUNT" 2>/dev/null || true
for n in 1 2 3 4 5; do
  if [[ -b "${DEV}${n}" ]]; then
    umount "${DEV}${n}" 2>/dev/null || true
  fi
done

wipefs -a "$DEV" >/dev/null 2>&1 || true
parted -s "$DEV" mklabel msdos
parted -s "$DEV" mkpart primary ext4 1MiB 100%
sleep 1
PART="${DEV}1"
[[ -b "$PART" ]] || { echo "FEHLER: Partition $PART fehlt nach parted." >&2; exit 1; }
mkfs.ext4 -F -L "$LABEL" "$PART" >/dev/null
mount "$PART" "$MOUNT"
_finalize_backup_mount_permissions "$MOUNT"
echo "OK: $PART neu erstellt und nach $MOUNT gemountet."
