# Developer QEMU ISO Rebuild After Autopilot Fix — Prebuild Validate

**Datum:** 2026-06-03

| Feld | Wert |
|------|------|
| validate_prebuild_exit | **11** |
| Grund | `FORBIDDEN: binary/live/filesystem.squashfs` (stale Post-Build-Artefakt) |
| Autopilot-Wants im Config-Tree geprüft (via Prepare) | **yes** (manuell) |
| dangerous_path_override | **nein** |

## Status

**blocked_prebuild_validate_failed** — erwartet bis `sudo clean`

Nach Clean + Prepare erneut: Validate Exit 0 erwartet (inkl. Autopilot-Wants-Check ab `fa9d2b0`).
