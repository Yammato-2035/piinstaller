# Developer QEMU ISO Rebuild — Profile Fingerprint

**Datum:** 2026-06-03  
**Log:** `developer_qemu_iso_rebuild_fingerprint_latest.log`

## Build-Tree (`auto/config`)

- `init=/lib/systemd/systemd` — **yes**
- `console=tty0 console=ttyS0,115200n8` — **yes**
- `quiet splash` — **nicht aktiv**

## ISO (`isolinux/live.cfg`, xorriso extract)

- `console=ttyS0,115200n8` — **yes**
- `init=/lib/systemd/systemd` — **yes**
- `SERIAL 0 115200` in `isolinux.cfg` — **yes**

## Manifest

- `rescue_build_profile`: developer-qemu
- `qemu_serial_console_configured`: true
- `qemu_guest_devserver_endpoint`: http://10.0.2.2:8001

## Bewertung

| Marker | Ergebnis |
|--------|----------|
| developer-qemu Profil belegt | **yes** |
| console=ttyS0 | **yes** |
| console=tty0 | **yes** |
| init=/lib/systemd/systemd | **yes** |
| quiet/splash entfernt | **yes** |
| Devserver 10.0.2.2:8001 (Autopilot-Unit) | **yes** |

## Status

**ok**
