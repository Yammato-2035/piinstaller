# Developer QEMU ISO Rebuild After Autopilot Fix — Validator Result

**Datum:** 2026-06-03

| Validator | Exit | Ergebnis |
|-----------|------|----------|
| validate-rescue-iso-squashfs.sh (ISO `3ee02b36…`) | **12** | Autopilot wants missing |
| validate-controlled-live-build-tree.sh (prebuild) | **11** | FORBIDDEN stale squashfs |

Validator prüft Autopilot-Wants (developer-qemu): **yes** (Exit 12 auf altem ISO bestätigt).

## Status

**blocked** — Post-Fix-ISO fehlt
