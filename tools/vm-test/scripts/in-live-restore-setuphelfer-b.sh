#!/usr/bin/env bash
# Im **Debian-Live-Gast** (setuphelfer-b) als **root** ausführen — nach manueller
# Laufwerksprüfung (lsblk). Schreibt nur unter /mnt/target (Standard /mnt/target).
#
# Voraussetzung: Repository auf dem Gast (z. B. ~/piinstaller-src), damit
# PYTHONPATH=…/backend und modules.restore_engine verfügbar sind (Host-Sync:
# scripts/sync-piinstaller-repo-to-guest.sh — braucht funktionierendes SSH).
#
# Pflicht:
#   LIVE_RESTORE_CONFIRM=yes
# Optional (Defaults für VM „b“ mit system-b.vdi an sda, backup-b.vdi an sdb):
#   LIVE_RESTORE_BACKUP_PART=/dev/sdb1
#   LIVE_RESTORE_SYSTEM_PART=/dev/sda1
#   LIVE_RESTORE_ARCHIVE=/mnt/backup/pi-backup-full-20260420_223625.tar.gz
#   LIVE_RESTORE_REPO="$HOME/piinstaller-src"
#
# Beispiel (nach lsblk angepasst):
#   sudo env LIVE_RESTORE_CONFIRM=yes \
#     LIVE_RESTORE_BACKUP_PART=/dev/sdb1 LIVE_RESTORE_SYSTEM_PART=/dev/sda1 \
#     LIVE_RESTORE_ARCHIVE=/mnt/backup/pi-backup-full-20260420_223625.tar.gz \
#     bash in-live-restore-setuphelfer-b.sh
#
set -euo pipefail

if [[ "${EUID:-0}" -ne 0 ]]; then
  echo "Bitte als root: sudo bash $0" >&2
  exit 1
fi
if [[ "${LIVE_RESTORE_CONFIRM:-}" != "yes" ]]; then
  echo "FEHLER: LIVE_RESTORE_CONFIRM=yes setzen (nach Prüfung von lsblk und Partitionen)." >&2
  exit 1
fi

BACKUP_PART="${LIVE_RESTORE_BACKUP_PART:-/dev/sdb1}"
SYS_PART="${LIVE_RESTORE_SYSTEM_PART:-/dev/sda1}"
ARCHIVE="${LIVE_RESTORE_ARCHIVE:-/mnt/backup/pi-backup-full-20260420_223625.tar.gz}"
REPO="${LIVE_RESTORE_REPO:-$HOME/piinstaller-src}"
BACKEND="$REPO/backend"

MNT_BAK=/mnt/backup
MNT_TGT=/mnt/target

echo "=== lsblk (Kurz) ==="
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT || true

[[ -b "$BACKUP_PART" ]] || { echo "FEHLER: $BACKUP_PART kein Blockgerät." >&2; exit 1; }
[[ -b "$SYS_PART" ]] || { echo "FEHLER: $SYS_PART kein Blockgerät." >&2; exit 1; }
[[ -f "$BACKEND/modules/restore_engine.py" ]] || {
  echo "FEHLER: Backend nicht gefunden: $BACKEND (LIVE_RESTORE_REPO anpassen oder Repo spiegeln)." >&2
  exit 1
}

mkdir -p "$MNT_BAK" "$MNT_TGT"
mount "$BACKUP_PART" "$MNT_BAK"
mount "$SYS_PART" "$MNT_TGT"

if [[ ! -f "$ARCHIVE" ]]; then
  echo "FEHLER: Archiv fehlt: $ARCHIVE" >&2
  ls -la "$MNT_BAK" >&2 || true
  exit 1
fi

echo "=== Leere Zielpartition (nur Inhalt von $MNT_TGT) ==="
rm -rf "${MNT_TGT:?}"/*

export PYTHONPATH="$BACKEND"
cd "$BACKEND"
python3 -c "
from pathlib import Path
from modules.restore_engine import restore_files
arch = Path('${ARCHIVE}')
td = Path('${MNT_TGT}').resolve()
ok, key, detail = restore_files(arch, td, allowed_target_prefixes=(td,))
print('RESTORE_OK=', ok)
print('RESTORE_KEY=', key)
print('RESTORE_DETAIL=', detail)
raise SystemExit(0 if ok else 1)
"

echo "OK: restore_files beendet. Anschließend manuell: chroot, grub-install, umount, Neustart (siehe RECOVERY_RUNBOOK.md / Aufgabenbeschreibung Phase 7–9)."
