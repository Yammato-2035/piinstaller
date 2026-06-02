# Controlled ISO Build — ISO Structure Review

**Datum:** 2026-06-02  
**Quelle:** `isoinfo -R -f` (read-only, kein Mount)

## Pflichtdateien

| Datei | Vorhanden |
|-------|-----------|
| `/live/vmlinuz` | **yes** |
| `/live/initrd.img` | **yes** |
| `/live/filesystem.squashfs` | **yes** |
| `/isolinux/isolinux.bin` | **yes** |
| `/isolinux/live.cfg` | **yes** |
| `/isolinux/splash.png` | **yes** (49093 B) |
| `/isolinux/menu.cfg`, `stdmenu.cfg` | **yes** |
| Setuphelfer Volume-Label | **yes** — `SETUPHELFER_RESCUE` |

## Bootappend (live.cfg)

`init=/lib/systemd/systemd` in append-Zeile vorhanden; `setuphelfer_rescue=1`, DE keyboard/locale/timezone.

## Bewertung

**Status: ok**

Listing: `controlled_iso_build_isoinfo_latest.txt` (gitignored).
