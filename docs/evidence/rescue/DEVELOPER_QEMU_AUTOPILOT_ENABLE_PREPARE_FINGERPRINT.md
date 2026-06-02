# Developer QEMU Autopilot Enable — Prepare Fingerprint

**Datum:** 2026-06-03  
**Prepare Exit:** **0**

## Bootappend / Serial

- `console=ttyS0,115200n8` — **yes** (`auto/config`)
- `quiet splash` — **nicht aktiv**
- `init=/lib/systemd/systemd` — **yes**

## Autopilot wants

| Feld | Wert |
|------|------|
| Service vorhanden | **yes** |
| Wants-Symlink vorhanden | **yes** |
| Symlink-Ziel | `../setuphelfer-qemu-smoke-autopilot.service` |
| Nur developer-qemu | **yes** (Funktion nur im Prepare-Zweig) |

```
readlink → ../setuphelfer-qemu-smoke-autopilot.service
```

## Validate Build-Tree

| Feld | Wert |
|------|------|
| validate_exit | **11** |
| Grund | `FORBIDDEN: binary/live/filesystem.squashfs` (Post-Build-Artefakte vom vorherigen ISO-Build) |
| Fix-Regression | **nein** — wants vor FORBIDDEN-Check manuell verifiziert |

Operator vor Rebuild: `sudo ./scripts/rescue-live/clean-controlled-live-build-tree.sh --operator-confirm-clean` → dann validate Exit 0 erwartet.

## Status

**ok** (Prepare-Fingerprint; validate nach clean ausstehend)
