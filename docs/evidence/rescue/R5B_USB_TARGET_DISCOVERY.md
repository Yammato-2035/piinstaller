# R.5B — USB Target Discovery

**Datum:** 2026-06-13  
**Methode:** `lsblk` (read-only, **kein Write**)

> **Commit-Hinweis:** Seriennummern und konkrete `/dev/*`-Pfade in diesem Lauf **redacted** — Operator wählt Ziel manuell im TTY.

## lsblk (strukturell, redacted)

| NAME | SIZE | TRAN | TYPE | FSTYPE | LABEL | MOUNT | Bewertung |
|------|------|------|------|--------|-------|-------|-----------|
| sda | ~932G | usb | disk | — | — | — | **Ablehnen** — großes Backup-Volume |
| sda1 | ~931G | — | part | ext4 | Backup | gemountet | **Verboten** — Backup-Ziel |
| sdb | ~59G | usb | disk | — | — | — | **Kandidat** — nur nach Operator-Bestätigung |
| sdb1 | ~4G | — | part | vfat | SETUPHELFER | — | bestehende Rescue-Partition |
| nvme*n* | ~1,8T | nvme | disk/part | ext4/ntfs/vfat | — | `/`, EFI | **Verboten** — System-/Windows-Disks |

## Operator-Aktion (Pflicht)

**Keine automatische Zielwahl.** Im Operator-Terminal:

```bash
# Beispiel — Ziel vom Operator verifizieren (lsblk, physisch am Stick erkennen)
export USB_TARGET=/dev/sdX          # vom Operator gesetzt
export USB_TARGET_CONFIRMED=1
export OPERATOR_USB_WRITE_FREIGABE=1
```

## Empfehlung (informativ, keine Auto-Auswahl)

- Rescue-Stick typischerweise **kleines USB-Flash** mit Label `SETUPHELFER` / `SETUPHELFER_RESCUE`
- **Niemals** `nvme*`, gemountete Backup-Partitionen oder Systemdisks
