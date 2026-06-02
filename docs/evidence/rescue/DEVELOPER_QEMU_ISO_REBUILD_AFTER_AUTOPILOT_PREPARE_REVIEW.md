# Developer QEMU ISO Rebuild After Autopilot Fix — Prepare Review

**Datum:** 2026-06-03  
**Prepare Exit:** **0**

## Fingerprint (Build-Tree `config/`)

| Prüfpunkt | Ergebnis |
|-----------|----------|
| profile developer-qemu | **yes** |
| console=ttyS0 | **yes** |
| init=/lib/systemd/systemd | **yes** |
| quiet/splash | **nicht aktiv** |
| Autopilot-Service | **yes** |
| Autopilot-Wants-Symlink | **yes** |
| Symlink-Ziel | `../setuphelfer-qemu-smoke-autopilot.service` |
| Devserver 10.0.2.2:8001 | **yes** |

## Hinweis

Prepare materialisiert Wants im **Config-Tree**; das auf Disk liegende **binary/live/filesystem.squashfs** stammt noch vom Build vor Fix (`3ee02b36…`) — Rebuild erforderlich.

## Status

**ok** (Prepare); Build ausstehend
