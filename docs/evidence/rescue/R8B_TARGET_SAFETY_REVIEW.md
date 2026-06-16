# R.8B — Target Safety Review (redacted)

**Datum:** 2026-06-13

## lsblk (redacted — keine Seriennummern)

| NAME | SIZE | MODEL | TRAN | TYPE | FSTYPE | LABEL | MOUNT |
|------|------|-------|------|------|--------|-------|-------|
| sda | ~931G | HGST … | usb | disk | — | — | — |
| └ sda1 | ~931G | — | — | part | ext4 | Backup | `/media/.../Backup` |
| **sdb** | **59G** | **Ultra Line** | **usb** | **disk** | — | — | — |
| └ **sdb1** | **4G** | — | — | part | **vfat** | **SETUPHELFER** | **`/media/.../SETUPHELFER`** (initial) |
| nvme*n* | ~1.8T | Samsung … | nvme | disk/part | ext4/vfat | — | `/` `/boot/efi` |

## Prüfmatrix

| Check | Ergebnis |
|-------|----------|
| `USB_TARGET` = Gerät `/dev/sdb` | **ja** (korrekt) |
| Partition `/dev/sdb1` als Target | **falsch** — Gates: `DEVICE_NOT_FOUND`, `EVIDENCE_DEVICE_MISMATCH` |
| TRAN=usb | **ja** (sdb) |
| Kein nvme-Target | **ja** |
| Nicht Root-Disk | **ja** (nvme=root) |
| Nicht Backup-Disk (sda) | **ja** |
| Rescue-Stick erkannt | **ja** (Label SETUPHELFER, 59G Ultra Line) |
| **Gemountet vor Write** | **ja** → Blocker |
| Nach `udisksctl unmount` | **nein** → Gates green |

## Mount (initial)

```
/dev/sdb1 on /media/gabriel/SETUPHELFER type vfat (rw, ...)
```

## Entscheidung

**Target sicher** (`/dev/sdb` = freigegebener Rettungsstick).  
**Write blockiert** wegen **Mount**, nicht wegen falschem Gerät.

## Fix (Operator)

```bash
udisksctl unmount -b /dev/sdb1
# oder: sudo umount /media/gabriel/SETUPHELFER
# Prüfen: findmnt /dev/sdb1 → leer
```

Dann Write im **Operator-TTY mit sudo**.
