# Developer QEMU ISO Rebuild After Autopilot Fix — Profile Fingerprint

**Datum:** 2026-06-03

## Build-Tree / historisches ISO (Bootloader)

| Marker | Build-Tree (Prepare) | ISO `3ee02b36…` |
|--------|----------------------|-----------------|
| console=ttyS0 | **yes** | **yes** (ISOLINUX) |
| console=tty0 | **yes** | **yes** |
| init=/lib/systemd/systemd | **yes** | **yes** |
| quiet/splash | **no** | **no** |
| SERIAL 0 115200 | **yes** | **yes** |
| Devserver 10.0.2.2:8001 | **yes** (Unit) | **yes** (Unit in Squashfs) |

## Status

**review_required** — Bootappend OK; Autopilot-Wants im **Squashfs** fehlt noch (Pre-Fix-Build).
