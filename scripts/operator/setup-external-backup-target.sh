#!/usr/bin/env bash
# BR-001: Externes Backup-Ziel unter /media/setuphelfer/<label> einrichten (Operator, sudo).
# Kein Backup-Start. Kein chmod 777. Kein /media/<login>/… als Ziel.
# Alternative API: POST /api/backup/target-prepare (siehe docs/knowledge-base/storage/automatic-external-backup-target.md)
set -euo pipefail

LABEL="${1:-br001}"
TARGET="/media/setuphelfer/${LABEL}"
USB_UUID="${SETUPHELFER_USB_UUID:-44ce6f76-7896-4623-87b0-d81aedbed6d5}"
MODE="${SETUPHELFER_MOUNT_MODE:-bind}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Bitte mit sudo ausführen: sudo $0 [label]" >&2
  exit 1
fi

echo "=== lsblk (USB) ==="
lsblk -o NAME,SIZE,TYPE,FSTYPE,UUID,MOUNTPOINTS,MODEL,TRAN,RM

echo "=== Variante: MODE=${MODE} TARGET=${TARGET} UUID=${USB_UUID} ==="

install -d -m 0755 /media/setuphelfer

case "${MODE}" in
  direct)
    # Variante A: Partition direkt nach /media/setuphelfer/<label> mounten
    install -d -m 0755 "${TARGET}"
    if ! findmnt -rn -T "${TARGET}" >/dev/null 2>&1; then
      mount -o nosuid,nodev,noatime "UUID=${USB_UUID}" "${TARGET}"
    fi
    ;;
  bind)
    # Variante B: bestehenden Desktop-Mount (udisks) per Bind nach /media/setuphelfer/<label>
    USB_SRC="$(findmnt -rn -S "UUID=${USB_UUID}" -o TARGET 2>/dev/null | head -1 || true)"
    if [[ -z "${USB_SRC}" ]]; then
      echo "Kein Mount für UUID=${USB_UUID} gefunden. USB einstecken oder SETUPHELFER_USB_UUID setzen." >&2
      exit 2
    fi
    install -d -m 0755 "${TARGET}"
    if ! findmnt -rn -T "${TARGET}" >/dev/null 2>&1; then
      mount --bind "${USB_SRC}" "${TARGET}"
    fi
    ;;
  *)
    echo "Unbekannter MODE=${MODE} (direct|bind)" >&2
    exit 2
    ;;
esac

chown root:setuphelfer "${TARGET}"
chmod 0770 "${TARGET}"

echo "=== findmnt ${TARGET} ==="
findmnt -T "${TARGET}"
echo "=== blkid SOURCE ==="
findmnt -rn -T "${TARGET}" -o SOURCE,FSTYPE,OPTIONS

echo "=== Schreibtest setuphelfer ==="
sudo -u setuphelfer touch "${TARGET}/.write_probe"
sudo -u setuphelfer rm -f "${TARGET}/.write_probe"

echo "=== target-check (API) ==="
curl -sG 'http://127.0.0.1:8000/api/backup/target-check' --data-urlencode "backup_dir=${TARGET}" | jq .

echo "Fertig. backup_dir=${TARGET}"
