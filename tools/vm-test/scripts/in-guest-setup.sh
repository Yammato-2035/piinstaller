#!/usr/bin/env bash
# Im **Gast** ausführen (nicht auf dem Linux-Host). Erzeugt Marker und Verzeichnisse.
# Keine destruktiven Operationen (kein dd, kein mkfs, keine Partitionierung).
#
# Benötigt root für /opt und /etc — Aufruf:
#   sudo bash in-guest-setup.sh
#
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Bitte mit root-Rechten ausführen: sudo bash $0" >&2
  exit 1
fi

STAMP="$(date -Iseconds)"
mkdir -p /opt/setuphelfer-test
printf '%s\n' "marker_id=setuphelfer-vm-test-001" "created=${STAMP}" > /opt/setuphelfer-test/marker.txt
chmod 644 /opt/setuphelfer-test/marker.txt

printf '%s\n' "SETUPHELFER_TEST=1" "STAMP=${STAMP}" > /etc/setuphelfer-test.conf
chmod 644 /etc/setuphelfer-test.conf

mkdir -p /mnt/backup-test
chmod 755 /mnt/backup-test

# Home-Verzeichnis des normalen Benutzers (nicht root), falls bekannt
TARGET_USER="${SUDO_USER:-}"
if [[ -n "$TARGET_USER" && "$TARGET_USER" != root ]]; then
  UHOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
  if [[ -n "$UHOME" && -d "$UHOME" ]]; then
    mkdir -p "$UHOME/testdata"
    printf 'testdata for %s at %s\n' "$TARGET_USER" "$STAMP" > "$UHOME/testdata/file.txt"
    chown -R "${TARGET_USER}:${TARGET_USER}" "$UHOME/testdata"
    chmod 755 "$UHOME/testdata"
    chmod 644 "$UHOME/testdata/file.txt"
  fi
else
  echo "Hinweis: SUDO_USER leer — ~/testdata/file.txt nicht angelegt. Als testuser anlegen:" >&2
  echo "  mkdir -p ~testuser/testdata && echo test > ~testuser/testdata/file.txt && chown -R testuser:testuser ~testuser/testdata" >&2
fi

cat <<EOF

=== Setuphelfer VM-Test (Gast) — erledigt ===
Marker:     /opt/setuphelfer-test/marker.txt
Konfig:     /etc/setuphelfer-test.conf
Mount-Punkt: /mnt/backup-test (leer; Backup-Disk später hier einhängen)

Backup-Datenträger im Gast finden (zweite Platte, oft sdb):
EOF

if command -v lsblk >/dev/null 2>&1; then
  lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS,FSTYPE,MODEL || true
else
  echo "lsblk nicht verfügbar — Platten manuell prüfen (z. B. fdisk -l)." >&2
fi

cat <<EOF

Nächste Schritte: BACKUP_RUNBOOK.md (Partition auf Backup-Disk, mount nach /mnt/backup-test, dann Setuphelfer-Backup).
EOF
