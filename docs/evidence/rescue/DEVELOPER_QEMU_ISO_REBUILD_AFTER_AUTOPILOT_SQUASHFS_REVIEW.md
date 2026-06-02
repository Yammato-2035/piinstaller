# Developer QEMU ISO Rebuild After Autopilot Fix — Squashfs Review

**Datum:** 2026-06-03  
**Squashfs:** `binary/live/filesystem.squashfs` (Build 2026-06-02 23:46, **vor** Wants-Fix im Chroot)

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Squashfs vorhanden | **yes** (stale) |
| /opt/setuphelfer-rescue | **yes** |
| devserver_agent | **yes** |
| rescue_agent | **no** (nicht erforderlich) |
| Autopilot-Service | **yes** |
| **Autopilot-Wants** | **no** |
| Dev-Agent enabled | **no** (erwartet) |
| Devserver-Endpunkt | **yes** |

## Status

**blocked_autopilot_wants_missing** — Rebuild nach `fa9d2b0` erforderlich
